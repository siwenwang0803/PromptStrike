#!/usr/bin/env bash
# Setup script for Stripe environment variables

echo "🔧 RedForge Stripe Environment Setup"
echo "====================================="

# Check if Stripe CLI is installed
if command -v stripe >/dev/null 2>&1; then
    echo "✅ Stripe CLI is installed"
    stripe --version
else
    echo "❌ Stripe CLI not found"
    echo ""
    echo "📥 Installation Options:"
    echo "   Option 1: Homebrew (requires updated Xcode Command Line Tools)"
    echo "   brew install stripe/stripe-cli/stripe"
    echo ""
    echo "   Option 2: Direct download (if Homebrew fails)"
    echo "   1. Visit: https://github.com/stripe/stripe-cli/releases"
    echo "   2. Download: stripe_X.X.X_mac-os_x86_64.tar.gz"
    echo "   3. Extract and move to /usr/local/bin/stripe"
    echo ""
    echo "   Option 3: Skip Stripe testing (recommended for now)"
    echo "   The core RedForge functionality works perfectly without Stripe!"
    echo ""
    echo "🎯 For Product Hunt launch, Stripe testing is OPTIONAL"
fi

echo ""
echo "🔑 Environment Variables Needed:"
echo ""

# Check current environment
echo "Current environment status:"
if [ -n "${STRIPE_API_KEY:-}" ]; then
    echo "✅ STRIPE_API_KEY: ${STRIPE_API_KEY:0:12}..."
else
    echo "❌ STRIPE_API_KEY: Not set"
fi

if [ -n "${PRICE_STARTER:-}" ]; then
    echo "✅ PRICE_STARTER: $PRICE_STARTER"
else
    echo "❌ PRICE_STARTER: Not set"
fi

if [ -n "${SUPABASE_URL:-}" ]; then
    echo "✅ SUPABASE_URL: ${SUPABASE_URL:0:30}..."
else
    echo "❌ SUPABASE_URL: Not set"
fi

if [ -n "${SUPABASE_SERVICE_ROLE:-}" ]; then
    echo "✅ SUPABASE_SERVICE_ROLE: ${SUPABASE_SERVICE_ROLE:0:12}..."
else
    echo "❌ SUPABASE_SERVICE_ROLE: Not set"
fi

echo ""
echo "📋 Setup Instructions:"
echo ""

if [ -z "${STRIPE_API_KEY:-}" ]; then
    echo "1. Get your Stripe API key:"
    echo "   • Go to: https://dashboard.stripe.com/test/apikeys"
    echo "   • Copy the 'Secret key' (starts with sk_test_)"
    echo "   • Run: export STRIPE_API_KEY=sk_test_..."
    echo ""
fi

if [ -z "${PRICE_STARTER:-}" ]; then
    echo "2. Get your Starter tier Price ID:"
    echo "   • Go to: https://dashboard.stripe.com/test/products"
    echo "   • Find your Starter tier product"
    echo "   • Copy the Price ID (starts with price_)"
    echo "   • Run: export PRICE_STARTER=price_..."
    echo ""
fi

if [ -z "${SUPABASE_URL:-}" ]; then
    echo "3. Get your Supabase URL:"
    echo "   • Go to: https://supabase.com/dashboard/project/[your-project]"
    echo "   • Go to Settings > API"
    echo "   • Copy the 'Project URL'"
    echo "   • Run: export SUPABASE_URL=https://your-project.supabase.co"
    echo ""
fi

if [ -z "${SUPABASE_SERVICE_ROLE:-}" ]; then
    echo "4. Get your Supabase Service Role key:"
    echo "   • Go to: https://supabase.com/dashboard/project/[your-project]"
    echo "   • Go to Settings > API"
    echo "   • Copy the 'service_role' key (NOT anon key)"
    echo "   • Run: export SUPABASE_SERVICE_ROLE=eyJ..."
    echo ""
fi

echo "🚀 Quick Setup Commands:"
echo ""
echo "# Copy and paste these, filling in your actual values:"
echo "export STRIPE_API_KEY=sk_test_..."
echo "export PRICE_STARTER=price_..."
echo "export SUPABASE_URL=https://your-project.supabase.co"
echo "export SUPABASE_SERVICE_ROLE=eyJ..."
echo ""
echo "# Then run the complete test:"
echo "./manual_test_script_complete.sh"
echo ""

# Alternative: Check if user has STRIPE_SECRET (your Render variable name)
if [ -n "${STRIPE_SECRET:-}" ]; then
    echo "🔄 Alternative: Found STRIPE_SECRET variable"
    echo "You can map it with: export STRIPE_API_KEY=\$STRIPE_SECRET"
    echo ""
fi

echo "💡 Pro tip: Add these to your ~/.bashrc or ~/.zshrc to persist"