#!/bin/bash

# ==================================================
# VERCEL SECRETS CONFIGURATION SCRIPT
# ==================================================
# This script adds all required environment variables
# as Vercel secrets for the JobPulse application
#
# Usage: ./vercel-secrets.sh
# Or: bash vercel-secrets.sh
#
# Prerequisites:
# 1. Vercel CLI installed (npm install -g vercel)
# 2. Logged in to Vercel (vercel login)
# 3. .env file with all required variables
# ==================================================

set -e

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}Vercel Secrets Configuration${NC}"
echo -e "${BLUE}===================================================${NC}\n"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please create .env from .env.example${NC}"
    exit 1
fi

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${RED}Error: Vercel CLI not installed${NC}"
    echo -e "${YELLOW}Install with: npm install -g vercel${NC}"
    exit 1
fi

# Check if logged in
if ! vercel whoami &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Vercel. Please login:${NC}"
    vercel login
fi

echo -e "${GREEN}✓ Logged in as: $(vercel whoami)${NC}\n"

# Source environment variables
export $(grep -v '^#' .env | xargs)

# Function to add or update secret
add_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if [ -z "$secret_value" ]; then
        echo -e "${YELLOW}⚠ Skipping $secret_name (not set in .env)${NC}"
        return
    fi
    
    echo -e "${BLUE}Adding secret: $secret_name${NC}"
    
    # Remove existing secret if it exists
    vercel secrets rm "$secret_name" -y 2>/dev/null || true
    
    # Add new secret
    if echo "$secret_value" | vercel secrets add "$secret_name" 2>&1; then
        echo -e "${GREEN}✓ Secret $secret_name added successfully${NC}\n"
    else
        echo -e "${RED}✗ Failed to add secret $secret_name${NC}\n"
    fi
}

# Add all required secrets
echo -e "${BLUE}Adding secrets from .env file...${NC}\n"

add_secret "mongodb_uri" "$MONGODB_URI"
add_secret "jwt_secret" "$JWT_SECRET"
add_secret "encryption_key" "$ENCRYPTION_KEY"
add_secret "google_client_id" "$GOOGLE_CLIENT_ID"
add_secret "google_client_secret" "$GOOGLE_CLIENT_SECRET"
add_secret "google_oauth_client_id" "$GOOGLE_OAUTH_CLIENT_ID"
add_secret "google_oauth_client_secret" "$GOOGLE_OAUTH_CLIENT_SECRET"
add_secret "smtp_user" "$SMTP_USER"
add_secret "smtp_password" "$SMTP_PASSWORD"
add_secret "from_email" "$FROM_EMAIL"

# OAuth redirect URI (you may need to update this after deployment)
if [ -n "$OAUTH_REDIRECT_URI" ]; then
    add_secret "oauth_redirect_uri" "$OAUTH_REDIRECT_URI"
else
    echo -e "${YELLOW}⚠ OAUTH_REDIRECT_URI not set${NC}"
    echo -e "${YELLOW}  After deployment, run:${NC}"
    echo -e "${YELLOW}  echo 'https://your-domain.vercel.app/api/auth/google/callback' | vercel secrets add oauth_redirect_uri${NC}\n"
fi

echo -e "${GREEN}===================================================${NC}"
echo -e "${GREEN}All secrets configured successfully!${NC}"
echo -e "${GREEN}===================================================${NC}\n"

echo -e "${BLUE}To verify secrets:${NC}"
echo -e "vercel secrets ls\n"

echo -e "${BLUE}To update a specific secret:${NC}"
echo -e "vercel secrets rm <secret_name> -y"
echo -e "echo 'new_value' | vercel secrets add <secret_name>\n"

echo -e "${BLUE}Next steps:${NC}"
echo -e "1. Deploy your project: ${YELLOW}vercel --prod${NC}"
echo -e "2. Update OAuth redirect URI with your deployment URL"
echo -e "3. Test your deployment\n"
