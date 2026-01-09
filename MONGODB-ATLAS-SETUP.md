# MongoDB Atlas Setup Guide for Render Deployment

## Quick Setup (5 minutes)

### Step 1: Create MongoDB Atlas Account

1. Go to: https://www.mongodb.com/cloud/atlas/register
2. Sign up with Google/GitHub or email
3. Choose **FREE** tier (M0)

### Step 2: Create Free Cluster

1. Click **"Build a Database"**
2. Select **"M0 FREE"** tier
3. Choose cloud provider: **AWS**
4. Region: **US East (N. Virginia)** or closest to Oregon
5. Cluster name: `lca-eufsi-cluster` (or any name)
6. Click **"Create Cluster"**

Wait 1-3 minutes for cluster creation.

### Step 3: Create Database User

1. Click **"Database Access"** (left sidebar)
2. Click **"Add New Database User"**
3. Authentication Method: **Password**
4. Username: `lca_admin` (or any name)
5. Password: Click **"Autogenerate Secure Password"**
   - **COPY THIS PASSWORD!** You'll need it
6. Database User Privileges: **"Read and write to any database"**
7. Click **"Add User"**

### Step 4: Whitelist IP Addresses

1. Click **"Network Access"** (left sidebar)
2. Click **"Add IP Address"**
3. Click **"Allow Access from Anywhere"** (0.0.0.0/0)
   - This is needed for Render servers
4. Click **"Confirm"**

### Step 5: Get Connection String

1. Click **"Database"** (left sidebar)
2. Click **"Connect"** button on your cluster
3. Choose **"Connect your application"**
4. Driver: **Python**, Version: **3.12 or later**
5. Copy the connection string:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
6. **Replace `<password>`** with the password you copied earlier
7. **Replace `<username>`** with `lca_admin` (or your username)

**Example connection string:**
```
mongodb+srv://lca_admin:YOUR_PASSWORD_HERE@lca-eufsi-cluster.abc123.mongodb.net/?retryWrites=true&w=majority
```

### Step 6: Add to Render

1. Go to Render Dashboard: https://dashboard.render.com
2. Click on your **lca-eufsi-api** service
3. Click **"Environment"** tab
4. Find **MONGO_URL** variable
5. Paste your MongoDB Atlas connection string
6. Click **"Save Changes"**

**Render will automatically redeploy!**

---

## Verification

Once deployed, check logs for:
```
Connecting to MongoDB at: mongodb+srv://...
Database: lca_tool
✓ Connected successfully
```

---

## Troubleshooting

### Error: "IP address not whitelisted"
- Go to Network Access
- Add 0.0.0.0/0 (allow from anywhere)

### Error: "Authentication failed"
- Double-check username and password in connection string
- Make sure you replaced `<password>` placeholder
- Password should NOT have < or > symbols

### Error: "Connection timeout"
- Check if cluster is running (not paused)
- Verify network access settings

---

## Alternative: Use Connection String Directly

If you want to set it up quickly for testing:

1. **Temporary MongoDB** (for testing only):
   ```
   mongodb://localhost:27017/lca_tool
   ```
   ⚠️ This won't work on Render (no local MongoDB)

2. **MongoDB Atlas Free Tier** (recommended for production):
   - 512MB storage (plenty for development)
   - Shared CPU
   - No credit card required
   - Perfect for this project!

---

## Free Tier Limits

MongoDB Atlas M0 (Free):
- ✅ 512 MB storage
- ✅ Shared RAM
- ✅ No credit card required
- ✅ No time limit (forever free)
- ⚠️ Cluster pauses after 60 days of inactivity (easy to resume)

This is MORE than enough for your LCA tool!

---

## Next Steps

After setting up MongoDB Atlas:

1. ✅ Create cluster
2. ✅ Create database user
3. ✅ Whitelist IPs (0.0.0.0/0)
4. ✅ Get connection string
5. ✅ Add to Render environment variable
6. ✅ Service auto-deploys
7. ✅ Check logs for successful connection
8. ✅ Test your app at https://lca-eufsi.onrender.com

---

## Security Best Practices

1. **Use strong password** - Auto-generated is best
2. **Whitelist specific IPs** - Once you know Render's IPs (optional)
3. **Rotate passwords** - Every 90 days
4. **Monitor access** - Check Atlas dashboard for suspicious activity
5. **Enable 2FA** - On your Atlas account

---

## Backup & Monitoring

### Enable Backups (Optional - Paid)
- Atlas M0 doesn't include automatic backups
- Manual backups: Database > Browse Collections > Export

### Monitor Usage
- Dashboard shows:
  - Storage used
  - Connection count
  - Query performance
  - Alerts

---

## Quick Reference

| Setting | Value |
|---------|-------|
| Cluster Tier | M0 (Free) |
| Cloud Provider | AWS |
| Region | us-east-1 (or closest) |
| Database Name | lca_tool |
| Username | lca_admin |
| IP Whitelist | 0.0.0.0/0 |

---

**Ready to set up? It takes just 5 minutes!** 🚀

Follow steps 1-6 above, then come back and we'll verify the deployment.
