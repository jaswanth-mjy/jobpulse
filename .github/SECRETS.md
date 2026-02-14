# GitHub Actions Secrets Configuration

This guide explains how to configure GitHub secrets for the CI/CD pipeline.

## Required Secrets

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) requires these secrets:

### 1. VERCEL_TOKEN
**Purpose**: Authenticate with Vercel for automated deployments

**How to get it**:
1. Go to https://vercel.com/account/tokens
2. Click "Create Token"
3. Name it: "GitHub Actions CI/CD"
4. Set scope: "Full Account"
5. Click "Create"
6. Copy the token immediately (it won't be shown again)

**Add to GitHub**:
1. Go to your GitHub repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `VERCEL_TOKEN`
4. Value: Paste your Vercel token
5. Click "Add secret"

### 2. RENDER_DEPLOY_HOOK
**Purpose**: Trigger Render deployments on push to main

**How to get it**:
1. Go to https://dashboard.render.com/
2. Select your service
3. Go to Settings → Deploy Hook
4. Click "Create Deploy Hook"
5. Name it: "GitHub Actions"
6. Copy the webhook URL

**Add to GitHub**:
1. Go to your GitHub repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `RENDER_DEPLOY_HOOK`
4. Value: Paste your Render deploy hook URL
5. Click "Add secret"

---

## Verifying Secrets

After adding secrets, verify they're configured:

1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. You should see:
   - `VERCEL_TOKEN`
   - `RENDER_DEPLOY_HOOK`

---

## Testing the CI/CD Pipeline

### Trigger a Workflow

1. Make a commit to main branch:
   ```bash
   git add -A
   git commit -m "Test CI/CD pipeline"
   git push origin main
   ```

2. Watch the workflow:
   - Go to GitHub repo → Actions tab
   - Click on the latest workflow run
   - Monitor each job: lint, test, security, build, deploy

### What Happens

The pipeline will:
1. **Lint**: Check code quality (Black, Flake8, Pylint)
2. **Test**: Run pytest with coverage
3. **Security**: Scan for vulnerabilities (Safety, Bandit)
4. **Build**: Verify Python compilation
5. **Deploy to Vercel**: Automatic production deployment
6. **Deploy to Render**: Trigger Render deployment

---

## Optional: Additional Secrets

### For Codecov (Code Coverage)
If you want code coverage reports:

1. Go to https://codecov.io/
2. Sign in with GitHub
3. Add your repository
4. Get the upload token

Add to GitHub:
- Name: `CODECOV_TOKEN`
- Value: Your Codecov token

### For Slack Notifications
If you want deployment notifications in Slack:

1. Create a Slack webhook: https://api.slack.com/messaging/webhooks
2. Add to GitHub:
   - Name: `SLACK_WEBHOOK_URL`
   - Value: Your Slack webhook URL

Then update `.github/workflows/ci-cd.yml` to add notification step.

---

## Troubleshooting

### Workflow Fails: "Secret not found"
- Ensure secret names match exactly (case-sensitive)
- Verify secrets are added at repository level (not organization)
- Check secret values don't have extra spaces

### Vercel Deployment Fails
- Check `VERCEL_TOKEN` is valid and not expired
- Ensure Vercel project is linked (run `vercel link` locally first)
- Check vercel.json configuration is correct

### Render Deployment Fails
- Verify `RENDER_DEPLOY_HOOK` URL is correct
- Check Render service is active
- Ensure render.yaml is in the repository

---

## Security Best Practices

1. **Never commit secrets to git**
   - Always use GitHub Secrets for sensitive values
   - Check .gitignore includes .env

2. **Rotate secrets periodically**
   - Update Vercel tokens every 90 days
   - Regenerate deploy hooks if compromised

3. **Use minimal permissions**
   - Vercel tokens: Only grant necessary scopes
   - GitHub: Use environment-specific secrets when possible

4. **Monitor usage**
   - Check GitHub Actions logs for unauthorized access
   - Review Vercel deployment history

---

## Quick Setup Script

Run this after adding secrets to test the workflow:

```bash
# Create a test commit
echo "# CI/CD Test" >> .github/workflows/README.md
git add .github/workflows/README.md
git commit -m "Test: Verify CI/CD pipeline"
git push origin main

# Watch the workflow
echo "View workflow at: https://github.com/$(git config --get remote.origin.url | sed 's/.*://;s/.git$//')/actions"
```

---

## References

- GitHub Actions Secrets: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- Vercel Token Guide: https://vercel.com/docs/rest-api#creating-an-access-token
- Render Deploy Hooks: https://render.com/docs/deploy-hooks
