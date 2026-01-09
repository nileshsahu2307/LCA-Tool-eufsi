# 🚀 Deployment Guide - For Beginners!

This guide will help you deploy your LCA Tool online so anyone can use it!

## What You'll Need

- ✅ A GitHub account (free)
- ✅ A Vercel account (free)
- ✅ A Render.com account (free)
- ✅ A MongoDB Atlas account (free)

Total cost: **$0** (completely free!)

---

## Part 1: Set Up MongoDB (5 minutes) ☁️

### Step 1: Create Account
1. Go to **https://www.mongodb.com/cloud/atlas/register**
2. Sign up for free
3. Complete the welcome questionnaire

### Step 2: Create Free Database
1. Click "Build a Database"
2. Select **"M0 - FREE"** tier
3. Choose **AWS** as provider
4. Pick a region close to you
5. Name it: `lca-cluster`
6. Click "Create Deployment"

### Step 3: Create Database User
1. In the popup, choose "Username and Password"
2. Username: `lcauser`
3. Password: (make one up and **SAVE IT!**)
4. Click "Create Database User"

### Step 4: Allow Network Access
1. Click "Network Access" in left sidebar
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere"
4. Click "Confirm"

### Step 5: Get Connection String
1. Click "Database" in left sidebar
2. Click "Connect" on your cluster
3. Click "Drivers"
4. Copy the connection string (looks like this):
   ```
   mongodb+srv://lcauser:<password>@lca-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. **Replace `<password>` with your actual password!**
6. **Save this string somewhere safe!**

---

## Part 2: Push Code to GitHub (5 minutes) 📦

### If you don't have the code on GitHub yet:

1. Open Command Prompt (Windows) or Terminal (Mac/Linux)
2. Navigate to your project:
   ```bash
   cd "C:\My Projects\LCA-Tool-eufsi"
   ```

3. Initialize Git (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit - LCA Tool"
   ```

4. Create a new repository on GitHub:
   - Go to **https://github.com/new**
   - Repository name: `LCA-Tool-eufsi`
   - Make it **Public**
   - Click "Create repository"

5. Connect and push:
   ```bash
   git remote add origin https://github.com/YOUR-USERNAME/LCA-Tool-eufsi.git
   git branch -M main
   git push -u origin main
   ```
   Replace `YOUR-USERNAME` with your actual GitHub username!

---

## Part 3: Deploy Backend to Render (10 minutes) 🖥️

### Step 1: Create Render Account
1. Go to **https://render.com**
2. Click "Get Started for Free"
3. Sign up with GitHub (recommended) or email

### Step 2: Create Web Service
1. Click "New +" → "Web Service"
2. Click "Build and deploy from a Git repository"
3. Connect your GitHub account
4. Find and select your `LCA-Tool-eufsi` repository
5. Click "Connect"

### Step 3: Configure Service
Fill in these settings:

- **Name**: `lca-backend`
- **Region**: Choose closest to you
- **Branch**: `main`
- **Root Directory**: Leave blank
- **Runtime**: `Python 3`
- **Build Command**:
  ```
  pip install -r backend/requirements.txt
  ```
- **Start Command**:
  ```
  cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT
  ```

### Step 4: Add Environment Variables
Scroll down to "Environment Variables" and add these:

| Key | Value |
|-----|-------|
| `MONGO_URL` | (paste your MongoDB connection string from Part 1) |
| `DB_NAME` | `lca_tool` |
| `JWT_SECRET_KEY` | `your-super-secret-key-change-this` |
| `CORS_ORIGINS` | `*` (we'll update this later) |

### Step 5: Deploy!
1. Click "Create Web Service"
2. Wait 10-15 minutes for it to build and deploy
3. When done, you'll see a URL like: `https://lca-backend-xxxx.onrender.com`
4. **Save this URL! You'll need it for Vercel!**

---

## Part 4: Deploy Frontend to Vercel (5 minutes) 🌐

### Step 1: Create Vercel Account
1. Go to **https://vercel.com/signup**
2. Sign up with GitHub (easiest!)

### Step 2: Import Project
1. Click "Add New..." → "Project"
2. Import your `LCA-Tool-eufsi` repository
3. Click "Import"

### Step 3: Configure Project
In the configuration screen:

- **Framework Preset**: Create React App
- **Root Directory**: Click "Edit" → Select `frontend`
- **Build Command**:
  ```
  npm install --force && npm run build
  ```
- **Output Directory**: `build`
- **Install Command**:
  ```
  npm install --force
  ```

### Step 4: Add Environment Variable
Click "Environment Variables" and add:

| Key | Value |
|-----|-------|
| `REACT_APP_BACKEND_URL` | `https://lca-backend-xxxx.onrender.com` (your Render URL from Part 3) |

### Step 5: Deploy!
1. Click "Deploy"
2. Wait 5-10 minutes
3. When done, Vercel will show you a URL like: `https://lca-tool-eufsi.vercel.app`
4. **This is your live website!** 🎉

---

## Part 5: Update CORS (Final Step!) 🔒

Now we need to tell the backend to accept requests from your Vercel site.

1. Go back to **Render.com**
2. Click on your `lca-backend` service
3. Click "Environment" in the left sidebar
4. Find `CORS_ORIGINS`
5. Update it to your Vercel URL:
   ```
   https://lca-tool-eufsi.vercel.app
   ```
6. Click "Save Changes"
7. Render will automatically redeploy (takes 2-3 minutes)

---

## 🎊 YOU'RE DONE!

Your LCA Tool is now live on the internet!

- **Your Website**: `https://lca-tool-eufsi.vercel.app`
- **Backend API**: `https://lca-backend-xxxx.onrender.com/api`
- **API Docs**: `https://lca-backend-xxxx.onrender.com/docs`

Share the website URL with anyone - they can create accounts and use it!

---

## ⚠️ Important Notes

### Free Tier Limitations:

**Render.com (Backend):**
- ✅ Free forever
- ⚠️ Sleeps after 15 minutes of inactivity
- ⏰ Takes 30-60 seconds to wake up on first visit
- 💡 Tip: Use a service like UptimeRobot to ping it every 10 minutes

**Vercel (Frontend):**
- ✅ 100GB bandwidth per month
- ✅ Always fast, never sleeps
- ✅ Automatic HTTPS

**MongoDB Atlas:**
- ✅ 512MB storage (enough for hundreds of projects)
- ✅ Shared cluster (a bit slower but fine for small apps)

---

## Troubleshooting

### "Cannot connect to backend"
- Check that CORS_ORIGINS matches your Vercel URL exactly
- Check that REACT_APP_BACKEND_URL is set correctly in Vercel
- Wait 30 seconds - backend might be waking up from sleep

### "Build failed" on Vercel
- Make sure Root Directory is set to `frontend`
- Make sure you're using `--force` flag in install command

### "Build failed" on Render
- Check Environment Variables are set correctly
- Check build logs for specific errors

---

## Updating Your App

When you make changes to your code:

1. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Updated feature X"
   git push
   ```

2. Vercel and Render will **automatically redeploy**! 🚀

No need to do anything else - it's all automatic!

---

## Need Help?

If something doesn't work, check:
1. All environment variables are set correctly
2. URLs don't have trailing slashes
3. MongoDB connection string has the password replaced
4. You waited long enough for builds to complete

Still stuck? Copy the error message and ask for help!
