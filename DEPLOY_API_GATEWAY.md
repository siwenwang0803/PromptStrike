# 🚀 Deploy API Gateway to Render

## Step 1: Go to Render Dashboard

1. Visit: [https://dashboard.render.com/](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**

## Step 2: Connect Repository

1. **Connect GitHub repository**: `siwenwang0803/RedForge`
2. **Root Directory**: `api_gateway`
3. **Branch**: `main`

## Step 3: Configure Service

**Basic Settings:**
- **Name**: `redforge-api-gateway`
- **Environment**: `Docker`
- **Region**: `Oregon (US West)`
- **Instance Type**: `Starter` (0.1 CPU / 256 MB)

**Build & Deploy:**
- **Build Command**: (leave empty - Docker will handle it)
- **Start Command**: (leave empty - Dockerfile CMD will handle it)

## Step 4: Environment Variables

Add these environment variables in Render:

| Name | Value |
|------|-------|
| `SUPABASE_URL` | `https://memfjxlbjjjtdsgipdlz.supabase.co` |
| `SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1lbWZqeGxiampqdGRzZ2lwZGx6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI4NTIyNzgsImV4cCI6MjA2ODQyODI3OH0.SQOU12m3qD5xTTlcnl0ydrcw4qTERpGseuL4UKhQfCo` |
| `SUPABASE_SERVICE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1lbWZqeGxiampqdGRzZ2lwZGx6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Mjg1MjI3OCwiZXhwIjoyMDY4NDI4Mjc4fQ.VdQMp6073IQOqt4a5dowPK3TOMfVvITsL9MhKmxXVeE` |
| `ENVIRONMENT` | `production` |
| `MAX_FREE_SCANS` | `1` |
| `MAX_STARTER_CONCURRENCY` | `3` |

## Step 5: Health Check

- **Health Check Path**: `/healthz`

## Step 6: Deploy

1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes)
3. You'll get a URL like: `https://redforge-api-gateway.onrender.com`

## Step 7: Test Deployment

Once deployed, test the API Gateway:

```bash
# Test health check
curl https://redforge-api-gateway.onrender.com/healthz

# Expected response:
{
  "service": "RedForge API Gateway",
  "version": "0.2.0",
  "status": "ok",
  "timestamp": "2025-01-18T...",
  "database": "connected"
}
```

## Files Created:

- ✅ `api_gateway/Dockerfile` - Docker configuration
- ✅ `api_gateway/requirements.txt` - Updated with gunicorn
- ✅ `api_gateway/main_simple.py` - Added /healthz endpoint
- ✅ `DEPLOY_API_GATEWAY.md` - This deployment guide

## Next Steps:

1. **Test with API key** using the test script
2. **Update CLI** to use the new URL
3. **Optional**: Set up custom domain

## Expected URL Structure:

```
https://redforge-api-gateway.onrender.com/
├── /                    # Health check
├── /healthz             # Detailed health check
├── /scan                # Create scan
├── /scan/{id}/status    # Get status
└── /scan/{id}/report    # Get report
```

🎯 **This will create a NEW service separate from your existing Payment API!**