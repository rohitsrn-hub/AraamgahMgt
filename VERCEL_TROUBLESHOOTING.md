# 🔧 Vercel Deployment Troubleshooting

Quick fixes for common Vercel frontend deployment issues.

---

## ❌ Error: "ERESOLVE unable to resolve dependency tree"

### Problem
```
npm error ERESOLVE unable to resolve dependency tree
npm error Could not resolve dependency:
npm error peer date-fns@"^2.28.0 || ^3.0.0" from react-day-picker@8.10.1
npm error Found: date-fns@4.1.0
```

### Solution
**Fixed in latest version!** The `package.json` has been updated.

#### What was changed:
- `date-fns`: `^4.1.0` → `^3.6.0` (compatible with react-day-picker)
- Added `.npmrc` to configure package manager
- Updated `vercel.json` to use yarn instead of npm

#### If you still see this error:

**Option 1: Pull latest changes (Recommended)**
```bash
git pull origin main
git push origin AramgahOnline  # or your branch
```

**Option 2: Manual fix**
1. Edit `frontend/package.json`:
   ```json
   "date-fns": "^3.6.0"  // Change from 4.1.0 to 3.6.0
   ```

2. Commit and push:
   ```bash
   git add frontend/package.json
   git commit -m "Fix date-fns version for Vercel compatibility"
   git push origin main
   ```

---

## ❌ Error: Vercel Using npm Instead of Yarn

### Problem
Vercel uses `npm install` but your project uses Yarn (has `yarn.lock` file).

### Solution

**Method 1: Configure in Vercel Dashboard (Recommended)**

1. **Vercel Dashboard** → Your Project → **Settings**
2. **General** → Scroll to **Build & Development Settings**
3. **Install Command:** Override with `yarn install`
4. **Build Command:** Keep as `yarn build`
5. **Output Directory:** `build`
6. Click **Save**

**Method 2: Use vercel.json (Already configured)**

The `vercel.json` file in the root is configured to use yarn:
```json
{
  "buildCommand": "cd frontend && yarn install && yarn build",
  "outputDirectory": "frontend/build"
}
```

---

## ❌ Error: "Root Directory" Configuration

### Problem
Vercel can't find the frontend code because it's in a subfolder.

### Solution

**In Vercel Dashboard:**

1. **Project Settings** → **General**
2. **Root Directory:** Set to `frontend`
3. **Framework Preset:** Create React App (auto-detect)
4. **Build Command:** `yarn build`
5. **Output Directory:** `build`
6. **Install Command:** `yarn install`
7. **Save**

---

## ✅ Correct Vercel Configuration

### Option A: Root Directory = `frontend` (Recommended)

| Setting | Value |
|---------|-------|
| **Root Directory** | `frontend` |
| **Framework Preset** | Create React App |
| **Build Command** | `yarn build` |
| **Output Directory** | `build` |
| **Install Command** | `yarn install` |

**Environment Variables:**
- `REACT_APP_BACKEND_URL` = `https://your-backend.onrender.com`

---

### Option B: Root Directory = `.` (Root)

| Setting | Value |
|---------|-------|
| **Root Directory** | `.` (or leave empty) |
| **Framework Preset** | Other |
| **Build Command** | `cd frontend && yarn install && yarn build` |
| **Output Directory** | `frontend/build` |
| **Install Command** | `echo 'Skipping'` |

**Environment Variables:**
- `REACT_APP_BACKEND_URL` = `https://your-backend.onrender.com`

---

## 📋 Step-by-Step: Reconfigure Vercel Project

If your deployment is failing, reconfigure from scratch:

### Step 1: Delete Current Deployment (Optional)
1. Vercel Dashboard → Your Project
2. Settings → Advanced → Delete Project
3. Confirm

### Step 2: Reimport Project

1. **Vercel Dashboard** → **Add New** → **Project**
2. **Import** your GitHub repository
3. **Configure Project:**

   **Project Name:** `earms-frontend`

   **Framework Preset:** Create React App

   **Root Directory:** Click **Edit** → Select `frontend` folder

   **Build and Output Settings:**
   - Build Command: `yarn build` (auto-detected)
   - Output Directory: `build` (auto-detected)
   - Install Command: `yarn install` (auto-detected)

4. **Environment Variables:**
   - Click "Add"
   - Name: `REACT_APP_BACKEND_URL`
   - Value: `https://your-backend.onrender.com` (your Render URL)
   - Environment: Production, Preview, Development (all)

5. **Deploy**

---

## 🔄 Force Redeploy After Fix

After fixing package.json or configuration:

**Method 1: Git Push (Recommended)**
```bash
git add .
git commit -m "Fix Vercel deployment dependencies"
git push origin AramgahOnline
```
Vercel auto-deploys in ~2 minutes.

