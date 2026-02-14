# 🚀 Render Deployment - Quick Start

## ⚡ One-Click Deploy

Render is **already configured** and ready to deploy! Your [render.yaml](render.yaml) is production-ready.

### Deploy Now

1. **Go to Render Dashboard:**
   ```
   https://dashboard.render.com/
   ```

2. **Click "New +" → "Blueprint"**

3. **Connect Your Repository:**
   - Select: `jaswanth-mjy/jobpulse`
   - Render will auto-detect `render.yaml`

4. **Configure Environment Variables** (one-time setup):
   
   Add these from your `.env` file:
   
   | Variable | Value | Notes |
   |----------|-------|-------|
   | `MONGODB_URI` | Your MongoDB Atlas URI | Required |
   | `JWT_SECRET` | Your JWT secret | Required |
   | `ENCRYPTION_KEY` | Your Fernet key | Required |
   | `GOOGLE_OAUTH_CLIENT_ID` | OAuth Client ID | Required |
   | `GOOGLE_OAUTH_CLIENT_SECRET` | OAuth Secret | Required |
   | `SMTP_USER` | Gmail address | Required |
   | `SMTP_PASSWORD` | Gmail app password | Required |
   | `FROM_EMAIL` | Sender email | Required |
   | `OAUTH_REDIRECT_URI` | `https://your-app.onrender.com/api/auth/google/callback` | Update after deploy |

5. **Click "Apply"** → Render will:
   - ✅ Install dependencies from `requirements.txt`
   - ✅ Build the application
   - ✅ Start gunicorn server (2 workers, 4 threads)
   - ✅ Auto-deploy on every git push to main

---

## 🔧 Already Configured

Your [render.yaml](render.yaml) includes:

✅ **Production Gunicorn:**
- 2 workers, 4 threads
- Worker recycling (max-requests: 1000)
- Request timeout: 60s
- Keep-alive: 5s

✅ **Environment Variables:**
- All OAuth credentials
- SMTP configuration
- MongoDB connection
- Security keys

✅ **Auto-Deploy:**
- Deploys automatically on git push
- Health checks on `/health` endpoint
- Static file serving

✅ **Logging:**
- Access logs and error logs enabled
- Log level: INFO

---

## 📋 Post-Deployment Steps

### 1. Get Your Render URL
After deployment completes:
```
https://your-app-name.onrender.com
```

### 2. Update Google OAuth Redirect URI
1. Go to: https://console.cloud.google.com/apis/credentials
2. Edit your OAuth 2.0 Client ID
3. Add to **Authorized redirect URIs**:
   ```
   https://your-app-name.onrender.com/api/auth/google/callback
   ```

### 3. Update OAUTH_REDIRECT_URI Variable
In Render dashboard → Your service → Environment:
```
OAUTH_REDIRECT_URI=https://your-app-name.onrender.com/api/auth/google/callback
```

### 4. Test Your Deployment
- ✅ Visit your Render URL
- ✅ Test Google OAuth login
- ✅ Test Gmail scanning
- ✅ Verify application tracking

---

## 🔄 Updates & Redeployment

**Automatic:** Push to main branch
```bash
git push origin main
# Render auto-deploys in ~2-3 minutes
```

**Manual:** In Render Dashboard
1. Go to your service
2. Click "Manual Deploy"
3. Select "Deploy latest commit"

---

## 📊 Monitoring

### Render Dashboard
- **Logs:** Real-time application logs
- **Metrics:** CPU, Memory, Response time
- **Events:** Deployment history
- **Shell:** Direct access to container

### Check Service Health
```bash
curl https://your-app-name.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

## 🆓 Free Tier Notes

**Render Free Tier includes:**
- ✅ 750 hours/month
- ✅ Auto-sleep after 15 min inactivity
- ✅ 512 MB RAM
- ✅ Shared CPU
- ✅ Auto SSL certificates

**Cold starts:**
- First request after sleep: ~30-60 seconds
- Subsequent requests: Normal speed

**Upgrade to keep always-on:**
- $7/month for Starter plan
- No cold starts
- More resources

---

## 🔍 Troubleshooting

### Build Fails
```bash
# Check logs in Render dashboard
# Common issues:
# - Missing dependencies in requirements.txt
# - Python syntax errors
# - Build command issues
```

### Application Crashes
```bash
# Check:
# 1. Environment variables are set correctly
# 2. MongoDB URI is accessible
# 3. Port binding (Render auto-assigns PORT env var)
```

### OAuth Not Working
```bash
# Verify:
# 1. Redirect URI matches Render URL exactly
# 2. Google Console has correct redirect URI
# 3. OAUTH_REDIRECT_URI env var is updated
```

### Database Connection Issues
```bash
# MongoDB Atlas:
# 1. Whitelist IP: 0.0.0.0/0 (allow all)
# 2. Check connection string format
# 3. Verify credentials
```

---

## 🎯 Render vs Vercel

| Feature | Render | Vercel |
|---------|--------|--------|
| Type | Container | Serverless |
| Cold Start | ~30-60s | ~1-5s |
| Always Free | ✅ 750h/month | ✅ Unlimited |
| Config | render.yaml | vercel.json |
| Deploy | Git push | Git push or CLI |
| Best For | Full Flask app | API endpoints |

**Current Setup:** Both are configured! Choose based on preference.

---

## 📝 Quick Commands

### Deploy to Render
```bash
git add -A
git commit -m "Deploy to Render"
git push origin main
# Render auto-deploys
```

### Check Deployment Status
```bash
# Install Render CLI (optional)
brew install renderinc/render/render  # macOS

# Login
render login

# View services
render services list

# View logs
render logs
```

---

## 🔗 Quick Links

- 🚀 **Render Dashboard:** https://dashboard.render.com/
- 📖 **Render Docs:** https://render.com/docs
- 🔧 **Blueprint Guide:** https://render.com/docs/infrastructure-as-code
- 💬 **Render Support:** https://render.com/docs/support

---

## ✅ Ready to Deploy?

**Your render.yaml is already configured!**

Just connect your repo in Render dashboard:
1. https://dashboard.render.com/ → New + → Blueprint
2. Select `jaswanth-mjy/jobpulse`
3. Add environment variables
4. Click Apply

**Done!** Render handles the rest. 🎉

Future updates deploy automatically on `git push origin main`.

---

## 🆘 Need Help?

- See full guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Check render.yaml: [render.yaml](render.yaml)
- GitHub Actions: Workflow already includes Render auto-deploy trigger
