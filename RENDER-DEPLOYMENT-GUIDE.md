# Render Deployment Guide - LCA Tool

Complete step-by-step guide to deploy your LCA Tool to Render.com for FREE.

---

## Prerequisites

✅ Render account connected to GitHub (You have this!)
✅ GitHub repository with latest code (Ready!)
✅ All deployment files in place (render.yaml, Dockerfiles)

---

## Deployment Steps

### Step 1: Access Render Dashboard

1. Go to https://render.com
2. Log in with your GitHub account
3. Click on **"Dashboard"** at the top

---

### Step 2: Deploy Using Blueprint

1. Click **"New +"** button (top right)
2. Select **"Blueprint"**
3. Connect your repository:
   - Repository: `naveenkumar29nl/LCA-Tool-eufsi`
   - Branch: `main`
4. Click **"Connect"**

Render will automatically detect your `render.yaml` file.

---

### Step 3: Review Configuration

Render will show you what it's going to create:

**Services to be created:**
- ✅ lca-backend (Web Service) - Your FastAPI backend
- ✅ lca-frontend (Web Service) - Your React frontend
- ✅ lca-mongodb (MongoDB Database) - Free 500MB database

**Review the configuration:**
- Region: Oregon (Free tier region)
- Plan: Free (All services)
- Auto-deploy: ON (deploys on every git push)

---

### Step 4: Configure Environment Variables

Before deploying, you may need to set/verify these:

#### Backend Environment Variables:
- `MONGO_URL` - Auto-filled from database ✓
- `DB_NAME` - Set to `lca_tool` ✓
- `JWT_SECRET_KEY` - Auto-generated ✓
- `CORS_ORIGINS` - Pre-configured ✓

#### Frontend Environment Variables:
- `REACT_APP_API_URL` - Set to backend URL ✓
- `PORT` - Set to 3000 ✓

**Note**: All variables are pre-configured in render.yaml!

---

### Step 5: Deploy!

1. Click **"Apply"** button
2. Render will start creating your services:
   - Creating MongoDB database (2-3 minutes)
   - Building backend Docker image (5-7 minutes)
   - Building frontend Docker image (3-5 minutes)
   - Deploying services

**Total deployment time: 10-15 minutes**

---

### Step 6: Monitor Deployment

You'll see three services building:

```
🔵 lca-mongodb - Creating database...
🔵 lca-backend - Building Docker image...
🔵 lca-frontend - Building Docker image...
```

Wait for all to show:
```
🟢 lca-mongodb - Live
🟢 lca-backend - Live
🟢 lca-frontend - Live
```

---

### Step 7: Get Your URLs

Once deployed, you'll have:

**Frontend URL**: `https://lca-frontend.onrender.com`
**Backend URL**: `https://lca-backend.onrender.com`
**Database**: Internal connection (not public)

---

### Step 8: Update CORS if Needed

If your frontend URL is different:

1. Go to **lca-backend** service
2. Click **"Environment"** tab
3. Update `CORS_ORIGINS` with your actual frontend URL
4. Click **"Save Changes"**
5. Service will auto-redeploy

---

### Step 9: Test Your Deployment

#### Test Backend:
```bash
# Health check
curl https://lca-backend.onrender.com/health

# API docs
# Visit: https://lca-backend.onrender.com/docs
```

#### Test Frontend:
Visit: `https://lca-frontend.onrender.com`

---

## Important Notes

### Free Tier Limitations

⚠️ **Services sleep after 15 minutes of inactivity**
- First request takes ~30 seconds to wake up
- Subsequent requests are fast
- This is normal for free tier

⚠️ **750 hours/month per service**
- More than enough for development/testing
- Roughly 1,000 hours total across all services

⚠️ **MongoDB: 500MB storage**
- Plenty for development
- ~10,000+ LCA projects

### Keeping Services Awake (Optional)

If you want to prevent sleep:

**Option 1: Use a ping service (Free)**
- https://cron-job.org (Free service)
- Ping your frontend every 14 minutes
- Keeps both services awake

**Option 2: Upgrade to paid plan**
- $7/month per service
- No sleep mode
- Better performance

---

## Troubleshooting

### Issue 1: Build Failed

**Backend build fails:**
```bash
# Check logs in Render dashboard
# Common issue: Missing dependencies

Solution:
- Verify requirements.txt is complete
- Check Dockerfile syntax
- Look at build logs for specific error
```

**Frontend build fails:**
```bash
Solution:
- Check package.json dependencies
- Verify Dockerfile
- Check for build errors in logs
```

---

### Issue 2: Service Won't Start

**Backend won't start:**
```bash
# Check environment variables
- MONGO_URL must be set
- JWT_SECRET_KEY must be set
- PORT must be 8000

Solution:
- Go to Environment tab
- Verify all variables are set
- Check logs for specific error
```

---

### Issue 3: Can't Connect to Database

```bash
Error: "Could not connect to MongoDB"

Solution:
1. Check database is running (green status)
2. Verify MONGO_URL env variable
3. Check database logs
4. Make sure IP allowlist is empty (allows all)
```

---

### Issue 4: CORS Errors