**Method 2: Manual Redeploy**
1. Vercel Dashboard → Deployments
2. Click ⋯ menu on latest deployment
3. Click "Redeploy"
4. Check "Use existing Build Cache" → Uncheck (force fresh build)
5. Redeploy

---

## 🧪 Test Dependency Fix Locally

Before pushing, test the fix works:

```bash
cd frontend

# Remove node_modules and lockfile
rm -rf node_modules yarn.lock

# Reinstall with fixed dependencies
yarn install

# Test build
yarn build

# If build succeeds, push to GitHub
cd ..
git add frontend/package.json frontend/yarn.lock
git commit -m "Fix date-fns version for compatibility"
git push origin main
```

---

## ❌ Error: "Module not found" After Deployment

### Problem
Build succeeds but app shows blank page with console error:
```
Module not found: Error: Can't resolve 'date-fns'
```

### Solution
1. Clear Vercel build cache
2. Redeploy with fresh build
3. Check `REACT_APP_BACKEND_URL` is set correctly

**Steps:**
1. Vercel Dashboard → Settings → General
2. Scroll to **Build & Development Settings**
3. Click **Clear Build Cache and Redeploy**

---

## 🔍 Debugging Vercel Build

### View Full Build Logs

1. Vercel Dashboard → Deployments
2. Click on the failed deployment
3. Click "Building" or "Build Logs" tab
4. Look for the exact error

### Common Errors:

**1. Wrong Node Version**
- Error: `Error: The engine "node" is incompatible`
- Fix: Add to `package.json`:
  ```json
  "engines": {
    "node": "18.x"
  }
  ```

**2. Environment Variable Missing**
- Error: `process.env.REACT_APP_BACKEND_URL is undefined`
- Fix: Add in Vercel Dashboard → Environment Variables

**3. Import Path Issues**
- Error: `Module not found: Can't resolve '@/components/...'`
- Fix: Check `jsconfig.json` paths are correct

---

## ✅ Verification After Successful Deploy

1. **Check deployment URL:**
   - `https://earms-frontend.vercel.app` or
   - `https://earms-frontend-xyz.vercel.app`

2. **Test Command Center page loads:**
   - Should see tactical military theme
   - 5 action buttons (New Booking, Check In, etc.)

3. **Check browser console (F12):**
   - No errors
   - `REACT_APP_BACKEND_URL` should be your Render URL

4. **Test API connection:**
   - Click "Settings" or "Dashboard"
   - Should load without CORS errors

5. **Test backend connection:**
   - Open browser DevTools → Network tab
   - Navigate to Dashboard
   - Should see API calls to your Render backend
   - Status: 200 (success)

---

## 🆘 Still Having Issues?

### Check These:

1. **Package.json dependencies:**
   ```json
   "date-fns": "^3.6.0",  // NOT 4.1.0
   "react-day-picker": "8.10.1"
   ```

2. **Vercel configuration:**
   - Root Directory: `frontend`
   - Build Command: `yarn build`
   - Install Command: `yarn install`

3. **Environment Variables:**
   - `REACT_APP_BACKEND_URL` is set
   - Value is `https://` not `http://`
   - No trailing slash

4. **GitHub branch:**
   - Deploying from correct branch
   - Latest commit includes fixes

### Test Locally First:

```bash
cd frontend
yarn install
yarn build
yarn start

# Open http://localhost:3000
# If works locally, issue is Vercel-specific
```

---

## 📊 Expected Build Output

Successful Vercel deployment shows:

```
✓ Installing dependencies
✓ Running build command
✓ Compiled successfully
✓ Creating an optimized production build
✓ Build completed
✓ Uploading build outputs
✓ Deployment ready
```

**Build time:** 2-5 minutes
**Deployment URL:** `https://your-app.vercel.app`

---

## 📞 Additional Resources

- **Vercel Docs:** https://vercel.com/docs/frameworks/create-react-app
- **CRA Docs:** https://create-react-app.dev/docs/deployment#vercel
- **date-fns Migration:** https://date-fns.org/docs/Upgrade-Guide

---

## 🎯 Summary of Fixes

**Dependencies:**
- ✅ `date-fns`: 4.1.0 → 3.6.0 (compatibility fix)
- ✅ Added `frontend/.npmrc` for package manager config
- ✅ Updated `vercel.json` for yarn usage

**Vercel Configuration:**
- ✅ Root Directory: `frontend`
- ✅ Build Command: `yarn build`
- ✅ Install Command: `yarn install`
- ✅ Output Directory: `build`

**Next Steps:**
1. Pull/apply fixes
2. Push to GitHub
3. Vercel auto-deploys
4. Test at your Vercel URL

---

**Your deployment should now succeed! 🚀**
