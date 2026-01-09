# 🚀 Quick Deployment Checklist

Follow these steps in order:

## ☑️ Checklist

### 1. MongoDB Atlas (5 min)
- [ ] Sign up at mongodb.com/cloud/atlas
- [ ] Create M0 FREE cluster
- [ ] Create database user
- [ ] Allow access from anywhere
- [ ] Copy connection string
- [ ] Replace `<password>` with actual password

### 2. GitHub (5 min)
- [ ] Create GitHub account (if needed)
- [ ] Create new repository
- [ ] Push your code:
  ```bash
  cd "C:\My Projects\LCA-Tool-eufsi"
  git add .
  git commit -m "Ready for deployment"
  git push origin main
  ```

### 3. Render.com - Backend (10 min)
- [ ] Sign up at render.com
- [ ] New → Web Service
- [ ] Connect GitHub repo
- [ ] Build: `pip install -r backend/requirements.txt`
- [ ] Start: `cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT`
- [ ] Add environment variables:
  - `MONGO_URL` = your MongoDB connection string
  - `DB_NAME` = lca_tool
  - `JWT_SECRET_KEY` = any random string
  - `CORS_ORIGINS` = * (update later)
- [ ] Deploy and copy your backend URL

### 4. Vercel - Frontend (5 min)
- [ ] Sign up at vercel.com
- [ ] Import GitHub repo
- [ ] Root Directory: `frontend`
- [ ] Build: `npm install --force && npm run build`
- [ ] Add environment variable:
  - `REACT_APP_BACKEND_URL` = your Render backend URL
- [ ] Deploy!

### 5. Final Step - Update CORS (2 min)
- [ ] Go back to Render
- [ ] Update `CORS_ORIGINS` with your Vercel URL
- [ ] Save (auto-redeploys)

## ✅ Done!

Your app is live! 🎉

**Frontend URL**: `https://your-app.vercel.app`

---

## 📝 Save These URLs

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| MongoDB | mongodb+srv://... | | |
| Render Backend | https://...onrender.com | | |
| Vercel Frontend | https://...vercel.app | | |

---

## 💡 Pro Tips

1. **Backend sleeps on free tier**: First visit takes 30-60 seconds
2. **Update app**: Just push to GitHub - auto-deploys!
3. **View logs**: Check Render and Vercel dashboards
4. **MongoDB free tier**: 512MB storage = plenty for this app

---

See **DEPLOYMENT.md** for detailed instructions!
