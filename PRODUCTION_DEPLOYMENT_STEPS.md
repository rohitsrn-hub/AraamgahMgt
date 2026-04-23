# 🚀 Production Deployment Guide - Enable Authentication

## Step-by-Step Instructions to Deploy Auth Feature to Your Live App

---

## ⚠️ **IMPORTANT - Read Before Starting:**

- **Downtime**: Plan for ~15-30 minutes maintenance window
- **Backup**: Your database is on Atlas - already backed up
- **Users**: Inform users about the upcoming auth requirement
- **Test**: Ensure preview environment works perfectly before production deploy

---

## 📋 **Pre-Deployment Checklist:**

- [ ] Auth feature tested thoroughly on preview (`auth-testing` branch)
- [ ] Admin can login successfully on preview
- [ ] Staff role redirects to Command Center correctly
- [ ] Viewer role has disabled buttons  
- [ ] Password reset feature works
- [ ] Zero-amount checkout works

---

## 🎯 **Deployment Steps:**

### **Phase 1: Prepare Production Environment** (10 minutes)

#### **Step 1: Merge Code to Main Branch**

**Option A - Via GitHub Web:**
1. Go to your GitHub repository
2. Click "Pull Requests" → "New Pull Request"
3. Base: `main` ← Compare: `auth-testing`
4. Title: "Add JWT Authentication System with RBAC"
5. Review changes → Click "Create Pull Request"
6. Click "Merge Pull Request" → "Confirm Merge"

**Option B - Via Command Line:**
```bash
git checkout main
git pull origin main
git merge auth-testing
git push origin main
```

#### **Step 2: Update Production Render Backend**

