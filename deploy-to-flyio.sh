#!/bin/bash

# CloudCost Optimizer - Fly.io Deployment Script
# Run this after following FLY_IO_MIGRATION.md steps 1-3

set -e  # Exit on error

echo "🚀 CloudCost Optimizer - Fly.io Deployment"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo -e "${RED}❌ flyctl CLI not found!${NC}"
    echo "Install it first:"
    echo "  Mac:    brew install flyctl"
    echo "  Linux:  curl -L https://fly.io/install.sh | sh"
    echo "  Windows: iwr https://fly.io/install.ps1 -useb | iex"
    exit 1
fi

echo -e "${GREEN}✅ flyctl found${NC}"
echo ""

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Fly.io${NC}"
    echo "Logging in..."
    flyctl auth login
fi

echo -e "${GREEN}✅ Logged in to Fly.io${NC}"
echo ""

# Initialize app (if not already done)
if [ ! -f "fly.toml" ]; then
    echo -e "${RED}❌ fly.toml not found!${NC}"
    echo "Run 'flyctl launch --no-deploy' first"
    exit 1
fi

echo -e "${GREEN}✅ fly.toml found${NC}"
echo ""

# Prompt for secrets
echo -e "${YELLOW}📝 Setting up environment variables...${NC}"
echo ""

# Database URL
read -p "Enter DATABASE_URL (from Fly PostgreSQL): " DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ DATABASE_URL is required!${NC}"
    exit 1
fi
flyctl secrets set DATABASE_URL="$DATABASE_URL"

# Groq API Key
read -p "Enter GROQ_API_KEY (for CloudCost AI): " GROQ_API_KEY
if [ -n "$GROQ_API_KEY" ]; then
    flyctl secrets set GROQ_API_KEY="$GROQ_API_KEY"
else
    echo -e "${YELLOW}⚠️  Skipping GROQ_API_KEY (CloudCost AI won't work)${NC}"
fi

# AWS Credentials (optional)
read -p "Enter AWS_ACCESS_KEY_ID (optional, for AWS spot prices): " AWS_ACCESS_KEY_ID
if [ -n "$AWS_ACCESS_KEY_ID" ]; then
    flyctl secrets set AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID"
    read -p "Enter AWS_SECRET_ACCESS_KEY: " AWS_SECRET_ACCESS_KEY
    flyctl secrets set AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY"
else
    echo -e "${YELLOW}⚠️  Skipping AWS credentials (AWS spot prices won't work)${NC}"
fi

echo ""
echo -e "${GREEN}✅ Secrets configured${NC}"
echo ""

# Deploy
echo -e "${YELLOW}🚀 Deploying to Fly.io...${NC}"
echo ""
flyctl deploy

echo ""
echo -e "${GREEN}=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "==========================================${NC}"
echo ""
echo "Your app is live at:"
flyctl status | grep "Hostname"
echo ""
echo "Next steps:"
echo "1. Test health: curl https://your-app.fly.dev/health"
echo "2. Set up GitHub Actions cron (see FLY_IO_MIGRATION.md Step 8)"
echo "3. Update frontend API URL"
echo ""
echo -e "${GREEN}🎉 Welcome to Fly.io!${NC}"
