# 🔥 RedForge Manual Testing Guide

## Quick Test (5 minutes)

```bash
# 1. Run the automated test script
./manual_test_script.sh

# 2. Check results - you should see ALL ✅ green checkmarks
```

## Detailed Manual Testing (15 minutes)

### 🎯 Sprint S-1: CLI Core

```bash
# Test CLI help
redforge --help

# Test diagnostics
redforge doctor

# Test attack listing
redforge list-attacks

# Test dry run (no API calls)
redforge scan gpt-4 --dry-run

# Test offline scan (limited, with watermark)
redforge scan gpt-4 --offline --output ./test-reports
```

**Expected Results:**
- ✅ CLI commands work without errors
- ✅ Doctor shows "All checks passed"
- ✅ 17+ attacks listed
- ✅ Dry run shows attack plan table
- ✅ Offline scan creates JSON report with watermark

### 🌐 Sprint S-3: API Gateway & Open-Core

```bash
# Test API Gateway health
curl https://api-gateway-uenk.onrender.com/healthz

# Test API documentation
curl https://api-gateway-uenk.onrender.com/docs

# Test user signup (replace with your email)
curl -X POST https://api-gateway-uenk.onrender.com/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"your-test@email.com"}'

# Copy the API key from response, then test scan
curl -X POST https://api-gateway-uenk.onrender.com/scan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{"target":"gpt-4","dry_run":true}'

# Test free tier limit (second scan should fail with 402)
curl -X POST https://api-gateway-uenk.onrender.com/scan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{"target":"gpt-4","dry_run":true}'
```

**Expected Results:**
- ✅ Health check returns `{"status":"ok"}`
- ✅ Docs return HTML page
- ✅ Signup returns `{"api_key":"rk_..."}`
- ✅ First scan returns `{"scan_id":"..."}`
- ✅ Second scan returns HTTP 402 (Payment Required)

### 🛡️ Sprint S-2: Security Components

```bash
# Test Guardrail SDK import
python3 -c "from guardrail.sdk import GuardrailClient; print('✅ Guardrail SDK')"

# Test Cost Guard
python3 -c "from redforge.sidecar import CostGuard; cg = CostGuard(); print('✅ Cost Guard')"

# Test Compliance Framework
python3 -c "from redforge.compliance.pci_dss_framework import PCIDSSFramework; print('✅ PCI DSS')"

# Check documentation exists
ls docs/RedForge/Security/Guardrail_Threat_Model.md
ls docs/RedForge/Guardrail/OTEL_SPAN_SCHEMA.md
```

**Expected Results:**
- ✅ All Python imports succeed
- ✅ Documentation files exist

## 🚨 Critical Issues to Watch

### ❌ FAIL Conditions:
1. **CLI doctor shows errors** → Check environment setup
2. **Offline scan fails** → Check attack compatibility
3. **API Gateway returns 500** → Check Supabase connection
4. **Signup endpoint 404** → Check deployment status
5. **Import errors** → Check Python dependencies

### ⚠️ WARNING Conditions:
1. **Free tier limit not enforced** → Business logic issue
2. **No watermark in offline reports** → Pricing model broken
3. **Health check slow (>2s)** → Performance issue

## 🎯 Success Criteria (100% Required)

**For Product Hunt Launch, ALL must be ✅:**

- [ ] CLI help, doctor, list-attacks work
- [ ] Offline scan generates reports
- [ ] API Gateway health check passes
- [ ] User signup creates API keys
- [ ] First scan succeeds (HTTP 200)
- [ ] Second scan hits limit (HTTP 402)
- [ ] Guardrail components import
- [ ] Documentation files exist
- [ ] No critical errors in any component

## 🛠️ Quick Fixes

If you find issues:

1. **CLI errors**: `poetry install` or check Python version
2. **API Gateway 500**: Wait 5 minutes for Render deployment
3. **Import errors**: Check if you're in the right directory
4. **Permission errors**: `chmod +x manual_test_script.sh`

## 🚀 When Ready for Launch

✅ All tests pass  
✅ No critical errors  
✅ Reports generate correctly  
✅ Free tier limits work  
✅ API Gateway stable  

**You're ready for Product Hunt! 🎉**