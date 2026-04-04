# ✅ Cloud Deployment Checklist

Use this checklist to deploy E-ARMS to Vercel + Render + MongoDB Atlas.

---

## 📋 Pre-Deployment Checklist

- [ ] GitHub account created
- [ ] MongoDB Atlas account created
- [ ] Render account created
- [ ] Vercel account created
- [ ] Code pushed to GitHub repository

---

## 🗄️ MongoDB Atlas Setup

- [ ] Create new project: `E-ARMS`
- [ ] Create M0 FREE cluster
- [ ] Create database user (`earms_admin`)
- [ ] **SAVE** username and password securely
- [ ] Configure network access: Allow `0.0.0.0/0`
- [ ] Get connection string
- [ ] **SAVE** connection string (replace `<password>`)
- [ ] Test connection (optional: use MongoDB Compass)

**Connection String:**
```
mongodb+srv://earms_admin:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

---

## 🖥️ Render Backend Deployment

- [ ] Login to Render dashboard
- [ ] New Web Service
- [ ] Connect GitHub repository
- [ ] Configure service:
  - [ ] Name: `earms-backend`
  - [ ] Root Directory: `backend`
  - [ ] Build Command: `pip install -r requirements.txt`
  - [ ] Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
  - [ ] Instance Type: Free
- [ ] Add environment variables:
  - [ ] `MONGO_URL` = (your MongoDB connection string)
  - [ ] `DB_NAME` = `earms_db`
  - [ ] `CORS_ORIGINS` = `*`
- [ ] Click "Create Web Service"
- [ ] Wait for deployment (5-10 minutes)
- [ ] **SAVE** backend URL: `https://earms-backend.onrender.com`
- [ ] Test health check: `https://earms-backend.onrender.com/api/health`
- [ ] Verify response: `{"status":"healthy","service":"E-ARMS Backend","database":"connected"}`

---

## 🌐 Vercel Frontend Deployment

- [ ] Login to Vercel dashboard
- [ ] New Project
- [ ] Import Git Repository (select your GitHub repo)
- [ ] Configure project:
  - [ ] Project Name: `earms-frontend`
  - [ ] Framework: Create React App
  - [ ] Root Directory: `frontend`
  - [ ] Build Command: `yarn build`
  - [ ] Output Directory: `build`
- [ ] Add environment variable:
  - [ ] `REACT_APP_BACKEND_URL` = `https://earms-backend.onrender.com`
- [ ] Click "Deploy"
- [ ] Wait for deployment (2-5 minutes)
- [ ] **SAVE** frontend URL: `https://earms-frontend.vercel.app`
- [ ] Open frontend URL in browser
- [ ] Verify Command Center page loads

---

## 🔐 Update CORS (Optional - For Production)

- [ ] Copy your Vercel frontend URL
- [ ] Go to Render > earms-backend > Environment
- [ ] Update `CORS_ORIGINS` to your frontend URL:
  ```
  CORS_ORIGINS=https://earms-frontend.vercel.app
  ```
- [ ] Click "Save"
- [ ] Backend will auto-redeploy (2-3 minutes)

---

## 🧪 End-to-End Testing

- [ ] Open frontend: `https://earms-frontend.vercel.app`
- [ ] Setup Wizard appears
- [ ] Complete setup:
  - [ ] Configure room rates
  - [ ] Add rooms (e.g., C1-01 to C1-06)
  - [ ] Add staff members
  - [ ] Click "Complete Setup"
- [ ] Test booking:
  - [ ] Click "New Booking"
  - [ ] Fill guest details
  - [ ] Select dates and rooms
  - [ ] Enter payment details
  - [ ] Submit
- [ ] Verify booking appears in Bookings page
- [ ] Test check-in:
  - [ ] Click "Check In"
  - [ ] Fill personal details
  - [ ] Submit
- [ ] Test dashboard:
  - [ ] Navigate to Dashboard
  - [ ] Verify occupancy shows 1 room occupied
  - [ ] Check analytics
- [ ] Test check-out:
  - [ ] Go to Bookings
  - [ ] Click "Check Out"
  - [ ] Fill feedback form
  - [ ] Submit
  - [ ] Verify PDF receipt downloads

---

## 📊 Post-Deployment

- [ ] Bookmark frontend URL
- [ ] Bookmark backend health check URL
- [ ] Save MongoDB Atlas dashboard link
- [ ] Save Render dashboard link
- [ ] Save Vercel dashboard link
- [ ] Document credentials securely (password manager)
- [ ] Set up UptimeRobot monitor (optional - prevents backend spin-down)
  - [ ] Add monitor: `https://earms-backend.onrender.com/api/health`
  - [ ] Interval: 5 minutes
- [ ] Share frontend URL with users

---

## 🎉 Deployment Complete!

**Your E-ARMS app is now live and accessible worldwide!**

### 🔗 Quick Access Links:

- **Frontend:** https://earms-frontend.vercel.app
- **Backend Health:** https://earms-backend.onrender.com/api/health
- **MongoDB Atlas:** https://cloud.mongodb.com/
- **Render Dashboard:** https://dashboard.render.com/
- **Vercel Dashboard:** https://vercel.com/dashboard

---

## 🔄 Future Updates

To deploy code changes:

1. Make changes locally
2. `git add . && git commit -m "Update message"`
3. `git push origin main`
4. Vercel auto-deploys frontend (30 seconds)
5. Render auto-deploys backend (2-3 minutes)

---

## 🆘 Troubleshooting

If something doesn't work:

1. **Check Render logs:** Dashboard > earms-backend > Logs
2. **Check browser console:** F12 > Console tab
3. **Verify environment variables:**
   - Render: `MONGO_URL`, `DB_NAME`, `CORS_ORIGINS`
   - Vercel: `REACT_APP_BACKEND_URL`
4. **Test backend health:** Open `/api/health` endpoint
5. **Refer to:** `CLOUD_DEPLOYMENT.md` troubleshooting section

---

**Need help? Check the full guide: `CLOUD_DEPLOYMENT.md`**
