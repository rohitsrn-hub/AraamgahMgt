# ⚡ Cloud Deployment - Quick Start

Get E-ARMS deployed to the cloud in 30 minutes. Follow these simplified steps.

---

## 🎯 What You'll Get

- ✅ **Frontend:** Hosted on Vercel (free tier)
- ✅ **Backend:** Hosted on Render (free tier)
- ✅ **Database:** MongoDB Atlas (free tier)
- ✅ **URL:** Your own public URL accessible from anywhere
- ✅ **SSL:** Free HTTPS certificate included
- ✅ **Cost:** $0/month (free tier)

---

## 📋 Prerequisites (5 minutes)

Create free accounts:

1. [ ] **GitHub:** https://github.com/join
2. [ ] **MongoDB Atlas:** https://www.mongodb.com/cloud/atlas/register
3. [ ] **Render:** https://render.com/register
4. [ ] **Vercel:** https://vercel.com/signup

---

## 🚀 Step 1: Push Code to GitHub (5 minutes)

```bash
# 1. Navigate to your E-ARMS folder
cd /path/to/AraamgahMgt

# 2. Initialize Git (if not already)
git init

# 3. Add all files
git add .

# 4. Commit
git commit -m "Initial commit for cloud deployment"

# 5. Create new GitHub repository at: https://github.com/new
# Name: earms-cloud
# Visibility: Private

# 6. Add remote and push (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/earms-cloud.git
git branch -M main
git push -u origin main
```

✅ **Done!** Code is now on GitHub.

---

## 🗄️ Step 2: Setup MongoDB Atlas (10 minutes)

### Create Database

1. **Login:** https://cloud.mongodb.com/
2. **New Project** → Name: `E-ARMS` → Create
3. **Build Database** → Select **M0 FREE** → **AWS** → **Mumbai** (or closest region)
4. **Cluster Name:** `Cluster0` → **Create**

### Create User

5. **Security** → **Database Access** → **Add New Database User**
   - Username: `earms_admin`
   - Password: Click "Autogenerate" → **COPY PASSWORD** (save it!)
   - Privileges: "Read and write to any database"
   - Click "Add User"

### Allow Network Access

6. **Security** → **Network Access** → **Add IP Address**
   - Click "Allow Access from Anywhere"
   - Confirm

### Get Connection String

7. **Database** → **Connect** (on your cluster)
   - Select "Connect your application"
   - Copy connection string:
     ```
     mongodb+srv://earms_admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
     ```
   - **Replace** `<password>` with your actual password (from step 5)
   - **SAVE THIS STRING** → You'll need it for Render

✅ **Done!** Database is ready.

---

## 🖥️ Step 3: Deploy Backend to Render (7 minutes)

1. **Login:** https://dashboard.render.com/
2. **New** → **Web Service**
3. **Connect GitHub** → Authorize → Select `earms-cloud` repository
4. **Configure:**
   - Name: `earms-backend`
   - Region: **Singapore** (or closest)
   - Branch: `main`
   - Root Directory: `backend`
   - Runtime: **Python 3**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - Instance Type: **Free**

5. **Environment Variables** (click "Advanced"):
   - Click "Add Environment Variable"
   - Add these 2 variables:

   | Key | Value |
   |-----|-------|
   | `MONGO_URL` | Your connection string from Step 2 |
   | `DB_NAME` | `earms_db` |

6. **Create Web Service**

7. **Wait for deployment** (5-7 minutes)
   - Watch logs
   - Look for: `Application startup complete`

8. **Copy your backend URL:**
   - Should be: `https://earms-backend.onrender.com`
   - **SAVE THIS URL**

9. **Test:** Open `https://earms-backend.onrender.com/api/health`
   - Should show: `{"status":"healthy",...}`

✅ **Done!** Backend is live.

---

## 🌐 Step 4: Deploy Frontend to Vercel (5 minutes)

1. **Login:** https://vercel.com/login
2. **Add New** → **Project**
3. **Import Git Repository** → Select `earms-cloud`
4. **Configure:**
   - Project Name: `earms-frontend`
   - Framework: **Create React App** (auto-detected)
   - Root Directory: `frontend`
   - Build Command: `yarn build` (auto-detected)
   - Output Directory: `build` (auto-detected)

