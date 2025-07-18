-- Migration: Security and Performance Improvements
-- Addresses potential abuse and concurrency issues

-- 1. Add missing constraints to prevent negative usage_count
ALTER TABLE api_keys 
ADD CONSTRAINT chk_usage_count_positive CHECK (usage_count >= 0);

ALTER TABLE users 
ADD CONSTRAINT chk_free_scans_positive CHECK (free_scans_used >= 0);

-- 2. Add missing indexes for performance
CREATE INDEX idx_scan_history_scan_id ON scan_history(id);
CREATE INDEX idx_scan_history_api_key ON scan_history(api_key);
CREATE INDEX idx_api_keys_last_used ON api_keys(last_used_at DESC);

-- 3. Add concurrent scan tracking
CREATE TABLE IF NOT EXISTS active_scans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  api_key TEXT REFERENCES api_keys(key),
  scan_id UUID REFERENCES scan_history(id),
  started_at TIMESTAMPTZ DEFAULT NOW(),
  target_model TEXT,
  status TEXT DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed'))
);

CREATE INDEX idx_active_scans_user_id ON active_scans(user_id);
CREATE INDEX idx_active_scans_status ON active_scans(status);

-- 4. Add pending activation tracking for Stripe webhooks
CREATE TABLE IF NOT EXISTS pending_activations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  stripe_session_id TEXT UNIQUE,
  target_tier TEXT CHECK (target_tier IN ('starter', 'pro')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  processed_at TIMESTAMPTZ,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed'))
);

CREATE INDEX idx_pending_activations_session_id ON pending_activations(stripe_session_id);
CREATE INDEX idx_pending_activations_status ON pending_activations(status);

-- 5. Add rate limiting table for per-IP throttling
CREATE TABLE IF NOT EXISTS rate_limits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ip_address INET,
  api_key TEXT,
  endpoint TEXT,
  request_count INTEGER DEFAULT 1,
  window_start TIMESTAMPTZ DEFAULT NOW(),
  last_request TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_rate_limits_ip_endpoint ON rate_limits(ip_address, endpoint);
CREATE INDEX idx_rate_limits_window_start ON rate_limits(window_start);

-- 6. Enhanced RLS for scan_history (cross-account isolation)
DROP POLICY IF EXISTS "Users can view own scans" ON scan_history;
CREATE POLICY "Users can view own scans" ON scan_history
  FOR SELECT USING (
    auth.uid() = user_id OR 
    auth.uid() IN (
      SELECT user_id FROM api_keys WHERE key = scan_history.api_key
    )
  );

-- 7. Add audit trail for key revocations
CREATE TABLE IF NOT EXISTS key_revocations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  api_key TEXT,
  user_id UUID REFERENCES users(id),
  reason TEXT,
  revoked_by TEXT, -- 'user', 'admin', 'system_abuse'
  revoked_at TIMESTAMPTZ DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_key_revocations_api_key ON key_revocations(api_key);
CREATE INDEX idx_key_revocations_user_id ON key_revocations(user_id);

-- 8. Improved helper functions with concurrency control
CREATE OR REPLACE FUNCTION increment_api_key_usage_safe(p_key TEXT)
RETURNS VOID AS $$
BEGIN
  UPDATE api_keys 
  SET 
    usage_count = usage_count + 1,
    last_used_at = NOW()
  WHERE key = p_key AND revoked = FALSE;
  
  -- Ensure we don't go negative (defensive programming)
  UPDATE api_keys 
  SET usage_count = 0 
  WHERE key = p_key AND usage_count < 0;
END;
$$ LANGUAGE plpgsql;

-- 9. Function to check concurrent scan limits
CREATE OR REPLACE FUNCTION can_start_concurrent_scan(p_user_id UUID, p_tier TEXT)
RETURNS BOOLEAN AS $$
DECLARE
  v_active_count INTEGER;
  v_limit INTEGER;
BEGIN
  -- Count active scans for user
  SELECT COUNT(*) INTO v_active_count
  FROM active_scans 
  WHERE user_id = p_user_id AND status = 'running';
  
  -- Set limits based on tier
  CASE p_tier
    WHEN 'free' THEN v_limit := 1;
    WHEN 'starter' THEN v_limit := 3;
    WHEN 'pro' THEN v_limit := 10;
    ELSE v_limit := 1;
  END CASE;
  
  RETURN v_active_count < v_limit;
END;
$$ LANGUAGE plpgsql;

