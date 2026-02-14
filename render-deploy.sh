#!/bin/bash

# ==================================================
# RENDER DEPLOYMENT HELPER
# ==================================================
# Quick script to open Render dashboard and guides
#
# Usage: ./render-deploy.sh
# ==================================================

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}Render Deployment Helper${NC}"
echo -e "${BLUE}===================================================${NC}\n"

# Check if render.yaml exists
if [ ! -f render.yaml ]; then
    echo -e "${YELLOW}⚠ render.yaml not found!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ render.yaml found${NC}\n"

# Show service configuration
SERVICE_NAME=$(grep "name:" render.yaml | head -1 | awk '{print $2}')
echo -e "📦 Service Name: ${YELLOW}$SERVICE_NAME${NC}"
echo -e "🔧 Configuration: ${YELLOW}render.yaml${NC}"
echo -e "📖 Guide: ${YELLOW}RENDER.md${NC}\n"

# Instructions
echo -e "${BLUE}🚀 Deploy to Render:${NC}\n"
echo -e "1. Open Render Dashboard:"
echo -e "   ${YELLOW}https://dashboard.render.com/${NC}\n"
echo -e "2. Click: ${YELLOW}New + → Blueprint${NC}\n"
echo -e "3. Select repository: ${YELLOW}jaswanth-mjy/jobpulse${NC}\n"
echo -e "4. Configure environment variables (see .env file)\n"
echo -e "5. Click ${YELLOW}Apply${NC} - Render handles the rest!\n"

echo -e "${BLUE}📝 Required Environment Variables:${NC}"
echo -e "   - MONGODB_URI"
echo -e "   - JWT_SECRET"
echo -e "   - ENCRYPTION_KEY"
echo -e "   - GOOGLE_OAUTH_CLIENT_ID"
echo -e "   - GOOGLE_OAUTH_CLIENT_SECRET"
echo -e "   - SMTP_USER"
echo -e "   - SMTP_PASSWORD"
echo -e "   - FROM_EMAIL"
echo -e "   - OAUTH_REDIRECT_URI (update after first deploy)\n"

echo -e "${BLUE}🔄 Future Updates:${NC}"
echo -e "   ${GREEN}git push origin main${NC} → Auto-deploys to Render\n"

# Offer to open browser
read -p "Open Render Dashboard in browser? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${GREEN}Opening Render Dashboard...${NC}"
    open https://dashboard.render.com/ 2>/dev/null || \
    xdg-open https://dashboard.render.com/ 2>/dev/null || \
    echo -e "${YELLOW}Please visit: https://dashboard.render.com/${NC}"
fi

# Offer to show guide
read -p "View deployment guide? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v cat &> /dev/null; then
        cat RENDER.md
    else
        echo -e "${YELLOW}See RENDER.md for full guide${NC}"
    fi
fi

echo -e "\n${GREEN}✓ Ready to deploy to Render!${NC}\n"
