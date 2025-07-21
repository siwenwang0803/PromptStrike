# 🔗 Complete Stripe Webhook Setup Guide

This guide will help you set up the complete Stripe webhook integration for automatic user upgrades.

## ✅ What This Enables

After setup, when a user pays $29:
1. **Stripe processes payment** ✅
2. **Webhook triggers automatically** ✅ 
3. **User created in Supabase** ✅
4. **API key generated** ✅
5. **Welcome email sent with API key** ✅
6. **User upgraded to paid tier** ✅

## 🔧 Step 1: Configure Stripe Webhook

### 1.1 Create Webhook Endpoint in Stripe

1. **Login to Stripe Dashboard**: https://dashboard.stripe.com/
2. **Go to**: Developers → Webhooks
3. **Click**: "Add endpoint"
4. **Endpoint URL**: `https://redforge.onrender.com/stripe/webhook`
5. **Select events**:
   - `checkout.session.completed` ✅
   - `customer.subscription.deleted` ✅ 
   - `invoice.payment_failed` ✅

### 1.2 Get Webhook Secret

After creating the webhook:
1. **Click** on your new webhook endpoint
2. **Copy** the "Signing secret" (starts with `whsec_`)
3. **Save** this - you'll need it for environment variables

## 🔑 Step 2: Configure Environment Variables

Set these environment variables in your deployment:

```bash
# Stripe Configuration (CRITICAL)
STRIPE_SECRET=sk_live_51XXXXX...     # Your Stripe secret key (live mode)
STRIPE_WEBHOOK_SECRET=whsec_XXXXX...      # Webhook signing secret from Step 1.2

# Email Configuration (for API key delivery)
SMTP_USERNAME=your-email@gmail.com        # Gmail for sending emails
SMTP_PASSWORD=your-app-password           # Gmail App Password (not regular password)
FROM_EMAIL=dev@solvas.ai                  # From address

# Supabase (should already be configured)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
```

### 2.1 Gmail App Password Setup

For email sending to work:

1. **Enable 2FA** on your Gmail account
2. **Go to**: Google Account → Security → 2-Step Verification → App passwords
3. **Generate** an app password for "Mail"
4. **Use this password** as `SMTP_PASSWORD` (not your regular Gmail password)

## 🚀 Step 3: Deploy Updated API Gateway

### 3.1 Update Render Deployment

If using Render:
1. **Push code** to GitHub (webhook code is now included)
2. **Render auto-deploys** new version
3. **Set environment variables** in Render dashboard
4. **Check logs** for successful startup

### 3.2 Verify Deployment

```bash
# Test health endpoint
curl https://redforge.onrender.com/healthz

# Should return:
{
  "service": "RedForge API Gateway",
  "status": "ok",
  "database": "connected"
}
```

## 🧪 Step 4: Test the Complete Flow

### 4.1 Test Payment Flow

1. **Use your $29 Stripe payment link**
2. **Complete payment** with real credit card
3. **Check email** - you should receive welcome email with API key
4. **Check Supabase** - user should be created with `tier = "starter"`

### 4.2 Test API Key

```bash
# Test the API key from welcome email
curl -H "X-API-Key: rk_XXXXX..." https://redforge.onrender.com/scan \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"target": "gpt-4", "dry_run": true}'

# Should return scan_id (not 402 Payment Required)
```

## 🔍 Step 5: Monitor & Debug

### 5.1 Check Webhook Delivery

1. **Stripe Dashboard** → Webhooks → Your endpoint
2. **View** recent webhook attempts 
3. **Check** response codes:
   - ✅ `200 OK` = Success
   - ❌ `400/500` = Error (check logs)

### 5.2 Common Issues

#### Issue: "Invalid signature" 
**Fix**: Double-check `STRIPE_WEBHOOK_SECRET` environment variable

#### Issue: "Database service unavailable"
**Fix**: Check `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`

#### Issue: "Email not sent"
**Fix**: Verify Gmail app password and SMTP settings

#### Issue: "User not upgraded"
**Fix**: Check Render logs for webhook processing errors

### 5.3 Render Logs

```bash
# View live logs in Render dashboard or CLI
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/$SERVICE_ID/logs
```

## 📋 Step 6: Verify Complete Integration

Test these scenarios:

### ✅ Successful Payment Test
1. Complete $29 payment → User receives welcome email with API key
2. User can make unlimited scans with API key
3. No more "free tier limit reached" errors

### ✅ Cancellation Test  
1. Cancel Stripe subscription → User downgraded to free tier
2. API keys revoked → User gets 401 errors

### ✅ Failed Payment Test
1. Stripe sends payment failed webhook → User notified (optional)

## 🎯 Success Criteria

Your integration is complete when:

- ✅ $29 payment creates Supabase user
- ✅ API key generated and emailed automatically  
- ✅ User can make unlimited scans immediately
- ✅ No manual user creation needed
- ✅ Webhook delivery shows 200 OK in Stripe dashboard

## 🚨 Security Notes

- **Never commit** Stripe keys to Git
- **Use environment variables** for all secrets
- **Verify webhook signatures** (already implemented)
- **Monitor failed webhook attempts** regularly

## 📞 Support

If you encounter issues:

1. **Check Render logs** first for error messages
2. **Verify environment variables** are set correctly  
3. **Test webhook endpoint** with Stripe webhook testing tool
4. **Contact**: dev@solvas.ai with specific error messages

## 🎉 You're Done!

Once working, your users get this experience:
1. **Click** "Start Cloud Scan - $29/mo" button
2. **Pay** via Stripe checkout
3. **Receive** welcome email with API key automatically
4. **Start** unlimited scanning immediately

No manual steps required! 🚀