5. **Environment Variables:**
   - Click "Environment Variables"
   - Add:

   | Name | Value |
   |------|-------|
   | `REACT_APP_BACKEND_URL` | Your Render URL from Step 3 (e.g., `https://earms-backend.onrender.com`) |

6. **Deploy**

7. **Wait for deployment** (2-3 minutes)

8. **Your frontend URL:** `https://earms-frontend.vercel.app`
   - Or: `https://earms-frontend-xyz123.vercel.app`
   - **SAVE THIS URL**

✅ **Done!** Frontend is live.

---

## 🎉 Step 5: Test Your Deployment (3 minutes)

1. **Open your frontend URL:** `https://earms-frontend.vercel.app`

2. **Setup Wizard should appear:**
   - Configure room rates:
     - Cat I: ₹500
     - Cat II: ₹400
     - Def Civ: ₹600
   - Default advance: ₹400
   - Add 6 Cat I rooms: C1-01, C1-02, C1-03, C1-04, C1-05, C1-06
   - Add 8 Cat II rooms: C2-01 through C2-08
   - Add a staff member: Name: "Duty Officer", Type: Army
   - Click "Complete Setup"

3. **Test booking:**
   - Click "New Booking"
   - Fill details:
     - Rank: Nb Sub
     - Name: Test Guest
     - Dates: Tomorrow to 2 days later
     - Select 1 room
     - Payment: Cash, Receipt: TEST001
   - Submit
   - Verify booking appears in Bookings page

✅ **Success!** Your E-ARMS is now deployed and accessible worldwide!

---

## 📌 Your Deployment Summary

After completing all steps, save these URLs:

```
Frontend (Main App):
https://earms-frontend.vercel.app

Backend API:
https://earms-backend.onrender.com

Health Check:
https://earms-backend.onrender.com/api/health

MongoDB Atlas Dashboard:
https://cloud.mongodb.com/

Render Dashboard:
https://dashboard.render.com/

Vercel Dashboard:
https://vercel.com/dashboard
```

---

## 🔄 Updating Your App

Made code changes? Deploy updates:

```bash
git add .
git commit -m "Your update description"
git push origin main
```

- **Vercel** auto-deploys frontend (30 seconds)
- **Render** auto-deploys backend (2-3 minutes)

No manual build commands needed!

---

## ⚠️ Important Notes

### Render Free Tier Limitation

- Backend **spins down** after 15 minutes of inactivity
- First request after spin-down takes **30-60 seconds**
- Subsequent requests are fast

**Solutions:**
1. Upgrade to Render paid plan ($7/month) - no spin-down
2. Use UptimeRobot to ping every 5 minutes (free): https://uptimerobot.com/

---

## 🆘 Troubleshooting

### Backend health check fails

1. Check Render logs: Dashboard → earms-backend → Logs
2. Verify `MONGO_URL` has correct password
3. Check MongoDB Atlas Network Access allows `0.0.0.0/0`

### Frontend can't connect to backend

1. Check browser console (F12) for errors
2. Verify `REACT_APP_BACKEND_URL` in Vercel settings
3. Ensure backend URL is `https://` (not `http://`)
4. No trailing slash in backend URL

### "Service Unavailable" error

- Backend is spinning down (free tier)
- Wait 30-60 seconds and refresh
- Or upgrade to paid plan

---

## 📚 Full Documentation

For detailed guides:

- **Complete Guide:** `CLOUD_DEPLOYMENT.md`
- **Checklist:** `CLOUD_DEPLOYMENT_CHECKLIST.md`
- **Environment Variables:** `ENVIRONMENT_VARIABLES.md`
- **Local vs Cloud:** `DEPLOYMENT_COMPARISON.md`

---

## 🎯 Next Steps

1. [ ] Share your frontend URL with users
2. [ ] Bookmark your dashboards (MongoDB, Render, Vercel)
3. [ ] Set up custom domain (optional)
4. [ ] Configure UptimeRobot monitoring (optional)
5. [ ] Create admin accounts if needed
6. [ ] Test all features end-to-end

---

## 💰 Upgrade Options (Optional)

Current: **$0/month** (Free tier)

**If you need:**
- No backend spin-down → Upgrade Render to $7/month
- More database storage → Upgrade Atlas to $9/month
- Custom domain with better performance → Keep Vercel free

**Total for production:** ~$16/month

---

**🎉 Congratulations! Your E-ARMS is now live on the cloud!**

Access it from anywhere: `https://earms-frontend.vercel.app`
