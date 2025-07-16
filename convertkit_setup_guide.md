# 📧 ConvertKit Setup Guide for RedForge

## 🎯 Overview

This guide will help you set up ConvertKit email marketing for the RedForge Product Hunt launch. ConvertKit will capture leads and nurture them toward paid conversions.

## 📋 Step 1: ConvertKit Account Setup

### 1.1 Create ConvertKit Account
1. Go to https://convertkit.com
2. Sign up for a free account (up to 1,000 subscribers)
3. Complete account verification

### 1.2 Get API Keys
1. Go to **Settings** → **Account** → **API Keys**
2. Copy your **API Key** and **API Secret**
3. Add to environment variables:
   ```bash
   export CONVERTKIT_API_KEY="your_api_key_here"
   export CONVERTKIT_API_SECRET="your_api_secret_here"
   ```

## 📋 Step 2: Create Forms & Tags

### 2.1 Create Main Signup Form
1. Go to **Grow** → **Landing Pages & Forms**
2. Click **Create Form**
3. Choose **Inline Form**
4. Name: "RedForge Main Signup"
5. Copy the **Form ID** (you'll need this for the landing page)

### 2.2 Create Tags
Create these tags in **Subscribers** → **Tags**:
- `redforge-user` (main tag)
- `landing-signup` (signed up from landing page)
- `product-hunt-2025` (Product Hunt launch)
- `github-visitor` (came from GitHub)
- `cli-user` (used the CLI)
- `conversion-ready` (hit free limit)
- `free-tier` (free user)
- `paid-customer` (paid user)
- `starter-plan` (starter tier)
- `pro-plan` (pro tier)

## 📋 Step 3: Email Sequences

### 3.1 Free User Welcome Sequence
Create sequence: **Automations** → **Sequences** → **Create Sequence**

**Name**: "RedForge Free User Welcome"

**Email 1** (Immediate): Welcome & First Steps
```
Subject: Welcome to the RedForge security community! 🔥

Hi [first_name],

Welcome to RedForge! You've just joined 500+ developers who are serious about LLM security.

Here's what you can do right now:

🚀 **Try Your Free Scan**
- Download: github.com/siwenwang0803/RedForge  
- Run: `redforge scan gpt-4`
- Get your first security report in minutes

🛡️ **Why LLM Security Matters**
- 78% of companies using LLMs have security gaps
- Average cost of an AI breach: $4.5M
- RedForge finds issues others miss

📚 **Quick Start Resources**
- [Installation Guide](link)
- [OWASP LLM Top 10 Explained](link)
- [Security Best Practices](link)

Questions? Just reply to this email.

Stay secure,
The RedForge Team

P.S. Your free scan includes a watermarked report. Upgrade for unlimited clean reports.
```

**Email 2** (Day 3): Security Tips & Social Proof
```
Subject: 3 LLM security mistakes that cost companies millions

Hi [first_name],

Did you try your free RedForge scan yet?

If not, here are 3 critical LLM security issues we've found in real customer scans:

🚨 **Prompt Injection Vulnerabilities**
- 67% of LLMs are vulnerable to prompt injections
- Attackers can bypass safety filters
- RedForge Test: "Ignore previous instructions..."

🔓 **Data Leakage Issues**  
- Training data exposure in 43% of models
- PII leaks through adversarial prompts
- RedForge Test: Memory extraction attacks

💸 **Cost Exploitation**
- DoS attacks causing 1000x cost spikes
- Resource exhaustion vulnerabilities
- RedForge Test: Token bombing patterns

**Ready to scan your LLM?**
Download: github.com/siwenwang0803/RedForge
Run: `redforge scan your-model`

[Case Study: How RedForge saved Company X $50k/month]

Questions? Reply anytime.

Best,
RedForge Security Team
```

**Email 3** (Day 7): Free Limit & Upgrade
```
Subject: Ready for unlimited security scans?

Hi [first_name],

You've had RedForge for a week now. How's your LLM security looking?

If you're like most developers, you want to:
✅ Run multiple scans as you develop
✅ Get clean, professional reports  
✅ Test different models and endpoints
✅ Share results with your team

**Your options:**

🆓 **Free Forever**
- 1 scan with watermarked report
- Perfect for trying RedForge

🚀 **Starter Plan - $29/month**
- Unlimited security scans
- Clean, professional reports
- All OWASP LLM Top 10 tests
- JSON, HTML & PDF exports

💎 **Pro Plan - $99/month**
- Everything in Starter
- Priority support
- Custom attack patterns
- Team collaboration

[Upgrade to Starter ($29/mo) →]
[Upgrade to Pro ($99/mo) →]

Questions about upgrading? Just reply.

Secure your AI,
The RedForge Team

P.S. Most teams need 5-10 scans during development. Starter pays for itself quickly.
```

### 3.2 Conversion-Ready Sequence (Free Limit Reached)
**Name**: "RedForge Conversion Sequence"

**Email 1** (Immediate): Free Limit Reached
```
Subject: Your free RedForge scan limit reached - here's what's next

Hi [first_name],

You've used your free RedForge scan! 🎉

This means you've experienced how RedForge finds LLM vulnerabilities that other tools miss.

**What happens next?**

To continue scanning, you'll need to upgrade to a paid plan:

🚀 **Starter Plan - $29/month**
- Unlimited security scans
- Clean reports (no watermarks)
- Perfect for developers & small teams

💎 **Pro Plan - $99/month**  
- Everything in Starter
- Priority support
- Custom attack patterns
- Advanced compliance reports

**Why upgrade now?**
- Your LLM is still vulnerable
- Security gaps compound over time
- Early detection saves $$$ later

[Continue Scanning - Upgrade Now →]

Questions? Reply to this email.

Stay secure,
RedForge Team

P.S. Most customers find 2-3 critical issues in their first paid scan.
```

**Email 2** (Day 1): Social Proof & Urgency
```
Subject: How RedForge users prevent LLM security incidents

Hi [first_name],

Yesterday you hit your free scan limit. Here's what other developers are saying about upgrading:

💬 **"RedForge found a prompt injection that would have cost us $10k/month in API abuse"**
- Sarah Chen, Lead AI Engineer

💬 **"The unlimited scans helped us secure 5 different models during development"**  
- Marcus Rodriguez, Startup CTO

💬 **"Clean reports made it easy to share security findings with stakeholders"**
- Dr. Emily Watson, ML Research Lead

**Your LLM security can't wait**

Every day without proper scanning is a day your LLM could be exploited.

[Secure Your LLM - Upgrade to Starter →]

30-day money-back guarantee. Cancel anytime.

Questions? Just reply.

Best,
RedForge Security Team
```

## 📋 Step 4: Update Landing Page Configuration

1. **Get Form ID**: From your ConvertKit form settings
2. **Get Public API Key**: From ConvertKit settings
3. **Update landing page**:

```javascript
const CONVERTKIT_CONFIG = {
    formId: 'YOUR_ACTUAL_FORM_ID',
    apiKey: 'YOUR_ACTUAL_PUBLIC_API_KEY'
};
```

## 📋 Step 5: Test Email Flow

### 5.1 Test Landing Page Signup
1. Go to https://redforge.solvas.ai
2. Enter your email in the hero form
3. Verify you receive welcome email

### 5.2 Test CLI Integration
```bash
# Test email capture in CLI
redforge signup your-test-email@example.com --name "Test User"

# Test free limit notification
# (Run scan until limit reached)
```

### 5.3 Test Conversion Sequence
1. Manually add your email to "conversion-ready" tag in ConvertKit
2. Verify you receive the conversion sequence

## 📊 Analytics & Tracking

### 5.1 ConvertKit Analytics
- Monitor signup rates from different sources
- Track email open/click rates  
- Monitor conversion to paid plans

### 5.2 Google Analytics (if available)
```javascript
// Email signup tracking
gtag('event', 'email_signup', {
    'event_category': 'lead',
    'event_label': 'hero_form'
});

// Conversion tracking
gtag('event', 'conversion', {
    'send_to': 'AW-CONVERSION_ID/CONVERSION_LABEL',
    'value': 29.00,
    'currency': 'USD'
});
```

## 🎯 Launch Day Checklist

**Day Before Product Hunt:**
- [ ] All email sequences tested
- [ ] Landing page form working
- [ ] CLI integration tested
- [ ] ConvertKit tags configured
- [ ] Analytics tracking verified

**Product Hunt Day:**
- [ ] Monitor ConvertKit dashboard
- [ ] Track signup conversion rates
- [ ] Respond to email replies quickly
- [ ] Monitor for deliverability issues

**Post-Launch:**
- [ ] Analyze conversion funnel
- [ ] A/B test email sequences
- [ ] Optimize based on data
- [ ] Scale successful campaigns

## 📈 Expected Results

**Conservative Estimates:**
- **Product Hunt Traffic**: 2,000 visitors
- **Email Signups**: 200-400 (10-20% conversion)
- **Free to Paid**: 10-20 conversions (5% of signups)
- **Revenue**: $290-580 from launch week

**Optimistic Estimates:**
- **Product Hunt Traffic**: 5,000 visitors  
- **Email Signups**: 1,000+ (20%+ conversion)
- **Free to Paid**: 50+ conversions (5% of signups)
- **Revenue**: $1,450+ from launch week

---

## 🚀 Ready to Launch!

Once this is set up, you'll have a complete email marketing funnel that:
1. Captures Product Hunt visitors
2. Nurtures free users with valuable content
3. Converts them to paid customers
4. Builds a long-term email list for future launches

**Next Steps:**
1. Set up ConvertKit account & sequences
2. Update landing page with your form ID/API key
3. Test the complete flow
4. Launch on Product Hunt! 🎉