1. **Go to Render Dashboard**: [https://dashboard.render.com](https://dashboard.render.com)
2. **Select your PRODUCTION backend service** (not the test one)
3. Click **"Environment"** tab
4. **Add these NEW environment variables**:

```bash
JWT_SECRET_KEY=<generate-using-command-below>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
```

**Generate JWT_SECRET_KEY:**
```bash
# Run on your local terminal:
openssl rand -hex 32

# Copy the output (e.g., a3f2b1c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1)
# Paste as JWT_SECRET_KEY value in Render
```

5. **Verify CORS_ORIGINS** includes your production Vercel URL:
```bash
CORS_ORIGINS=https://your-production-app.vercel.app
```

6. Click **"Save Changes"**
7. Render will auto-redeploy backend (~5-7 minutes)
8. **Wait for "Live" status** before proceeding

---

#### **Step 3: Update Production Vercel Frontend**

**No changes needed!** Vercel will auto-deploy from `main` branch when you merged.

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Click **"Deployments"** tab
4. Wait for latest `main` branch deployment to show **"Ready"** status (~2-3 minutes)

---

### **Phase 2: Create Production Admin User** (5 minutes)

You have **3 options**:

#### **Option A: MongoDB Atlas Direct Insert** (EASIEST - Recommended)

1. **Generate Password Hash** (on your local terminal):
```bash
python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(pwd_context.hash('Admin@2026!'))"
```

Copy the output hash (e.g., `$2b$12$abc123...`)

2. **Insert Admin in MongoDB Atlas:**
   - Go to [MongoDB Atlas](https://cloud.mongodb.com) → Browse Collections
   - Select your cluster → Database: **`sarai`** (your production DB)
   - Collection: **`users`** (create if doesn't exist)
   - Click **"Insert Document"** → Switch to **JSON view**
   - Paste this (replace `password_hash` with YOUR generated hash):

```json
{
  "id": "admin-prod-001",
  "username": "admin",
  "email": "admin@sarai.local",
  "password_hash": "$2b$12$PASTE_YOUR_HASH_HERE",
  "name": "System Administrator",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-04-13T00:00:00.000000+00:00",
  "last_login": null
}
```

3. Click **"Insert"**

---

#### **Option B: Use Production Render Shell** (If enabled)

1. Render Dashboard → Your production service → **"Shell"** tab
2. Run:
```bash
cd /opt/render/project/src/backend
python scripts/create_admin.py
```

---

#### **Option C: Temporary API Endpoint** (If needed)

If you need the seed endpoint again, let me know and I'll re-add it temporarily.

---

### **Phase 3: Test Production Deployment** (10 minutes)

#### **Test 1: Login Page Shows**

1. Visit your production URL: `https://your-app.vercel.app`
2. ✅ **Should see Login page** (not setup wizard)
3. ✅ Username and Password fields visible
4. ✅ Eye icon to show/hide password works

#### **Test 2: Admin Login**

1. Login with:
   - Username: `admin` (or `admin@sarai.local`)
   - Password: `Admin@2026!`
2. ✅ **Should redirect to Dashboard**
3. ✅ **Top-right shows user name and logout button**
4. ✅ **All menu items visible** (Admin has full access)

#### **Test 3: Create Staff User**

1. Go to **User Management** page
2. Click **"Create User"**
3. Fill form:
   - Username: `staff_test`
   - Email: `staff@sarai.local`
   - Name: `Test Staff`
   - Role: **Staff**
   - Password: `Staff@123`
4. Click **Create**
5. ✅ **User created successfully**

#### **Test 4: Test Staff Login**

1. **Logout** (top-right button)
2. Login as Staff:
   - Username: `staff_test`
   - Password: `Staff@123`
3. ✅ **Should redirect to Command Center** (Splash Screen)
4. ✅ **User Management menu hidden**
5. ✅ **Settings menu hidden**
6. ✅ **Can access Backup & Restore**

#### **Test 5: Create Viewer User**

1. Logout → Login as admin
2. User Management → Create User:
   - Username: `viewer_test`
   - Role: **Viewer**
   - Password: `Viewer@123`

#### **Test 6: Test Viewer Permissions**

1. Logout → Login as Viewer
2. ✅ **Redirects to Dashboard**
3. ✅ **New Booking button DISABLED** (grayed out)
4. ✅ **Check In button DISABLED**
5. ✅ **Check Out button DISABLED**
6. ✅ **Cancel button DISABLED**
7. ✅ **Can view all data (read-only)**

#### **Test 7: Existing App Features**

Login as Admin and test:
- ✅ Create a new booking
- ✅ Check in a guest
- ✅ Check out a guest (test zero-amount flow)
- ✅ Generate PDFs
- ✅ View reports
- ✅ Backup & restore

---

### **Phase 4: Post-Deployment** (5 minutes)

#### **1. Update Test Credentials Document**

Update `/app/memory/test_credentials.md` with production credentials (for your reference).

#### **2. Change Default Password**

**IMPORTANT Security:**
1. Login as admin
2. Go to User Management
3. Click **"Reset"** on your admin account
4. Generate a strong unique password
5. **Save it securely** (password manager)

#### **3. Delete Test Users**

1. Delete `staff_test` and `viewer_test` if created for testing
2. Create real staff/viewer accounts with proper credentials

#### **4. Inform Your Team**

Send this message to users:

> **SARAI Update: User Authentication Now Required**
> 
> We've added secure login to protect your data. 
> 
> **What you need:**
> - Username and password (contact admin if you don't have one)
> - Your role determines access: Admin, Staff, or Viewer
> 
> **Login at**: https://your-app.vercel.app
> 
> Contact [admin name] if you need help logging in.

---

## 🐛 **Troubleshooting:**

### Issue: "Login page not showing - Setup wizard appears"

**Solution:**
- Hard refresh: `Ctrl + Shift + R`
- Clear browser cache
- Try incognito/private window
- Check Vercel deployment completed successfully

### Issue: "Invalid username or password" for admin

**Solutions:**
1. Check username is exactly: `admin` (lowercase)
2. Check password is exactly: `Admin@2026!`
3. Verify admin user exists in MongoDB Atlas `sarai.users` collection
4. Verify `password_hash` field is not empty

### Issue: "500 Internal Server Error" on login

**Check Render Logs:**
1. Render Dashboard → Your service → **Logs** tab
2. Look for errors related to:
   - `JWT_SECRET_KEY` missing
   - bcrypt errors
   - MongoDB connection issues

**Solution:**
- Verify all JWT environment variables are set
- Check Python version is 3.11.9 (via `runtime.txt`)
- Verify bcrypt version is 4.1.2

### Issue: "CORS error" when logging in

**Solution:**
- Verify `CORS_ORIGINS` in Render exactly matches your Vercel production URL
- No trailing slash
- Use `https://` not `http://`

### Issue: Staff/Viewer can see restricted features

**Solution:**
- Hard refresh browser
- Check user's `role` field in MongoDB is correctly set (`admin`, `staff`, or `viewer`)
- Logout and login again to refresh token

---

## 🔒 **Security Best Practices:**

1. ✅ **Change default admin password** immediately
2. ✅ **Use strong passwords** (min 12 characters, mix of letters, numbers, symbols)
3. ✅ **Create individual accounts** for each team member (don't share passwords)
4. ✅ **Review user access** monthly - disable inactive users
5. ✅ **Keep JWT_SECRET_KEY private** - never share or commit to git
6. ✅ **Enable 2FA on MongoDB Atlas** for database access
7. ✅ **Regular backups** - Your existing backup system covers this

---

## ✅ **Deployment Complete!**

Your SARAI application now has:
- ✅ Secure JWT authentication
- ✅ Role-based access control (Admin/Staff/Viewer)
- ✅ Password management for admins
- ✅ Protected API endpoints
- ✅ Role-specific landing pages
- ✅ Disabled buttons for read-only viewers

---

## 📞 **Need Help?**

If you encounter issues during deployment:
1. Check the troubleshooting section above
2. Review Render and Vercel logs
3. Verify all environment variables are set correctly
4. Test in preview environment first to isolate production-specific issues

---

**Congratulations on your secure deployment! 🎉**