-- 10. Function to clean up old rate limit entries
CREATE OR REPLACE FUNCTION cleanup_old_rate_limits()
RETURNS VOID AS $$
BEGIN
  DELETE FROM rate_limits 
  WHERE window_start < NOW() - INTERVAL '1 hour';
END;
$$ LANGUAGE plpgsql;

-- 11. Function to revoke API key with audit trail
CREATE OR REPLACE FUNCTION revoke_api_key(
  p_key TEXT, 
  p_reason TEXT DEFAULT 'User requested',
  p_revoked_by TEXT DEFAULT 'user'
)
RETURNS VOID AS $$
DECLARE
  v_user_id UUID;
BEGIN
  -- Get user_id before revoking
  SELECT user_id INTO v_user_id FROM api_keys WHERE key = p_key;
  
  -- Revoke the key
  UPDATE api_keys 
  SET revoked = TRUE 
  WHERE key = p_key;
  
  -- Log the revocation
  INSERT INTO key_revocations (api_key, user_id, reason, revoked_by)
  VALUES (p_key, v_user_id, p_reason, p_revoked_by);
  
  -- Clean up active scans for this key
  UPDATE active_scans 
  SET status = 'failed' 
  WHERE api_key = p_key AND status = 'running';
END;
$$ LANGUAGE plpgsql;

-- 12. Enhanced user scan permission check with concurrency
CREATE OR REPLACE FUNCTION can_user_scan_enhanced(p_key TEXT, p_ip INET DEFAULT NULL)
RETURNS TABLE(allowed BOOLEAN, reason TEXT, tier TEXT, concurrent_ok BOOLEAN) AS $$
DECLARE
  v_key_record RECORD;
  v_user_record RECORD;
  v_can_concurrent BOOLEAN;
BEGIN
  -- Get key details
  SELECT * INTO v_key_record 
  FROM api_keys 
  WHERE key = p_key AND revoked = FALSE;
  
  IF NOT FOUND THEN
    RETURN QUERY SELECT FALSE, 'Invalid or revoked API key', NULL::TEXT, FALSE;
    RETURN;
  END IF;
  
  -- Get user details
  SELECT * INTO v_user_record
  FROM users
  WHERE id = v_key_record.user_id;
  
  -- Check concurrent scan limits
  SELECT can_start_concurrent_scan(v_user_record.id, v_user_record.tier) 
  INTO v_can_concurrent;
  
  -- Check tier limits
  IF v_user_record.tier = 'free' AND v_user_record.free_scans_used >= 1 THEN
    RETURN QUERY SELECT FALSE, 'Free tier limit reached. Upgrade to continue.', v_user_record.tier, v_can_concurrent;
  ELSIF NOT v_can_concurrent THEN
    RETURN QUERY SELECT FALSE, 'Concurrent scan limit reached for your tier.', v_user_record.tier, FALSE;
  ELSE
    RETURN QUERY SELECT TRUE, 'Scan allowed', v_user_record.tier, TRUE;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- 13. Add RLS policies for new tables
ALTER TABLE active_scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_activations ENABLE ROW LEVEL SECURITY;
ALTER TABLE key_revocations ENABLE ROW LEVEL SECURITY;

-- Users can only see their own active scans
CREATE POLICY "Users can view own active scans" ON active_scans
  FOR SELECT USING (auth.uid() = user_id);

-- Users can only see their own pending activations
CREATE POLICY "Users can view own pending activations" ON pending_activations
  FOR SELECT USING (auth.uid() = user_id);

-- Users can only see their own key revocations
CREATE POLICY "Users can view own key revocations" ON key_revocations
  FOR SELECT USING (auth.uid() = user_id);

-- 14. Create cleanup job function (to be run by cron)
CREATE OR REPLACE FUNCTION cleanup_maintenance()
RETURNS VOID AS $$
BEGIN
  -- Clean up old rate limits
  PERFORM cleanup_old_rate_limits();
  
  -- Clean up completed active scans older than 1 hour
  DELETE FROM active_scans 
  WHERE status IN ('completed', 'failed') 
  AND started_at < NOW() - INTERVAL '1 hour';
  
  -- Clean up old processed pending activations (keep for 7 days)
  DELETE FROM pending_activations 
  WHERE status = 'completed' 
  AND processed_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- 15. Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON active_scans TO authenticated;
GRANT SELECT ON pending_activations TO authenticated;
GRANT SELECT ON key_revocations TO authenticated;
GRANT SELECT ON rate_limits TO service_role;