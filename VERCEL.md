# ================================================== # VERCEL DEPLOYMENT QUICK START GUIDE
# ==================================================

## 🚀 Automated Deployment (Recommended)

### One-Command Setup
```bash
./setup-vercel.sh
```

This script will:
- ✓ Install Vercel CLI
- ✓ Login to Vercel
- ✓ Configure all secrets from .env
- ✓ Link your project
- ✓ Deploy to production

---

## 📋 Prerequisites

### 1. Create .env File
```bash
cp .env.example .env
```

Then edit `.env` and fill in your actual values:
- MongoDB Atlas URI
- JWT secret (generate: `openssl rand -hex 32`)
- Encryption key (generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
- Google OAuth credentials
- Gmail SMTP credentials

### 2. Install Node.js
- Download from: https://nodejs.org/
- Verify: `node --version` (should be ≥18.x)

### 3. Commit Your Code
```bash
git add -A
git commit -m "Prepare for Vercel deployment"
```

---

## 🛠️ Manual Deployment

### Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

### Step 2: Login
```bash
vercel login
```

### Step 3: Validate Configuration
```bash
python validate-deployment.py
```

This checks:
- ✓ Environment variables in .env
- ✓ vercel.json configuration
- ✓ API entry point (api/index.py)
- ✓ Requirements.txt
- ✓ Frontend/backend file structure

### Step 4: Configure Secrets
```bash
./vercel-secrets.sh
```

Or manually:
```bash
# Example secret configuration
vercel secrets rm mongodb_uri -y  # Remove if exists
echo "your-mongodb-uri" | vercel secrets add mongodb_uri

# Repeat for all secrets (see .env.example)
```

### Step 5: Deploy
```bash
# Preview deployment
vercel

# Production deployment
vercel --prod
```

---

## 🔑 Required Secrets

Add these secrets using `vercel secrets add <name>`:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `mongodb_uri` | MongoDB Atlas connection string | `mongodb+srv://user:pass@cluster...` |
| `jwt_secret` | JWT signing key (32+ chars) | `your-random-secret-key-here` |
| `encryption_key` | Fernet encryption key (44 chars) | `your-fernet-key-here=` |
| `google_oauth_client_id` | Google OAuth Client ID | `xxx.apps.googleusercontent.com` |
| `google_oauth_client_secret` | Google OAuth Client Secret | `GOCSPX-xxx` |
| `smtp_user` | Gmail address | `your-email@gmail.com` |
| `smtp_password` | Gmail app password | `xxxx xxxx xxxx xxxx` |
| `from_email` | Sender email address | `your-email@gmail.com` |
| `oauth_redirect_uri` | OAuth callback URL | `https://your-app.vercel.app/api/auth/google/callback` |

---

## 🔄 Quick Redeploy

For subsequent deployments:

```bash
# Quick deploy script
./vercel-deploy.sh production

# Or direct Vercel command
vercel --prod

# Preview deployment
vercel
```

---

## 📦 NPM Scripts

Defined in `package.json`:

```bash
npm run dev              # Run locally
npm run deploy           # Deploy to production
npm run deploy:preview   # Deploy preview
npm run setup:vercel     # Full setup script
npm run secrets          # Configure secrets only
npm run validate         # Validate before deploy
```

---

## 🌐 Post-Deployment Configuration

### 1. Update Google OAuth
After deployment, get your Vercel URL and:

1. Go to https://console.cloud.google.com/apis/credentials
2. Edit your OAuth 2.0 Client ID
3. Add to **Authorized redirect URIs**:
   ```
   https://your-app.vercel.app/api/auth/google/callback
   ```

### 2. Update OAuth Redirect URI Secret
```bash
vercel secrets rm oauth_redirect_uri -y
echo 'https://your-app.vercel.app/api/auth/google/callback' | vercel secrets add oauth_redirect_uri
```

### 3. Test Your Deployment
- Visit your Vercel URL
- Test Google OAuth login
- Test Gmail scanning
- Check application tracking features

---

## 🔍 Troubleshooting

### Check Deployment Logs
```bash
vercel logs
```

### Check Secrets
```bash
vercel secrets ls
```

### Redeploy After Changes
```bash
git add -A
git commit -m "Your changes"
git push origin main
vercel --prod
```

### Common Issues

**1. "Secret not found" error**
```bash
# Re-add the missing secret
echo 'your-value' | vercel secrets add secret_name
```

**2. "Build failed" error**
- Check `requirements.txt` has all dependencies
- Verify Python syntax: `python -m py_compile backend/*.py`
- Check logs: `vercel logs`

**3. "Function timeout" error**
- Default timeout is 60s (configured in vercel.json)
- For longer operations, optimize your code

**4. OAuth not working**
- Verify redirect URI in Google Console matches deployment URL
- Check `oauth_redirect_uri` secret is correct
- Ensure credentials are properly set in Vercel secrets

---

## 📊 Monitoring

### Vercel Dashboard
- https://vercel.com/dashboard
- View deployments, logs, analytics
- Monitor performance and errors

### GitHub Actions
- CI/CD pipeline runs automatically on push to main
- View workflow: GitHub repo → Actions tab
- Includes: linting, testing, security scanning, auto-deploy

---

## 🔒 Security Checklist

- [x] .env file is in .gitignore
- [x] All secrets use Vercel secrets (@secret_name format)
- [x] JWT secret is 32+ random characters
- [x] Encryption key is 44 characters (Fernet key)
- [x] Google OAuth restricted to your domain
- [x] Gmail uses app password, not account password
- [x] MongoDB Atlas IP whitelist configured (0.0.0.0/0 for Vercel)
- [x] CORS configured properly in backend

---

## 🆘 Support

- **Vercel Docs**: https://vercel.com/docs
- **GitHub Issues**: https://github.com/jaswanth-mjy/jobpulse/issues
- **Deployment Guide**: See `DEPLOYMENT.md`

---

## 📝 Quick Reference

### Environment Setup
```bash
cp .env.example .env
# Edit .env with your values
```

### Validate
```bash
python validate-deployment.py
```

### Deploy
```bash
./setup-vercel.sh        # First time
./vercel-deploy.sh       # Updates
```

### Update Secrets
```bash
./vercel-secrets.sh      # All secrets
vercel secrets add <name>  # Single secret
```

### Logs
```bash
vercel logs              # View logs
vercel logs --follow     # Tail logs
```

---

**Ready to deploy?** Run `./setup-vercel.sh` now! 🚀
