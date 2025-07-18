-- Migration: Add API Keys and User Tiers for Open-Core Model
-- This enables cloud-based scanning with usage limits

-- 1. Update users table with tier and Stripe customer ID
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS tier TEXT DEFAULT 'free' CHECK (tier IN ('free', 'starter', 'pro')),
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
ADD COLUMN IF NOT EXISTS free_scans_used INTEGER DEFAULT 0;

-- 2. Create API keys table
CREATE TABLE IF NOT EXISTS api_keys (
  key TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name TEXT, -- Optional friendly name like "Production Key"
  tier TEXT DEFAULT 'free' CHECK (tier IN ('free', 'starter', 'pro')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_used_at TIMESTAMPTZ,
  revoked BOOLEAN DEFAULT FALSE,
  usage_count INTEGER DEFAULT 0 CHECK (usage_count >= 0), -- Prevent negative usage
  rate_limit_per_hour INTEGER DEFAULT 10, -- Tier-based rate limits
  metadata JSONB DEFAULT '{}' -- For future extensibility
);

-- Indexes for performance
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_active ON api_keys(key) WHERE revoked = FALSE;

-- 3. Create scan history table for audit trail
CREATE TABLE IF NOT EXISTS scan_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  api_key TEXT REFERENCES api_keys(key),
  user_id UUID REFERENCES users(id),
  scan_type TEXT, -- 'full', 'dry-run', 'custom'
  target_model TEXT,
  attack_count INTEGER,
  severity_counts JSONB, -- {"critical": 2, "high": 5, ...}
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  report_url TEXT,
  metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_scan_history_user_id ON scan_history(user_id);
CREATE INDEX idx_scan_history_created_at ON scan_history(created_at DESC);
CREATE INDEX idx_scan_history_scan_id ON scan_history(id); -- For status polling performance

-- 4. Row Level Security (RLS)
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_history ENABLE ROW LEVEL SECURITY;

-- Users can only see their own API keys
CREATE POLICY "Users can view own API keys" ON api_keys
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own API keys" ON api_keys
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own API keys" ON api_keys
  FOR UPDATE USING (auth.uid() = user_id);

-- Users can only see their own scan history
CREATE POLICY "Users can view own scans" ON scan_history
  FOR SELECT USING (auth.uid() = user_id);

-- 5. Helper functions
CREATE OR REPLACE FUNCTION increment_api_key_usage(p_key TEXT)
RETURNS VOID AS $$
BEGIN
  UPDATE api_keys 
  SET 
    usage_count = usage_count + 1,
    last_used_at = NOW()
  WHERE key = p_key AND revoked = FALSE;
END;
$$ LANGUAGE plpgsql;

-- Function to check if user can perform scan
CREATE OR REPLACE FUNCTION can_user_scan(p_key TEXT)
RETURNS TABLE(allowed BOOLEAN, reason TEXT, tier TEXT) AS $$
DECLARE
  v_key_record RECORD;
  v_user_record RECORD;
BEGIN
  -- Get key details
  SELECT * INTO v_key_record 
  FROM api_keys 
  WHERE key = p_key AND revoked = FALSE;
  
  IF NOT FOUND THEN
    RETURN QUERY SELECT FALSE, 'Invalid or revoked API key', NULL::TEXT;
    RETURN;
  END IF;
  
  -- Get user details
  SELECT * INTO v_user_record
  FROM users
  WHERE id = v_key_record.user_id;
  
  -- Check tier limits
  IF v_user_record.tier = 'free' AND v_user_record.free_scans_used >= 1 THEN
    RETURN QUERY SELECT FALSE, 'Free tier limit reached. Upgrade to continue.', v_user_record.tier;
  ELSE
    RETURN QUERY SELECT TRUE, 'Scan allowed', v_user_record.tier;
  END IF;
END;
$$ LANGUAGE plpgsql;