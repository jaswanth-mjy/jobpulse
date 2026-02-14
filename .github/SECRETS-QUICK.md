# 🔐 GitHub Actions Secrets - Quick Setup

## ⚡ Quick Commands

### Get Your Vercel Token
```bash
# Open Vercel tokens page
open https://vercel.com/account/tokens
# or visit: https://vercel.com/account/tokens
```

**Then:**
1. Click "Create Token"
2. Name: `GitHub Actions CI/CD`
3. Scope: `Full Account`
4. Expiration: `No Expiration` (or your preference)
5. Click Create → **Copy the token** (shown only once!)

### Add to GitHub Secrets

#### Option 1: GitHub Web UI
```
1. Go to: https://github.com/jaswanth-mjy/jobpulse/settings/secrets/actions
2. Click "New repository secret"
3. Name: VERCEL_TOKEN
4. Value: Paste your Vercel token
5. Click "Add secret"
```

#### Option 2: GitHub CLI
```bash
# Install GitHub CLI if needed
brew install gh  # macOS
# or: https://cli.github.com/

# Login
gh auth login

# Add secret
gh secret set VERCEL_TOKEN
# Paste your token when prompted
```

---

## 🎯 Required Secrets Checklist

### 1. ✅ VERCEL_TOKEN
**Status:** ⚠️ **REQUIRED** - Not configured yet  
**Purpose:** Deploy to Vercel automatically  
**Get it:** https://vercel.com/account/tokens

### 2. ⚪ RENDER_DEPLOY_HOOK (Optional)
**Status:** Optional - For Render auto-deploy  
**Purpose:** Trigger Render deployment  
**Get it:**
```
1. Go to: https://dashboard.render.com/
2. Select your service
3. Settings → Deploy Hook
4. Click "Create Deploy Hook"
5. Copy the URL
6. Add to GitHub secrets as RENDER_DEPLOY_HOOK
```

---

## 🔍 Verify Secrets

```bash
# Using GitHub CLI
gh secret list

# Expected output:
# VERCEL_TOKEN        Updated 2026-02-14
# RENDER_DEPLOY_HOOK  Updated 2026-02-14
```

Or visit: https://github.com/jaswanth-mjy/jobpulse/settings/secrets/actions

---

## 🧪 Test the Workflow

After adding secrets:

```bash
# Option 1: Push a test commit
git commit --allow-empty -m "test: Verify CI/CD with secrets"
git push origin main

# Option 2: Manually trigger workflow
gh workflow run ci-cd.yml
```

Watch it run:
```bash
# Command line
gh run watch

# Or visit
open https://github.com/jaswanth-mjy/jobpulse/actions
```

---

## ❗ Current Status

The workflow is currently **failing** because:
- ❌ `VERCEL_TOKEN` is not set

**Fix now:**
1. Get token: https://vercel.com/account/tokens
2. Add to GitHub: https://github.com/jaswanth-mjy/jobpulse/settings/secrets/actions/new

---

## 🛠️ What Happens After Setup

Once `VERCEL_TOKEN` is added:
- ✅ Every push to `main` auto-deploys to Vercel
- ✅ Deployment URL posted as commit comment
- ✅ Full CI/CD pipeline runs (lint, test, security, deploy)

Optional `RENDER_DEPLOY_HOOK`:
- ✅ Triggers Render deployment in parallel
- Note: Render auto-deploys via render.yaml anyway

---

## 📞 Help

**Token not working?**
- Ensure you copied the entire token
- Check token hasn't expired
- Verify token has "Full Account" scope

**Deployment still failing?**
- Check workflow logs: https://github.com/jaswanth-mjy/jobpulse/actions
- Verify Vercel project is linked: `vercel link`
- Run validation: `python3 validate-deployment.py`

**Manual deployment instead:**
```bash
./setup-vercel.sh  # One-command setup & deploy
```

---

## 🔗 Quick Links

- 🔑 Add Secrets: https://github.com/jaswanth-mjy/jobpulse/settings/secrets/actions
- 🔧 Vercel Tokens: https://vercel.com/account/tokens
- 📊 Workflow Runs: https://github.com/jaswanth-mjy/jobpulse/actions
- 📖 Full Guide: [SECRETS.md](SECRETS.md)
