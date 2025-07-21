# RedForge Testing Strategy

## Overview

RedForge testing is split into **Core** and **Paid Flow** to ensure Product Hunt readiness while validating premium features before releases.

## 🎯 Core Testing (CI/CD Ready)

### Purpose
- Product Hunt launch readiness
- Free tier user experience
- OSS demonstration
- GitHub Stars conversion

### Coverage
- ✅ CLI functionality (help, doctor, list-attacks)
- ✅ Offline scanning with watermarked reports
- ✅ Multi-format report generation (JSON, PDF, HTML)
- ✅ API Gateway health and documentation
- ✅ Free tier signup and single scan
- ✅ Free tier limit enforcement
- ✅ Security component imports (Guardrail, Cost Guard, PCI DSS)

### Usage

**Manual:**
```bash
./manual_test_script_core.sh
```

**Make target:**
```bash
make test-core
```

**GitHub Actions:**
- Triggers on: push to main/develop, PRs
- Runs automatically in CI/CD
- Blocks merges if core functionality breaks

### Expected Results
```
✅ 21/21 tests passed
🎉 ALL CORE TESTS PASSED! Ready for Product Hunt launch!
Success Rate: 100%
```

## 💳 Paid Flow Testing (Manual)

### Purpose
- Validate Stripe → Supabase tier upgrades
- Test concurrent rate limiting (Starter: 3 allowed, 2+ denied)
- Ensure first paid users don't encounter issues
- Pre-release validation

### Coverage
- ✅ Stripe checkout session creation
- ✅ Payment webhook processing
- ✅ Supabase tier update verification
- ✅ Concurrent rate limiting enforcement
- ✅ Webhook endpoint health

### Prerequisites
```bash
# Required environment variables
export STRIPE_API_KEY=sk_test_...
export PRICE_STARTER=price_...
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_SERVICE_ROLE=eyJ...

# Required tools
brew install stripe/stripe-cli/stripe
```

### Usage

**Setup:**
```bash
./setup_stripe_env.sh
```

**Manual:**
```bash
./paid_flow_test.sh
```

**Make target:**
```bash
make test-paid-flow
```

### When to Run
- Before major releases
- Monthly verification
- When payment logic changes
- Before Product Hunt launch (optional but recommended)

## 📋 File Structure

```
RedForge/
├── .github/workflows/
│   └── e2e_core.yml                 # Automated core testing
├── manual_test_script_core.sh       # Core functionality tests
├── paid_flow_test.sh               # Paid flow tests
├── setup_stripe_env.sh             # Stripe setup helper
├── manual_test_script_fixed.sh     # Legacy (includes optional Stripe)
└── TESTING_STRATEGY.md             # This document
```

## 🚀 Product Hunt Launch Strategy

### Required (Core)
```bash
make test-core
# Must show: 🎉 ALL CORE TESTS PASSED!
```

### Optional (Paid Flow)
```bash
make test-paid-flow
# Validates premium features work
# Can be done post-launch if needed
```

### CI/CD Integration
- Core tests run automatically on every commit
- Prevents broken functionality from reaching users
- Ensures free tier experience always works

## 🔧 Troubleshooting

### Common Issues

**Core Tests Failing:**
- Check API Gateway status (may be sleeping on Render)
- Verify CLI installation: `poetry run redforge --version`
- Check PDF dependencies: `sudo apt-get install wkhtmltopdf`

**Paid Flow Issues:**
- Stripe CLI not installed: See `setup_stripe_env.sh`
- Environment variables missing: Run `./setup_stripe_env.sh`
- Webhook not triggered: Check Render logs for `/stripe/webhook`

### Command Line Tools Issue (macOS 15)
If you see Xcode Command Line Tools errors:
```bash
# Option 1: Update tools
sudo rm -rf /Library/Developer/CommandLineTools
sudo xcode-select --install

# Option 2: Skip Stripe testing (recommended for now)
# Use core testing only - perfectly fine for Product Hunt launch
```

## 📊 Success Criteria

### Core Testing (Required for Launch)
- ✅ 100% test pass rate
- ✅ All report formats generate
- ✅ API Gateway responsive
- ✅ Free tier works end-to-end

### Paid Flow Testing (Nice to Have)
- ✅ >85% test pass rate
- ✅ Stripe payment processing
- ✅ Tier upgrades in Supabase
- ✅ Rate limiting enforced

## 🎯 Recommendation

**For Product Hunt Launch:**
1. Run `make test-core` → Must pass 100%
2. Run `make test-paid-flow` → Optional, can fix post-launch
3. Deploy with confidence knowing free tier works perfectly

The core testing covers everything needed for a successful Product Hunt launch. Paid flow testing ensures premium features work but isn't blocking for initial launch.