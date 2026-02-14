#!/bin/bash

# ==================================================
# QUICK VERCEL DEPLOYMENT SCRIPT
# ==================================================
# Fast deployment script for updates
# Use setup-vercel.sh for first-time setup
#
# Usage: ./vercel-deploy.sh [preview|production]
# ==================================================

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default to production
ENVIRONMENT=${1:-production}

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}Vercel Deployment - $ENVIRONMENT${NC}"
echo -e "${BLUE}===================================================${NC}\n"

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}Installing Vercel CLI...${NC}"
    npm install -g vercel@latest
fi

# Check authentication
if ! vercel whoami &> /dev/null; then
    echo -e "${YELLOW}Logging in to Vercel...${NC}"
    vercel login
fi

echo -e "${GREEN}✓ Logged in as: $(vercel whoami)${NC}\n"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "${YELLOW}⚠ Warning: You have uncommitted changes${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Deploy based on environment
echo -e "${BLUE}Starting deployment...${NC}\n"

if [ "$ENVIRONMENT" = "production" ]; then
    vercel --prod
else
    vercel
fi

echo -e "\n${GREEN}===================================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}===================================================${NC}\n"

# Get deployment URL
echo -e "${BLUE}Getting deployment URL...${NC}"
DEPLOYMENT_URL=$(vercel ls --prod 2>/dev/null | grep -o 'https://[^ ]*' | head -1)

if [ -n "$DEPLOYMENT_URL" ]; then
    echo -e "${GREEN}✓ Deployment URL: $DEPLOYMENT_URL${NC}\n"
    
    # Offer to open in browser
    read -p "Open deployment in browser? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "$DEPLOYMENT_URL" 2>/dev/null || xdg-open "$DEPLOYMENT_URL" 2>/dev/null || echo "Please visit: $DEPLOYMENT_URL"
    fi
fi

echo -e "${BLUE}View logs at: https://vercel.com/dashboard${NC}\n"