```bash
Error: "CORS policy blocked"

Solution:
1. Go to backend service
2. Environment tab
3. Update CORS_ORIGINS with your frontend URL
4. Save and redeploy
```

---

### Issue 5: Service Sleeping

```bash
First request takes 30+ seconds

This is normal for free tier!

Solutions:
- Use a ping service (cron-job.org)
- Upgrade to paid plan ($7/month)
- Accept 30s wake-up time
```

---

## Post-Deployment

### Enable Auto-Deploy

1. Go to each service settings
2. Enable **"Auto-Deploy"**
3. Now every `git push` auto-deploys!

### Add Custom Domain (Optional)

Free tier supports custom domains:

1. Go to service settings
2. Click **"Custom Domain"**
3. Add your domain
4. Update DNS records as instructed
5. SSL certificate auto-generated

---

## Monitoring

### View Logs

1. Click on service name
2. Click **"Logs"** tab
3. See real-time logs

### Check Metrics

1. Click on service
2. Click **"Metrics"** tab
3. See:
   - CPU usage
   - Memory usage
   - Request count
   - Response times

---

## Updating Your App

### Automatic Updates:
```bash
# Just push to GitHub
git add .
git commit -m "Update feature"
git push

# Render auto-deploys within 2-3 minutes
```

### Manual Deploy:
1. Go to service
2. Click **"Manual Deploy"**
3. Select **"Deploy latest commit"**

---

## Costs

### Current Setup: $0/month

- Backend: FREE
- Frontend: FREE
- Database: FREE
- Bandwidth: FREE (100GB/month)
- SSL: FREE

### If You Need More:

**Upgrade to Starter Plan ($7/month per service):**
- No sleep mode
- Better performance
- 400 hours/month compute
- Still affordable

**Total if upgraded: $21/month**
- Backend: $7/month
- Frontend: $7/month
- Database: $7/month

---

## Security Checklist

Before going live:

- [ ] Change JWT_SECRET_KEY (done automatically ✓)
- [ ] Update CORS_ORIGINS to production URLs
- [ ] Enable HTTPS only (Render does this ✓)
- [ ] Set up database backups
- [ ] Review environment variables
- [ ] Test authentication flow
- [ ] Run security audit (use security-compliance agent!)

---

## Backup & Disaster Recovery

### Database Backups:

Render free tier doesn't include automatic backups.

**Manual backup:**
```bash
# Connect to MongoDB
mongodump --uri="YOUR_MONGO_URL" --out=./backup

# Store backup locally or in cloud
```

**Automated backups:**
- Upgrade to paid MongoDB plan ($7/month)
- Includes daily automatic backups

---

## Performance Tips

1. **Optimize Docker images**
   - Use multi-stage builds (already done ✓)
   - Minimize image size

2. **Database indexes**
   - Add indexes for frequent queries
   - Use MongoDB compass to analyze

3. **Caching**
   - Add Redis for caching (optional)
   - Cache LCA calculations

4. **CDN**
   - Render includes CDN for static files
   - Frontend assets are cached

---

## Next Steps After Deployment

1. **Test everything thoroughly**
   - Create test account
   - Run LCA calculations
   - Test all features

2. **Set up monitoring**
   - Use Render metrics
   - Consider adding Sentry for error tracking

3. **Document your deployment**
   - Note down all URLs
   - Save important credentials securely

4. **Plan for scaling**
   - Monitor usage
   - Upgrade when needed

---

## Support & Help

### Render Support:
- Docs: https://render.com/docs
- Community: https://community.render.com
- Status: https://status.render.com

### If Deployment Fails:
1. Check this guide's troubleshooting section
2. Review Render logs
3. Check GitHub issues
4. Ask in Render community

---

## Alternative: Manual Service Creation

If Blueprint doesn't work, create manually:

### 1. Create Database:
1. New + → PostgreSQL/MongoDB
2. Name: lca-mongodb
3. Region: Oregon
4. Plan: Free
5. Create

### 2. Create Backend:
1. New + → Web Service
2. Connect GitHub repo
3. Runtime: Docker
4. Dockerfile path: ./backend/Dockerfile
5. Add environment variables
6. Create

### 3. Create Frontend:
1. New + → Web Service
2. Connect GitHub repo
3. Runtime: Docker
4. Dockerfile path: ./frontend/Dockerfile
5. Add environment variables
6. Create

---

## Quick Reference

### URLs to Save:
- Dashboard: https://dashboard.render.com
- Backend: https://lca-backend.onrender.com
- Frontend: https://lca-frontend.onrender.com
- Docs: https://lca-backend.onrender.com/docs

### Important Commands:
```bash
# View logs
render logs <service-name>

# Manual deploy
render deploy <service-name>

# Check status
render services list
```

---

## Success Criteria

Your deployment is successful when:

- ✅ All 3 services show green status
- ✅ Frontend loads at your URL
- ✅ Backend API responds at /health
- ✅ Can create account and login
- ✅ Can create LCA projects
- ✅ Database stores data correctly

---

**You're ready to deploy! Go to https://render.com and click "New +" → "Blueprint"**

Good luck! 🚀
