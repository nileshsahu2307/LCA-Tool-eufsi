# 🚀 Render Deployment Checklist

Use this checklist when deploying to Render.

---

## Pre-Deployment (Do Once)

### Code Preparation
- [x] render.yaml configured
- [x] Backend Dockerfile exists
- [x] Frontend Dockerfile exists
- [x] requirements.txt complete
- [x] package.json complete
- [x] Health check endpoint exists (/health)
- [ ] All code committed to GitHub
- [ ] All code pushed to GitHub

### Security Review
- [ ] Run security-compliance agent
- [ ] No secrets in code
- [ ] .env files in .gitignore
- [ ] JWT_SECRET will be auto-generated
- [ ] CORS origins configured

---

## Deployment Steps

### 1. Access Render
- [ ] Go to https://render.com
- [ ] Log in with GitHub account
- [ ] Navigate to Dashboard

### 2. Create Blueprint
- [ ] Click "New +" → "Blueprint"
- [ ] Select repository: `naveenkumar29nl/LCA-Tool-eufsi`
- [ ] Branch: `main`
- [ ] Click "Connect"

### 3. Review Configuration
- [ ] Verify 3 services will be created:
  - [ ] lca-backend (Web Service)
  - [ ] lca-frontend (Web Service)
  - [ ] lca-mongodb (Database)
- [ ] All services on FREE plan
- [ ] Region: Oregon

### 4. Environment Variables Check
Backend should have:
- [ ] MONGO_URL (from database)
- [ ] DB_NAME = lca_tool
- [ ] JWT_SECRET_KEY (auto-generated)
- [ ] CORS_ORIGINS (configured)
- [ ] PORT = 8000

Frontend should have:
- [ ] REACT_APP_API_URL (configured)
- [ ] PORT = 3000

### 5. Deploy
- [ ] Click "Apply"
- [ ] Wait for build to complete (10-15 minutes)

---

## Post-Deployment Verification

### Check Service Status
- [ ] lca-mongodb shows 🟢 Live
- [ ] lca-backend shows 🟢 Live
- [ ] lca-frontend shows 🟢 Live

### Save URLs
```
Backend URL: https://lca-backend.onrender.com
Frontend URL: https://lca-frontend.onrender.com
```
- [ ] Backend URL saved
- [ ] Frontend URL saved

### Test Backend
- [ ] Visit: https://lca-backend.onrender.com/health
  - Should return: `{"status": "healthy"}`
- [ ] Visit: https://lca-backend.onrender.com/docs
  - Should show API documentation

### Test Frontend
- [ ] Visit: https://lca-frontend.onrender.com
  - Frontend loads successfully
- [ ] No console errors
- [ ] Can see login/signup page

### Test Functionality
- [ ] Can create new account
- [ ] Can log in
- [ ] Can create new project
- [ ] Can add activities
- [ ] Dashboard loads
- [ ] Data persists after refresh

### Update CORS (If Needed)
If frontend URL is different:
- [ ] Go to lca-backend service
- [ ] Environment tab
- [ ] Update CORS_ORIGINS
- [ ] Save and wait for redeploy

---

## Enable Auto-Deploy

For each service:
- [ ] lca-backend: Enable "Auto-Deploy"
- [ ] lca-frontend: Enable "Auto-Deploy"

Now every `git push` will auto-deploy!

---

## Optional Enhancements

### Keep Services Awake
- [ ] Set up cron-job.org to ping every 14 minutes
  - Ping: https://lca-frontend.onrender.com

### Custom Domain
- [ ] Register domain (if desired)
- [ ] Add custom domain in Render
- [ ] Update DNS records
- [ ] Wait for SSL certificate

### Monitoring
- [ ] Set up error tracking (Sentry)
- [ ] Configure uptime monitoring
- [ ] Set up alerts

---

## Troubleshooting

### If Build Fails:
1. [ ] Check build logs in Render dashboard
2. [ ] Verify Dockerfile syntax
3. [ ] Check requirements.txt/package.json
4. [ ] Review error messages

### If Service Won't Start:
1. [ ] Check service logs
2. [ ] Verify environment variables
3. [ ] Check database connection
4. [ ] Review startup command

### If Can't Connect:
1. [ ] Check CORS configuration
2. [ ] Verify API URL in frontend
3. [ ] Check network tab in browser
4. [ ] Review backend logs

---

## Rollback Plan

If deployment fails:
1. [ ] Note the error message
2. [ ] Check last successful commit
3. [ ] Revert to last working version:
   ```bash
   git revert HEAD
   git push
   ```
4. [ ] Or manually deploy previous commit in Render

---

## Success Criteria

Deployment is successful when ALL are checked:
- [ ] All services show green status
- [ ] Frontend loads and works
- [ ] Can create account and login
- [ ] Can perform LCA operations
- [ ] Data persists in database
- [ ] No errors in logs
- [ ] Health check returns 200

---

## Next Session Checklist

When you come back:
- [ ] Check service status (may be sleeping)
- [ ] Wait 30s for wake-up (free tier)
- [ ] Monitor performance
- [ ] Review logs for errors
- [ ] Check database usage

---

## Quick Commands

```bash
# Commit and push (triggers auto-deploy)
git add .
git commit -m "Your message"
git push

# Check git status
git status

# View deployment URLs
# Visit Render dashboard
```

---

## Important Notes

⚠️ **First Request Takes 30 Seconds**
- Services sleep after 15 min idle
- This is normal for free tier
- Use ping service or upgrade

⚠️ **Database Backup**
- Free tier has no auto-backup
- Manually backup important data
- Or upgrade to $7/month for backups

⚠️ **Monthly Limits**
- 750 hours per service
- 100GB bandwidth
- 500MB database storage

---

**Ready to deploy? Start with "Pre-Deployment" section!**
