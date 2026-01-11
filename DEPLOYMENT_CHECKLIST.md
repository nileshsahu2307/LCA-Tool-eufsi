# Deployment Checklist - EUFSI LCA Tool

## 🚀 After Pushing Code Changes

### 1. Push Local Changes to GitHub
```bash
git push origin main
```

### 2. On Deployment Server (SSH into your server)

#### A. Pull Latest Code
```bash
cd /path/to/LCA-Tool-eufsi-main
git pull origin main
```

#### B. Rebuild Frontend
```bash
cd frontend
npm install  # Install any new dependencies
npm run build  # Build production React app
```

**This creates the `frontend/dist` or `frontend/build` folder with compiled JavaScript.**

#### C. Restart Backend
```bash
cd ../backend

# If using systemd service:
sudo systemctl restart lca-backend

# OR if using PM2:
pm2 restart lca-backend

# OR if running manually:
pkill -f "uvicorn server:app"
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

#### D. Clear Browser Cache
**Important:** Your browser might cache the old JavaScript files.

- **Hard refresh:** `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
- **Clear cache:** Browser settings → Clear browsing data → Cached images and files

### 3. Verify Changes

#### Check Backend Changes (Enhanced TEXTILE Schema)
```bash
# Test the new schema endpoint
curl http://your-server.com:8000/api/schemas/textile

# Should show 11 sections (was 4 before)
```

#### Check Frontend Changes (Batch Assessment Page)
1. Navigate to: `http://your-server.com/batch-assessment`
2. You should see:
   - "Batch Textile LCA Assessment" header
   - Alert about textile-only processing
   - 4-step process indicator
   - Download template button

#### Check Batch Processing Endpoints
```bash
# Test CSV template generation
curl http://your-server.com:8000/api/schemas/textile/csv-template -o template.csv

# Should download a CSV with 70+ columns
```

---

## 🔧 Common Deployment Issues

### Issue 1: Frontend Changes Not Showing
**Cause:** React app not rebuilt
**Fix:**
```bash
cd frontend
npm run build
```

### Issue 2: Backend Changes Not Showing
**Cause:** FastAPI server not restarted
**Fix:**
```bash
sudo systemctl restart lca-backend
# OR
pm2 restart lca-backend
```

### Issue 3: "404 Not Found" on `/batch-assessment`
**Cause:** Frontend routing not configured on server
**Fix:** Ensure your web server (nginx/Apache) redirects all routes to index.html

**For nginx:**
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### Issue 4: API Calls Failing
**Cause:** CORS or API URL misconfiguration
**Fix:** Check `frontend/.env` or `frontend/vite.config.js`:
```env
VITE_API_URL=http://your-actual-server.com:8000
```

### Issue 5: Browser Shows Old Version
**Cause:** Aggressive caching
**Fix:**
1. Hard refresh: `Ctrl + Shift + R`
2. Clear browser cache completely
3. Try incognito/private window

---

## 📋 Quick Deployment Script

Create this file on your server: `/path/to/deploy.sh`

```bash
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Pull latest code
echo "📥 Pulling latest code from GitHub..."
git pull origin main

# Rebuild frontend
echo "🔨 Building frontend..."
cd frontend
npm install
npm run build

# Restart backend
echo "🔄 Restarting backend..."
cd ../backend
pm2 restart lca-backend || sudo systemctl restart lca-backend

echo "✅ Deployment complete!"
echo "🧹 Remember to clear browser cache: Ctrl + Shift + R"
```

Make it executable:
```bash
chmod +x deploy.sh
```

Run it after each push:
```bash
./deploy.sh
```

---

## 🎯 Verification Steps

After deployment, verify these changes:

### ✅ Enhanced TEXTILE Schema (11 sections)
1. Go to "New Assessment"
2. Select "Textile Products"
3. You should see these sections:
   - Product Information
   - Fiber Composition
   - Yarn Production (NEW)
   - Fabric Construction (NEW)
   - Wet Processing (EXPANDED)
   - Cut, Make & Trim
   - Packaging (NEW)
   - Manufacturing Waste Management (NEW)
   - Logistics & Transportation
   - Use Phase (Optional) (NEW)
   - End of Life (Optional) (NEW)

### ✅ Batch Assessment Page
1. Navigate to `/batch-assessment`
2. Should see textile-only batch processing interface
3. Download template button should work
4. Template should have 70+ columns

### ✅ BAWEAR Unchanged
1. Go to "New Assessment"
2. Select "Textile (bAwear Detailed)"
3. Should still show original 10-section structure
4. **Should NOT have batch processing option**

---

## 📞 Troubleshooting Commands

```bash
# Check if backend is running
ps aux | grep uvicorn

# Check backend logs
tail -f backend/logs/app.log
# OR
pm2 logs lca-backend

# Check frontend build output
ls -la frontend/dist  # or frontend/build

# Test backend health
curl http://localhost:8000/health

# Check git status
git log --oneline -5
git status
```

---

## 🔐 Security Note

Make sure to set proper environment variables on the server:
```bash
# backend/.env
DATABASE_URL=mongodb://...
JWT_SECRET=...
ECOINVENT_PATH=/path/to/ecoinvent
```

---

## 📝 Deployment Log Template

After each deployment, log:
- Date/Time: ___________
- Commits deployed: ___________
- Frontend rebuilt: ☐ Yes ☐ No
- Backend restarted: ☐ Yes ☐ No
- Changes verified: ☐ Yes ☐ No
- Issues encountered: ___________
