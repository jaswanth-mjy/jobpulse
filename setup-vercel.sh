#!/bin/bash

# ==================================================
# JOBPULSE - AUTOMATED VERCEL DEPLOYMENT SCRIPT
# ==================================================
# This script automates the complete Vercel deployment process
# including secret configuration and project deployment
#
# Usage: ./setup-vercel.sh
# Or: bash setup-vercel.sh
#
# Prerequisites:
# 1. Node.js and npm installed
# 2. .env file with all required variables
# 3. Git repository initialized and committed
# ==================================================

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ==================================================
# STEP 1: PREREQUISITE CHECKS
# ==================================================
print_header "STEP 1: Checking Prerequisites"

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    print_info "Please create .env file from .env.example and fill in your values"
    print_info "cp .env.example .env"
    exit 1
fi
print_success ".env file found"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed"
    print_info "Install from: https://nodejs.org/"
    exit 1
fi
print_success "Node.js installed: $(node --version)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed"
    exit 1
fi
print_success "npm installed: $(npm --version)"

# Check if git is initialized
if [ ! -d .git ]; then
    print_error "Git repository not initialized"
    print_info "Run: git init"
    exit 1
fi
print_success "Git repository initialized"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    print_warning "You have uncommitted changes"
    print_info "Commit them before deploying for best results"
fi

# ==================================================
# STEP 2: INSTALL VERCEL CLI
# ==================================================
print_header "STEP 2: Installing Vercel CLI"

if ! command -v vercel &> /dev/null; then
    print_info "Installing Vercel CLI globally..."
    npm install -g vercel@latest
    print_success "Vercel CLI installed"
else
    print_success "Vercel CLI already installed: $(vercel --version)"
fi

# ==================================================
# STEP 3: VERCEL LOGIN
# ==================================================
print_header "STEP 3: Vercel Authentication"

print_info "Checking Vercel authentication..."
if vercel whoami &> /dev/null; then
    print_success "Already logged in to Vercel as: $(vercel whoami)"
else
    print_info "Please login to Vercel (browser will open)..."
    vercel login
    print_success "Successfully logged in to Vercel"
fi

# ==================================================
# STEP 4: CONFIGURE VERCEL SECRETS
# ==================================================
print_header "STEP 4: Configuring Vercel Secrets"

print_info "Reading environment variables from .env file..."

# Source .env file
export $(grep -v '^#' .env | xargs)

# Array of secrets to add (secret_name:env_var_name)
declare -a secrets=(
    "mongodb_uri:MONGODB_URI"
    "jwt_secret:JWT_SECRET"
    "encryption_key:ENCRYPTION_KEY"
    "google_client_id:GOOGLE_CLIENT_ID"
    "google_client_secret:GOOGLE_CLIENT_SECRET"
    "google_oauth_client_id:GOOGLE_OAUTH_CLIENT_ID"
    "google_oauth_client_secret:GOOGLE_OAUTH_CLIENT_SECRET"
    "smtp_user:SMTP_USER"
    "smtp_password:SMTP_PASSWORD"
    "from_email:FROM_EMAIL"
    "oauth_redirect_uri:OAUTH_REDIRECT_URI"
)

print_info "Adding secrets to Vercel..."
for secret_pair in "${secrets[@]}"; do
    IFS=':' read -r secret_name env_var <<< "$secret_pair"
    
    # Get value from environment
    value="${!env_var}"
    
    if [ -z "$value" ]; then
        print_warning "Skipping $secret_name (not set in .env)"
        continue
    fi
    
    print_info "Adding secret: $secret_name"
    
    # Try to add secret, if it exists, update it
    if echo "$value" | vercel secrets add "$secret_name" 2>&1 | grep -q "already exists"; then
        print_info "Secret $secret_name already exists, removing and re-adding..."
        vercel secrets rm "$secret_name" -y 2>/dev/null || true
        echo "$value" | vercel secrets add "$secret_name"
    fi
    
    print_success "Secret $secret_name configured"
done

print_success "All secrets configured successfully!"

# ==================================================
# STEP 5: LINK VERCEL PROJECT
# ==================================================
print_header "STEP 5: Linking Vercel Project"

if [ -d .vercel ]; then
    print_success "Project already linked"
    print_info "Project: $(cat .vercel/project.json | grep -o '"projectId":"[^"]*"' | cut -d'"' -f4)"
else
    print_info "Linking to Vercel project..."
    print_warning "Follow the prompts to create/link your project"
    vercel link
    print_success "Project linked successfully"
fi

# ==================================================
# STEP 6: DEPLOY TO VERCEL
# ==================================================
print_header "STEP 6: Deploying to Vercel"

print_info "Starting deployment..."
print_warning "This may take a few minutes..."

# Deploy to production
vercel --prod

print_success "Deployment completed!"

# ==================================================
# STEP 7: POST-DEPLOYMENT CONFIGURATION
# ==================================================
print_header "STEP 7: Post-Deployment Configuration"

print_info "Getting deployment URL..."
DEPLOYMENT_URL=$(vercel ls --prod 2>/dev/null | grep -o 'https://[^ ]*' | head -1)

if [ -z "$DEPLOYMENT_URL" ]; then
    DEPLOYMENT_URL=$(vercel ls | grep -o 'https://[^ ]*' | head -1)
fi

print_success "Deployment URL: $DEPLOYMENT_URL"

print_info "\n${YELLOW}IMPORTANT: Update the following settings:${NC}"
echo ""
echo "1. Google OAuth Authorized Redirect URIs:"
echo "   → https://console.cloud.google.com/apis/credentials"
echo "   → Add: ${DEPLOYMENT_URL}/api/auth/google/callback"
echo ""
echo "2. Update OAUTH_REDIRECT_URI secret:"
echo "   → Run: vercel secrets rm oauth_redirect_uri -y"
echo "   → Run: echo '${DEPLOYMENT_URL}/api/auth/google/callback' | vercel secrets add oauth_redirect_uri"
echo ""
echo "3. Update frontend URL in your code if needed"
echo ""
echo "4. Test your deployment:"
echo "   → Visit: ${DEPLOYMENT_URL}"
echo "   → Try Google OAuth login"
echo "   → Test Gmail scanning"
echo ""

# ==================================================
# COMPLETION
# ==================================================
print_header "DEPLOYMENT COMPLETE!"

print_success "Your JobPulse application is now live on Vercel!"
print_info "Deployment URL: $DEPLOYMENT_URL"
print_info "\nFor monitoring and logs, visit: https://vercel.com/dashboard"
print_info "For any issues, check: ./DEPLOYMENT.md"

echo ""
print_success "Setup completed successfully! 🚀"
echo ""
