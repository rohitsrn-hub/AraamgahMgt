# 🚀 SARAI Deployment Guide - Vercel + Render + MongoDB Atlas

Complete step-by-step guide to deploy SARAI application to production.

---

## 📋 Architecture Overview

- **Frontend**: React → Deploy to **Vercel**
- **Backend**: FastAPI (Python) → Deploy to **Render**
- **Database**: MongoDB → **MongoDB Atlas** (free tier available)

---

## Part 1: MongoDB Atlas Setup (Database)

### Step 1: Create MongoDB Atlas Account
1. Go to [https://www.mongodb.com/cloud/atlas/register](https://www.mongodb.com/cloud/atlas/register)
2. Sign up for a free account
3. Create a new cluster (FREE M0 tier is sufficient)

### Step 2: Configure Database Access
1. **Database Access** (left sidebar) → **Add New Database User**
   - Username: `sarai_admin` (or any username you prefer)
   - Password: Generate a strong password (SAVE THIS!)
   - Database User Privileges: **Read and write to any database**
   - Click **Add User**

### Step 3: Configure Network Access
1. **Network Access** (left sidebar) → **Add IP Address**
   - Click **Allow Access from Anywhere** (0.0.0.0/0)
   - Confirm

### Step 4: Get Connection String
1. Go to **Database** → Click **Connect** on your cluster
2. Choose **Connect your application**
3. Copy the connection string:
   ```
   mongodb+srv://sarai_admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
4. Replace `<password>` with your actual password
5. **SAVE THIS CONNECTION STRING** - you'll need it for backend deployment

---

## Part 2: Backend Deployment (Render)

### Step 1: Prepare Backend for Deployment
No changes needed! The backend is already configured correctly.

### Step 2: Create Render Account
1. Go to [https://render.com](https://render.com)
2. Sign up using GitHub (recommended for easy deployment)

### Step 3: Create New Web Service
1. Click **New +** → **Web Service**
2. Connect your GitHub repository (or use Render's Git)
3. Configure the service:
   - **Name**: `sarai-backend` (or any name)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn server:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type**: Free (or paid for better performance)

### Step 4: Set Environment Variables (CRITICAL!)
In Render dashboard, go to **Environment** tab and add these variables:

```bash
# Database
MONGO_URL=mongodb+srv://sarai_admin:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DB_NAME=sarai_production

# JWT Security
JWT_SECRET_KEY=GENERATE_THIS_USING_COMMAND_BELOW
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# CORS (Replace with your actual Vercel domain)
CORS_ORIGINS=https://your-app-name.vercel.app
```

**Generate JWT Secret:**
Run this command on your local terminal:
```bash
openssl rand -hex 32
```
Copy the output and paste it as `JWT_SECRET_KEY` value.

### Step 5: Deploy Backend
1. Click **Create Web Service**
2. Wait for deployment to complete (5-10 minutes)
3. Once deployed, you'll get a backend URL like:
   ```
   https://sarai-backend.onrender.com
   ```
4. **SAVE THIS URL** - you'll need it for frontend

### Step 6: Create First Admin User
1. Go to Render dashboard → **Shell** tab
2. Run the admin creation script:
   ```bash
   cd /opt/render/project/src
   python scripts/create_admin.py
   ```
3. You'll see:
   ```
   ✅ Admin user created!
   Username: admin
   Password: Admin@2026!
   ```

---

## Part 3: Frontend Deployment (Vercel)

### Step 1: Update Frontend Environment Variable
1. Edit `/app/frontend/.env`:
   ```bash
   REACT_APP_BACKEND_URL=https://sarai-backend.onrender.com
   ```
   (Use your actual Render backend URL)

2. Commit this change to your repository

### Step 2: Create Vercel Account
1. Go to [https://vercel.com](https://vercel.com)
2. Sign up using GitHub (recommended)

### Step 3: Deploy Frontend
1. Click **Add New** → **Project**
2. Import your Git repository
3. Configure the project:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `yarn build` (default)
   - **Output Directory**: `build` (default)
   - **Install Command**: `yarn install` (default)

### Step 4: Set Environment Variables
In Vercel project settings → **Environment Variables**:
```bash
REACT_APP_BACKEND_URL=https://sarai-backend.onrender.com
```
(Use your actual Render backend URL)

### Step 5: Deploy
1. Click **Deploy**
2. Wait for deployment (2-5 minutes)
3. You'll get a production URL like:
   ```
   https://sarai-app.vercel.app
   ```

### Step 6: Update CORS in Backend
1. Go back to Render → Your backend service → **Environment**
2. Update `CORS_ORIGINS`:
   ```bash
   CORS_ORIGINS=https://sarai-app.vercel.app
   ```
3. Save and wait for automatic redeploy

---

## Part 4: Verify Deployment

### Step 1: Test Login
1. Go to your Vercel URL: `https://sarai-app.vercel.app`
2. You should see the login page
3. Login with:
   - **Username**: `admin`
   - **Password**: `Admin@2026!`

### Step 2: Test API Communication
1. Open browser console (F12)
2. Login and check Network tab
3. Verify API calls go to your Render backend URL
4. Check for any CORS errors (there should be none)

### Step 3: Create Additional Users
1. Login as admin
2. Go to **User Management**
3. Create staff and viewer users

---

## Part 5: Post-Deployment Security

### 🔒 CRITICAL SECURITY STEPS:

1. **Change Admin Password**
   - Login as admin
   - Change default password immediately

2. **Update JWT Secret (Production)**
   - Generate new secret: `openssl rand -hex 32`
   - Update in Render environment variables
   - All users will need to re-login

3. **Secure MongoDB**
   - Don't share MongoDB credentials
   - Use strong password
   - Keep backups enabled in Atlas

4. **Monitor Logs**
   - Render: Dashboard → Logs tab
   - Vercel: Dashboard → Deployments → View Function Logs

---

## Part 6: Troubleshooting

### Issue: CORS Errors
**Symptoms**: Login fails, browser console shows CORS error

**Solution**:
1. Check Render environment variable `CORS_ORIGINS` matches Vercel URL exactly
2. No trailing slash in URL
3. Use `https://` not `http://`

### Issue: 500 Error on Login
**Symptoms**: Login returns 500 Internal Server Error

**Solution**:
1. Check Render logs for errors
2. Verify `MONGO_URL` is correct
3. Verify `JWT_SECRET_KEY` is set
4. Check admin user was created

### Issue: Frontend Shows "Network Error"
**Symptoms**: All API calls fail

**Solution**:
1. Check `REACT_APP_BACKEND_URL` in Vercel environment variables
2. Verify backend is running (visit Render URL directly)
3. Check Render logs for crashes

### Issue: "Cannot connect to database"
**Symptoms**: Backend crashes on startup

**Solution**:
1. Verify MongoDB Atlas cluster is running
2. Check `MONGO_URL` connection string is correct
3. Verify password in connection string doesn't have special characters (URL encode if needed)
4. Ensure IP whitelist allows 0.0.0.0/0

---

## Part 7: Environment Variables Summary

### Backend (Render)
```bash
MONGO_URL=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=sarai_production
JWT_SECRET_KEY=<generated-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
CORS_ORIGINS=https://your-frontend.vercel.app
```

### Frontend (Vercel)
```bash
REACT_APP_BACKEND_URL=https://your-backend.onrender.com
```

---

## Part 8: Updating After Deployment

### Update Backend Code:
1. Push changes to GitHub
2. Render auto-deploys from `main` branch
3. Check logs for successful deployment

### Update Frontend Code:
1. Push changes to GitHub
2. Vercel auto-deploys from `main` branch
3. Visit site to see changes

### Update Environment Variables:
1. Change in Render/Vercel dashboard
2. Manual redeploy may be required

---

## 📞 Support

### Common Resources:
- MongoDB Atlas: [https://docs.atlas.mongodb.com](https://docs.atlas.mongodb.com)
- Render Docs: [https://render.com/docs](https://render.com/docs)
- Vercel Docs: [https://vercel.com/docs](https://vercel.com/docs)

### Need Help?
1. Check Render logs for backend errors
2. Check Vercel deployment logs for frontend errors
3. Check browser console for client-side errors

---

## ✅ Deployment Checklist

Before going live:
- [ ] MongoDB Atlas cluster created and configured
- [ ] Backend deployed to Render
- [ ] Environment variables set in Render
- [ ] First admin user created
- [ ] Frontend deployed to Vercel
- [ ] CORS configured correctly
- [ ] Login tested successfully
- [ ] Admin password changed from default
- [ ] Additional users created
- [ ] Backup schedule configured
- [ ] All features tested in production

---

**🎉 Your SARAI application is now live!**

**Production URLs:**
- **Frontend**: https://your-app.vercel.app
- **Backend API**: https://your-backend.onrender.com/api
- **Database**: MongoDB Atlas (managed)

**Default Admin Credentials:**
- Username: `admin`
- Password: `Admin@2026!`
- ⚠️ **CHANGE IMMEDIATELY AFTER FIRST LOGIN**
