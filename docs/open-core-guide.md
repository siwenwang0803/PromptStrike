# 🔥 RedForge Open-Core Guide

RedForge now supports both local and cloud-based scanning with a flexible Open-Core model.

## 🆓 Free Tier (Offline Mode)

### Quick Start - No Registration Required
```bash
# Run limited offline scan (1 sample attack)
redforge scan gpt-4 --offline

# This will:
# - Run 1 sample attack to demonstrate functionality
# - Generate watermarked report
# - Show upgrade options
```

### What You Get
- ✅ 1 sample attack from OWASP LLM Top 10
- ✅ Basic JSON report (with watermark)
- ✅ Full source code access
- ✅ Community support

## 🚀 Starter Plan ($29/month)

### Cloud-Based Scanning
```bash
# Get your API key from https://redforge.solvas.ai/dashboard
export REDFORGE_API_KEY="your_api_key_here"

# Run full cloud scan
redforge scan gpt-4 --cloud-api-key $REDFORGE_API_KEY

# Or use environment variable
redforge scan gpt-4
```

### What You Get
- ✅ 50 attacks (full OWASP LLM Top 10)
- ✅ Unlimited scans
- ✅ Clean reports (no watermarks)
- ✅ JSON, HTML, PDF formats
- ✅ Cloud processing (no local compute needed)
- ✅ Priority support

## 💎 Pro Plan ($99/month)

### Advanced Features
```bash
# Same commands as Starter, but with more features
redforge scan gpt-4 --attack-pack custom-advanced
```

### What You Get
- ✅ 100+ attacks (all attack packs)
- ✅ Custom attack patterns
- ✅ Advanced compliance reports
- ✅ Team collaboration features
- ✅ Priority support

## 🛠️ CLI Commands

### Status & Configuration
```bash
# Check current status
redforge status

# Sign up (creates local profile)
redforge signup user@example.com --name "John Doe"

# Activate API key
redforge activate YOUR_API_KEY

# List available attacks
redforge list-attacks
```

### Scanning Options
```bash
# Cloud scanning (requires API key)
redforge scan gpt-4 --cloud-api-key YOUR_KEY

# Offline mode (free, limited)
redforge scan gpt-4 --offline

# Legacy local mode (if you have existing setup)
redforge scan gpt-4 --api-key YOUR_OPENAI_KEY
```

## 🔧 API Key Management

### Get Your API Key
1. Visit https://redforge.solvas.ai/dashboard
2. Sign up or log in
3. Go to "API Keys" section
4. Click "Generate New Key"
5. Copy and save securely

### Set Environment Variable
```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export REDFORGE_API_KEY="your_api_key_here"

# Or set for current session
export REDFORGE_API_KEY="your_api_key_here"
```

### Save to Config File
```bash
# Activate saves to ~/.redforge/config.json
redforge activate YOUR_API_KEY --save

# Then you can use without --cloud-api-key
redforge scan gpt-4
```

## 🏗️ Architecture

### Cloud Mode Flow
```
CLI → RedForge Cloud API → Scan Processing → Report Generation → Download
```

### Offline Mode Flow
```
CLI → Local Scanner → Limited Attacks → Watermarked Report
```

## 📊 Usage Limits

| Feature | Free | Starter | Pro |
|---------|------|---------|-----|
| Attacks | 1 sample | 50 (OWASP Top 10) | 100+ (All packs) |
| Scans | 1 offline | Unlimited | Unlimited |
| Formats | JSON only | JSON, HTML, PDF | All formats |
| Watermark | Yes | No | No |
| Support | Community | Priority | Priority |

## 🔐 Security & Privacy

### Data Handling
- **API Keys**: Never sent to third parties
- **Scan Data**: Processed securely in cloud
- **Reports**: Encrypted in transit and at rest
- **Retention**: Reports deleted after 30 days

### Open Source
- **CLI Code**: Fully open source (MIT license)
- **Attack Patterns**: Open source
- **Cloud API**: Closed source (proprietary)

## 🚨 Migration Guide

### From Old Version
If you were using RedForge locally:

```bash
# Old way (still works)
redforge scan gpt-4 --api-key YOUR_OPENAI_KEY

# New cloud way (recommended)
redforge scan gpt-4 --cloud-api-key YOUR_REDFORGE_KEY

# New offline way (free)
redforge scan gpt-4 --offline
```

### Benefits of Upgrading
- **No local compute required**
- **Faster scanning** (cloud processing)
- **Always up-to-date** attack patterns
- **Better reports** with compliance mapping
- **Usage analytics** and history

## 💡 Tips & Best Practices

### Development Workflow
```bash
# Quick test (offline)
redforge scan gpt-4 --offline

# Full development testing (cloud)
redforge scan gpt-4 --cloud-api-key $REDFORGE_API_KEY

# Production scanning (cloud)
redforge scan production-model --cloud-api-key $REDFORGE_API_KEY
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Run RedForge Security Scan
  run: |
    redforge scan ${{ secrets.LLM_ENDPOINT }} \
      --cloud-api-key ${{ secrets.REDFORGE_API_KEY }} \
      --format json
  env:
    REDFORGE_API_KEY: ${{ secrets.REDFORGE_API_KEY }}
```

## 📞 Support

### Free Users
- GitHub Issues: https://github.com/siwenwang0803/RedForge/issues
- Community Discord: https://discord.gg/redforge

### Paid Users
- Priority Support: support@redforge.ai
- Private Slack Channel
- Direct email support

## 🎯 Product Hunt Launch

RedForge Open-Core is launching on Product Hunt! 🚀

**Get early access:**
1. Visit https://redforge.solvas.ai
2. Sign up for free
3. Get your API key
4. Start scanning!

**Special Launch Offer:**
- 50% off first month for Product Hunt users
- Use code: `PRODUCTHUNT50`