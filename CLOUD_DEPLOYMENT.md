# 🚀 E-ARMS Cloud Deployment Guide

Complete guide to deploy E-ARMS online using **Vercel (Frontend) + Render (Backend) + MongoDB Atlas (Database)**.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [MongoDB Atlas Setup](#1-mongodb-atlas-setup-database)
3. [Render Backend Deployment](#2-render-backend-deployment)
4. [Vercel Frontend Deployment](#3-vercel-frontend-deployment)
5. [Environment Variables Configuration](#4-environment-variables-configuration)
6. [Testing Your Deployment](#5-testing-your-deployment)
7. [Troubleshooting](#6-troubleshooting)
8. [Cost Breakdown](#7-cost-breakdown)

---

## Prerequisites

Before you begin, create free accounts on:

- ✅ **MongoDB Atlas** - https://www.mongodb.com/cloud/atlas/register
- ✅ **Render** - https://render.com/register
- ✅ **Vercel** - https://vercel.com/signup
- ✅ **GitHub** - https://github.com/join (to host your code)

**Total Setup Time:** ~30-45 minutes

---

## 1. MongoDB Atlas Setup (Database)

### Step 1.1: Create a Cluster

1. **Login to MongoDB Atlas**: https://cloud.mongodb.com/
2. **Create New Project**:
   - Click "New Project"
   - Name: `E-ARMS`
   - Click "Create Project"

3. **Build a Database**:
   - Click "Build a Database"
   - Select **M0 FREE** tier (512 MB storage, shared)
   - **Cloud Provider:** AWS
   - **Region:** Choose closest to your users (e.g., `Mumbai (ap-south-1)` for India)
   - **Cluster Name:** `Cluster0` (or your choice)
   - Click "Create"

### Step 1.2: Create Database User

1. **Security > Database Access**:
   - Click "Add New Database User"
   - **Authentication Method:** Password
   - **Username:** `earms_admin` (save this)
   - **Password:** Click "Autogenerate Secure Password" (SAVE THIS PASSWORD!)
   - **Database User Privileges:** Read and write to any database
   - Click "Add User"

### Step 1.3: Configure Network Access

1. **Security > Network Access**:
   - Click "Add IP Address"
   - **Option 1 (Recommended for development):**
     - Click "Allow Access from Anywhere"
     - IP: `0.0.0.0/0`
   - **Option 2 (More secure):**
     - Add Render's IP addresses (you'll get these from Render dashboard)
   - Click "Confirm"

### Step 1.4: Get Connection String

1. **Deployment > Database**:
   - Click "Connect" on your cluster
   - Select "Connect your application"
   - **Driver:** Python, Version: 3.12 or later
   - **Copy the connection string**:
     ```
     mongodb+srv://earms_admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
     ```
   - **Replace `<password>`** with your actual password from Step 1.2
   - **SAVE THIS** - you'll need it for Render

**Example Connection String:**
```
mongodb+srv://earms_admin:MySecurePass123@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
```

---

## 2. Render Backend Deployment

### Step 2.1: Push Code to GitHub

1. **Create a new GitHub repository**:
   - Go to https://github.com/new
   - Repository name: `earms-cloud`
   - Visibility: Private (recommended) or Public
   - **Do NOT** initialize with README
   - Click "Create repository"

2. **Push your code to GitHub**:
   ```bash
   # Navigate to your project folder
   cd /path/to/AraamgahMgt
   
   # Initialize git (if not already)
   git init
   
   # Add all files
   git add .
   
   # Commit
   git commit -m "Initial commit for cloud deployment"
   
   # Add remote (replace YOUR_USERNAME)
   git remote add origin https://github.com/YOUR_USERNAME/earms-cloud.git
   
   # Push to GitHub
   git branch -M main
   git push -u origin main
   ```

### Step 2.2: Create Render Web Service

1. **Login to Render**: https://dashboard.render.com/
2. **New > Web Service**
3. **Connect Repository**:
   - Click "Connect account" (GitHub)
   - Authorize Render to access your GitHub
   - Select your `earms-cloud` repository

4. **Configure Service**:
   - **Name:** `earms-backend`
   - **Region:** Singapore (or closest to your users)
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     uvicorn server:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type:** Free (512 MB RAM, spins down after inactivity)

5. **Environment Variables** (Click "Advanced" > "Add Environment Variable"):
   
   | Key | Value |
   |-----|-------|
   | `MONGO_URL` | Your MongoDB Atlas connection string from Step 1.4 |
   | `DB_NAME` | `earms_db` |
   | `CORS_ORIGINS` | `*` (or your Vercel domain later) |

   **Example:**
   ```
   MONGO_URL=mongodb+srv://earms_admin:MySecurePass123@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
   DB_NAME=earms_db
   CORS_ORIGINS=*
   ```

6. **Click "Create Web Service"**

### Step 2.3: Wait for Deployment

- Render will build and deploy your backend
- **First deployment takes 5-10 minutes**
- Watch the logs in real-time
- Once you see: `Application startup complete` → ✅ Backend is live!

### Step 2.4: Get Your Backend URL

- Your backend URL will be: `https://earms-backend.onrender.com`
- **Test it:** Open `https://earms-backend.onrender.com/api/health` in browser
- Should return: `{"status":"healthy","service":"E-ARMS Backend","database":"connected"}`

**SAVE THIS URL** - you'll need it for Vercel!

---

## 3. Vercel Frontend Deployment

### Step 3.1: Install Vercel CLI (Optional)

```bash
npm install -g vercel
```

### Step 3.2: Deploy via Vercel Dashboard (Recommended)

1. **Login to Vercel**: https://vercel.com/login
2. **New Project**:
   - Click "Add New..." > "Project"
   - Click "Import Git Repository"
   - Select your `earms-cloud` repository from GitHub
   - Click "Import"

3. **Configure Project**:
   - **Project Name:** `earms-frontend`
   - **Framework Preset:** Create React App
   - **Root Directory:** `frontend`
   - **Build Command:** `yarn build` (should auto-detect)
   - **Output Directory:** `build` (should auto-detect)
   - **Install Command:** `yarn install`

4. **Environment Variables**:
   - Click "Environment Variables"
   - Add variable:
     
     | Name | Value |
     |------|-------|
     | `REACT_APP_BACKEND_URL` | `https://earms-backend.onrender.com` (from Step 2.4) |

   **Important:** Use your actual Render backend URL!

5. **Click "Deploy"**

### Step 3.3: Wait for Deployment

- Vercel will build and deploy your frontend
- **First deployment takes 2-5 minutes**
- Watch the build logs
- Once complete: ✅ Frontend is live!

### Step 3.4: Get Your Frontend URL

- Your frontend URL will be: `https://earms-frontend.vercel.app`
- Or custom domain like: `https://earms-frontend-abc123.vercel.app`

---

## 4. Environment Variables Configuration

### 🔐 Backend Environment Variables (Render)

Add these in Render Dashboard > Your Service > Environment:

```bash
MONGO_URL=mongodb+srv://earms_admin:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DB_NAME=earms_db
CORS_ORIGINS=https://earms-frontend.vercel.app,https://earms-frontend-abc123.vercel.app
```

**Note:** Update `CORS_ORIGINS` with your actual Vercel URL for security.

### 🎨 Frontend Environment Variables (Vercel)

Add these in Vercel Dashboard > Project > Settings > Environment Variables:

```bash
REACT_APP_BACKEND_URL=https://earms-backend.onrender.com
```

**Important:** Must match your Render backend URL exactly!

---

## 5. Testing Your Deployment

### ✅ Backend Health Check

1. Open: `https://earms-backend.onrender.com/api/health`
2. Should return:
   ```json
   {
     "status": "healthy",
     "service": "E-ARMS Backend",
     "database": "connected"
   }
   ```

### ✅ Frontend Access

1. Open: `https://earms-frontend.vercel.app`
2. You should see the **Command Center** landing page
3. Click "Settings" to run the setup wizard

### ✅ End-to-End Test

1. **Complete Setup Wizard**:
   - Navigate to Settings
   - Configure room rates, add rooms, add staff
   - Click "Complete Setup"

2. **Create a Test Booking**:
   - Click "New Booking" from Command Center
   - Fill guest details
   - Select dates and rooms
   - Enter payment details
   - Submit

3. **Check Dashboard**:
   - Navigate to Dashboard
   - Verify booking appears
   - Check occupancy status

4. **Test Check-In**:
   - Go to Bookings page
   - Click "Check In" on your test booking
   - Fill all details
   - Submit

5. **Test Check-Out**:
   - Click "Check Out" on checked-in booking
   - Fill feedback form
   - Verify PDF receipt downloads

---

## 6. Troubleshooting

### ❌ Backend Shows "Service Unhealthy"

**Problem:** Health check fails

**Solutions:**
1. **Check MongoDB connection string**:
   - Verify password is correct (no special characters causing issues)
   - Ensure IP whitelist includes `0.0.0.0/0` in MongoDB Atlas
   - Test connection string in MongoDB Compass

2. **Check Render logs**:
   - Dashboard > Your Service > Logs
   - Look for `MongoServerError` or connection errors

3. **Verify environment variables**:
   - Dashboard > Your Service > Environment
   - Ensure `MONGO_URL` and `DB_NAME` are set correctly

### ❌ Frontend Can't Connect to Backend

**Problem:** API calls fail with CORS or network errors

**Solutions:**
1. **Check REACT_APP_BACKEND_URL**:
   - Vercel Dashboard > Project > Settings > Environment Variables
   - Must be: `https://earms-backend.onrender.com` (NOT `http://`)
   - Must NOT have trailing slash

2. **Update CORS_ORIGINS on backend**:
   - Render Dashboard > earms-backend > Environment
   - Add: `CORS_ORIGINS=https://your-frontend.vercel.app`
   - Redeploy backend

3. **Check browser console**:
   - Open Developer Tools (F12)
   - Look for CORS errors or failed API calls
   - Verify API URL is correct

### ❌ Render Free Tier "Spins Down"

**Problem:** Backend sleeps after 15 minutes of inactivity

**Solutions:**
1. **Upgrade to paid plan** ($7/month) - no spin-down
2. **Use a ping service** (free):
   - https://uptimerobot.com/ - pings your backend every 5 minutes
   - Add monitor: `https://earms-backend.onrender.com/api/health`

### ❌ MongoDB Atlas Shows "No Data"

**Problem:** Bookings not saving to database

**Solutions:**
1. **Check database name**:
   - MongoDB Atlas > Browse Collections
   - Verify `earms_db` database exists
   - Collections should auto-create on first booking

2. **Check network access**:
   - MongoDB Atlas > Network Access
   - Ensure `0.0.0.0/0` is whitelisted

3. **Test connection**:
   - Use MongoDB Compass to connect with your connection string
   - If Compass connects, backend should too

---

## 7. Cost Breakdown

| Service | Free Tier | Paid Tier | Recommended |
|---------|-----------|-----------|-------------|
| **MongoDB Atlas** | 512 MB storage (enough for ~10,000 bookings) | $9/month for 2 GB | Start with Free |
| **Render** | 512 MB RAM, spins down after 15 min | $7/month for always-on | Free (or paid if high traffic) |
| **Vercel** | 100 GB bandwidth/month | $20/month for Pro | Free tier is plenty |
| **Total** | **$0/month** | **~$16-36/month** | Free tier works great for small-medium use |

### 💡 Recommendations:

- **Start with 100% free tier** - Perfect for testing and low traffic
- **If backend spin-down is annoying** - Upgrade Render to $7/month (removes spin-down)
- **For production with high traffic** - Budget $16/month (Render + Atlas paid tiers)

---

## 8. Custom Domain (Optional)

### For Frontend (Vercel):

1. **Vercel Dashboard** > Your Project > Settings > Domains
2. **Add Domain:** `earms.yourdomain.com`
3. **Follow Vercel's DNS setup instructions**
4. **Free SSL certificate** auto-configured

### For Backend (Render):

1. **Render Dashboard** > Your Service > Settings > Custom Domain
2. **Add Domain:** `api.earms.yourdomain.com`
3. **Update DNS CNAME** record to point to Render
4. **Free SSL certificate** auto-configured

**Then update:**
- Frontend `REACT_APP_BACKEND_URL=https://api.earms.yourdomain.com`
- Backend `CORS_ORIGINS=https://earms.yourdomain.com`

---

## 🎉 You're Done!

Your E-ARMS application is now **deployed online** and accessible from anywhere!

### 📌 Quick Reference URLs:

- **Frontend:** https://earms-frontend.vercel.app
- **Backend:** https://earms-backend.onrender.com
- **Health Check:** https://earms-backend.onrender.com/api/health
- **Database:** MongoDB Atlas Dashboard

### 🔄 Updating Your Deployment:

**To deploy changes:**

1. Make code changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```
3. **Vercel** auto-deploys frontend (30 seconds)
4. **Render** auto-deploys backend (2-3 minutes)

---

## 📞 Support Resources

- **MongoDB Atlas Docs:** https://docs.atlas.mongodb.com/
- **Render Docs:** https://render.com/docs
- **Vercel Docs:** https://vercel.com/docs
- **E-ARMS GitHub Issues:** (your repo)/issues

---

**Made with ❤️ for cloud deployment of E-ARMS**
