# 🔐 Enable Authentication on Your Deployed SARAI App

Quick guide to add authentication to your already-deployed application.

---

## Step 1: Add Environment Variables to Render (Backend)

1. Go to your Render dashboard: [https://dashboard.render.com](https://dashboard.render.com)
2. Open your SARAI backend service
3. Go to **Environment** tab
4. Add these NEW environment variables:

### Required Variables:

```bash
# JWT Authentication
JWT_SECRET_KEY=PASTE_OUTPUT_FROM_COMMAND_BELOW
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
```

### Generate JWT Secret Key:
**Run this on your local terminal:**
```bash
openssl rand -hex 32
```
Copy the output (a long random string like `a3f2b1c9d8e7f6...`) and paste it as the `JWT_SECRET_KEY` value.

### Existing Variables (Keep as-is):
- `MONGO_URL` - Already configured
- `DB_NAME` - Already configured
- `CORS_ORIGINS` - Already configured

4. Click **Save Changes**
5. Render will automatically redeploy your backend (takes 2-3 minutes)

---

## Step 2: Push Code to GitHub

Your authentication code is ready. Just push it to deploy:

```bash
# From your local machine (Emergent workspace)
git add .
git commit -m "Add user authentication system"
git push origin main
```

**Both Vercel (frontend) and Render (backend) will auto-deploy from GitHub.**

Wait 3-5 minutes for deployments to complete.

---

## Step 3: Create First Admin User

After backend deployment completes:

### Option A: Via Render Shell (Recommended)
1. Go to Render dashboard → Your backend service
2. Click **Shell** tab (top right)
3. Run this command:
   ```bash
   cd /opt/render/project/src
   python scripts/create_admin.py
   ```
4. You'll see:
   ```
   ✅ Admin user created!
   Username: admin
   Password: Admin@2026!
   ```

### Option B: Via MongoDB Atlas (Alternative)
If Shell doesn't work, manually insert admin user:

1. Go to MongoDB Atlas → Browse Collections
2. Select your database → `users` collection
3. Click **Insert Document**
4. Paste this (replace `YOUR_DB_NAME`):

```json
{
  "id": "admin-001",
  "email": "admin",
  "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqNPKKqm6e",
  "name": "System Administrator",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-04-12T00:00:00.000000+00:00",
  "last_login": null
}
```

**Note:** This creates admin user with password `Admin@2026!`

5. Click **Insert**

---

## Step 4: Test Authentication

1. **Visit your Vercel frontend URL**
   - Example: `https://your-app.vercel.app`

2. **You should be redirected to `/login`**
   - If not, manually go to: `https://your-app.vercel.app/login`

3. **Login with:**
   - Username: `admin`
   - Password: `Admin@2026!`

4. **You should be redirected to dashboard**
   - Check top-right corner for user name and logout button

5. **Test User Management** (Admin only)
   - Go to sidebar → Click "User Management"
   - Create a staff user
   - Logout and login as staff user
   - Verify staff can't see "User Management" menu

---

## Step 5: Change Admin Password

⚠️ **IMPORTANT: Do this immediately!**

1. Login as admin
2. Go to **User Management**
3. Find admin user in the list
4. Click **Edit** or use the update API

**OR** manually in MongoDB Atlas:
1. Browse Collections → `users`
2. Find admin user
3. Generate new password hash locally:
   ```bash
   python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(pwd_context.hash('YourNewPassword123!'))"
   ```
4. Replace `password_hash` field with the output

---

## Troubleshooting

### Issue: Login page not showing
**Solution:**
- Clear browser cache (Ctrl + Shift + R)
- Check Vercel deployment logs
- Verify frontend deployed successfully

### Issue: "Invalid username or password" on login
**Solutions:**
1. Check admin user was created (MongoDB Atlas → Browse Collections → `users`)
2. Verify username is exactly: `admin` (case-sensitive)
3. Verify password is exactly: `Admin@2026!`
4. Check Render logs for errors

### Issue: CORS error in browser console
**Solution:**
- Render → Environment → Check `CORS_ORIGINS` matches your Vercel URL exactly
- No trailing slash
- Use `https://` not `http://`
- Example: `CORS_ORIGINS=https://your-app.vercel.app`

### Issue: 500 Error on login
**Solutions:**
1. Check Render logs: Dashboard → Logs tab
2. Verify `JWT_SECRET_KEY` is set
3. Verify `MONGO_URL` is correct
4. Restart backend: Manual Deploy → Deploy latest commit

### Issue: Backend not restarting after env variable change
**Solution:**
- Render → Manual Deploy → "Clear build cache & deploy"

---

## Quick Verification Checklist

- [ ] JWT environment variables added to Render
- [ ] Render backend redeployed successfully
- [ ] Code pushed to GitHub
- [ ] Vercel frontend redeployed successfully
- [ ] Admin user created in database
- [ ] Login page loads at `/login`
- [ ] Can login with admin credentials
- [ ] Dashboard loads after login
- [ ] User info shows in top-right
- [ ] Logout button works
- [ ] User Management page accessible (admin only)

---

## Environment Variables Summary

### Render (Backend) - Add These:
```bash
JWT_SECRET_KEY=<generated-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
```

### Vercel (Frontend) - No Changes Needed:
Your existing `REACT_APP_BACKEND_URL` is already correct.

---

## What Happens After Enabling Auth?

1. **All users must login** to access the app
2. **Unauthenticated users** → Redirected to `/login`
3. **Admin users** can:
   - Access all features
   - Manage users (create/edit/delete)
   - Access Settings & Backup
4. **Staff users** can:
   - Access bookings, rooms, reports
   - Access Backup & Restore
   - Cannot access User Management or Settings
5. **Viewer users** can:
   - Read-only access
   - Cannot modify data

---

## Need Help?

**Check Logs:**
- Backend logs: Render Dashboard → Logs tab
- Frontend logs: Vercel Dashboard → Deployments → Function Logs
- Browser console: F12 → Console tab

**Common Issues:**
- 90% of issues = Missing/incorrect environment variables
- 5% = Admin user not created
- 5% = CORS mismatch

---

## Summary - 3 Simple Steps:

1. **Add JWT variables to Render** (JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES)
2. **Push code to GitHub** (triggers auto-deploy on Vercel & Render)
3. **Create admin user via Render Shell** (or MongoDB Atlas)

**Then login at your Vercel URL with: `admin` / `Admin@2026!`**

🎉 **Authentication enabled!**
