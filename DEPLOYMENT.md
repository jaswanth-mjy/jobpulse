# JobPulse Deployment Guide

## Available Deployment Options

JobPulse supports multiple deployment platforms with different configurations optimized for each.

---

## 🚀 Vercel Deployment (Serverless)

**Best for:** Quick deployments, global CDN, automatic HTTPS

### Prerequisites
- Vercel account ([vercel.com](https://vercel.com))
- GitHub/GitLab repository connected

### Steps

1. **Install Vercel CLI (optional)**
   ```bash
   npm install -g vercel
   ```

2. **Deploy via CLI**
   ```bash
   vercel
   ```

3. **Or Deploy via Dashboard**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your Git repository
   - Vercel will auto-detect `vercel.json`
   - Configure environment variables (see below)

### Environment Variables (Vercel Secrets)

Set these as Vercel Secrets (not regular env vars):

```bash
vercel secrets add mongodb_uri "mongodb+srv://..."
vercel secrets add jwt_secret "your-secret-key"
vercel secrets add encryption_key "your-encryption-key"
vercel secrets add google_client_id "your-client-id"
vercel secrets add google_client_secret "your-client-secret"
vercel secrets add google_oauth_client_id "your-oauth-id"
vercel secrets add google_oauth_client_secret "your-oauth-secret"
vercel secrets add smtp_user "your-email@gmail.com"
vercel secrets add smtp_password "your-app-password"
vercel secrets add from_email "your-email@gmail.com"
vercel secrets add oauth_redirect_uri "https://your-domain.vercel.app/api/gmail/oauth/callback"
```

### Vercel Configuration

The `vercel.json` file is already configured with:
- Python serverless functions for backend API
- Static file serving for frontend
- CORS headers
- Custom routes for SPA
- Region: US East (iad1)
- Max duration: 60 seconds

### Custom Domain (Optional)
1. Go to Project Settings → Domains
2. Add your custom domain
3. Configure DNS records as shown

---

## 🎨 Render.com Deployment (Container-based)

**Best for:** Long-running processes, background workers, cron jobs

### Prerequisites
- Render account ([render.com](https://render.com))
- GitHub/GitLab repository connected

### Steps

1. **Via Blueprint (Recommended)**
   - Go to [render.com/new](https://render.com/new)
   - Select "Blueprint"
   - Choose your repository
   - Render will read `render.yaml` automatically
   - Configure environment variables
   - Click "Apply"

2. **Via Dashboard (Manual)**
   - Create new Web Service
   - Connect repository
   - Configure:
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `cd backend && gunicorn app:app --bind 0.0.0.0:$PORT`
     - **Environment:** Add all env vars from `.env`

### Environment Variables (Render)

Add these in Render Dashboard → Environment:
- `MONGODB_URI` (secret)
- `JWT_SECRET` (secret)
- `ENCRYPTION_KEY` (secret)
- `GOOGLE_CLIENT_ID` (secret)
- `GOOGLE_CLIENT_SECRET` (secret)
- `GOOGLE_OAUTH_CLIENT_ID` (secret)
- `GOOGLE_OAUTH_CLIENT_SECRET` (secret)
- `SMTP_HOST` = smtp.gmail.com
- `SMTP_PORT` = 587
- `SMTP_USER` (secret)
- `SMTP_PASSWORD` (secret)
- `FROM_EMAIL` (secret)
- `FROM_NAME` = JobPulse
- `OAUTH_REDIRECT_URI` (secret)

### Advanced Features

The `render.yaml` includes configurations for:
- ✅ Auto-deploy on git push
- ✅ Health check endpoint
- ✅ Gunicorn with optimized workers
- ✅ Production environment
- 📦 Optional cron jobs (commented out)
- 💼 Optional background workers (commented out)

To enable cron jobs or workers, uncomment the relevant sections in `render.yaml`.

---

## 🐳 Docker Deployment

**Best for:** Self-hosting, Kubernetes, custom infrastructure

### Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/

EXPOSE 5050

CMD ["gunicorn", "--chdir", "backend", "app:app", "--bind", "0.0.0.0:5050", "--workers", "2", "--timeout", "120"]
```

### Build and Run

```bash
# Build
docker build -t jobpulse .

# Run
docker run -p 5050:5050 \
  -e MONGODB_URI="..." \
  -e JWT_SECRET="..." \
  jobpulse
```

---

## 🌐 Environment Variables Reference

### Required Secrets
| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB Atlas connection string | `mongodb+srv://user:pass@cluster.mongodb.net/db` |
| `JWT_SECRET` | Secret key for JWT tokens | Random 32+ char string |
| `ENCRYPTION_KEY` | Fernet key for encrypting passwords | Base64 encoded 32-byte key |

### Google OAuth
| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Google Sign-In client ID |
| `GOOGLE_CLIENT_SECRET` | Google Sign-In client secret |
| `GOOGLE_OAUTH_CLIENT_ID` | Gmail API OAuth client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Gmail API OAuth client secret |
| `OAUTH_REDIRECT_URI` | OAuth callback URL |

### Email (SMTP)
| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | SMTP username | Your Gmail |
| `SMTP_PASSWORD` | SMTP password | Gmail App Password |
| `FROM_EMAIL` | Sender email | Same as SMTP_USER |
| `FROM_NAME` | Sender name | `JobPulse` |

---

## 🔒 Security Checklist

Before deploying to production:

- [ ] Change `JWT_SECRET` from default value
- [ ] Generate new `ENCRYPTION_KEY` using: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- [ ] Use Gmail App Passwords (not regular password)
- [ ] Enable MongoDB IP whitelist (0.0.0.0/0 for cloud deployments)
- [ ] Set proper CORS origins in production
- [ ] Enable HTTPS (automatic on Vercel/Render)
- [ ] Review and update `OAUTH_REDIRECT_URI` for your domain

---

## 📊 Performance Tips

### Vercel (Serverless)
- Functions cold start: ~1-2 seconds
- Keep functions under 50MB
- Use caching for static assets
- Region: Choose closest to users

### Render (Container)
- Free tier: Spins down after 15min inactivity
- Upgrade to keep alive 24/7
- Use Render cron for scheduled tasks
- Add Redis for job queues (optional)

### Database (MongoDB Atlas)
- Free tier: 512MB storage
- Enable indexes for frequently queried fields
- Use connection pooling
- Consider read replicas for scaling

---

## 🐛 Troubleshooting

### Vercel
- **Function timeout:** Increase `maxDuration` in `vercel.json`
- **Import errors:** Check Python dependencies in `requirements.txt`
- **Cold starts:** Upgrade to hobby plan for faster cold starts

### Render
- **Build fails:** Check build logs, ensure all dependencies in `requirements.txt`
- **Health check fails:** Verify `/health` endpoint returns 200
- **Memory issues:** Upgrade plan or optimize code

### MongoDB
- **Connection timeout:** Check IP whitelist, network access
- **Auth failed:** Verify username/password in connection string
- **Slow queries:** Add indexes, check query patterns

---

## 📞 Support

- **GitHub Issues:** [github.com/jaswanth-mjy/jobpulse/issues](https://github.com/jaswanth-mjy/jobpulse/issues)
- **Render Docs:** [render.com/docs](https://render.com/docs)
- **Vercel Docs:** [vercel.com/docs](https://vercel.com/docs)

---

**Happy Deploying! 🚀**
