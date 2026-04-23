# 🔧 Render Deployment Troubleshooting

Quick fixes for common Render deployment issues.

---

## ❌ Error: "No matching distribution found for emergentintegrations"

### Problem
```
ERROR: Could not find a version that satisfies the requirement emergentintegrations==0.1.0
ERROR: No matching distribution found for emergentintegrations==0.1.0
```

### Solution
The `emergentintegrations` package is specific to Emergent platform and not available on public PyPI.

**Fixed in latest version!** The `requirements.txt` has been updated to remove this package.

If you still see this error:

1. **Pull latest changes:**
   ```bash
   git pull origin main
   ```

2. **Or manually edit `backend/requirements.txt`:**
   - Remove line: `emergentintegrations==0.1.0`
   - Remove other unused packages (boto3, jq, typer, pytest, black, etc.)

3. **Commit and push:**
   ```bash
   git add backend/requirements.txt
   git commit -m "Remove emergentintegrations for cloud deployment"
   git push origin main
   ```

4. **Redeploy on Render:**
   - Render will auto-deploy, or
   - Dashboard → Your Service → Manual Deploy

---

## ❌ Error: "Python version 3.14.3" (Too New)

### Problem
Render is using Python 3.14.3 which may have compatibility issues.

### Solution
Specify Python version in Render dashboard:

1. **Dashboard → Your Service → Environment**
2. **Add/Update Environment Variable:**
   - Key: `PYTHON_VERSION`
   - Value: `3.11.0`
3. **Save and redeploy**

Or use `render.yaml` (already configured in this repo).

---

## ❌ Error: "Root directory not found"

### Problem
```
ERROR: Could not find backend/requirements.txt
```

### Solution
Check Root Directory setting in Render:

1. **Dashboard → Your Service → Settings**
2. **Root Directory:** Should be empty or `.` (not `backend`)
3. **Build Command:** Should be `cd backend && pip install -r requirements.txt`
4. **Start Command:** Should be `cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT`

---

## ❌ Error: "MongoDB connection failed"

### Problem
```
pymongo.errors.ServerSelectionTimeoutError: connection refused
```

### Solution

1. **Check MongoDB Atlas Network Access:**
   - Atlas Dashboard → Security → Network Access
   - Ensure `0.0.0.0/0` is whitelisted (allows all IPs)

2. **Verify MONGO_URL in Render:**
   - Dashboard → Your Service → Environment
   - Check `MONGO_URL` is correct
   - Format: `mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority`
   - **Important:** Password must be URL-encoded if it has special characters

3. **Test connection string locally:**
   ```bash
   mongosh "mongodb+srv://username:password@cluster.mongodb.net/"
   ```

---

## ❌ Error: "Service Unavailable" (503)

### Problem
Backend deployed but health check fails.

### Solution

1. **Check Render logs:**
   - Dashboard → Your Service → Logs
   - Look for startup errors

2. **Verify environment variables:**
   - `MONGO_URL` - MongoDB Atlas connection string
   - `DB_NAME` - `earms_db`

3. **Test health endpoint:**
   - Open: `https://your-service.onrender.com/api/health`
   - Should return: `{"status":"healthy",...}`

---

## ❌ Error: "Build failed" (generic)

### Solution

1. **Check build logs** in Render dashboard

2. **Common fixes:**
   - Ensure `requirements.txt` has no platform-specific packages
   - Remove `emergentintegrations`
   - Use compatible Python version (3.9-3.11)

3. **Minimal requirements.txt for cloud:**
   ```txt
   fastapi==0.110.1
   uvicorn==0.25.0
   pymongo==4.5.0
   motor==3.3.1
   pydantic>=2.6.4
   python-dotenv>=1.0.1
   python-multipart>=0.0.9
   ```

---

## ✅ Correct Render Configuration

### Service Settings

| Setting | Value |
|---------|-------|
| **Name** | `earms-backend` |
| **Region** | Singapore / Oregon |
| **Branch** | `main` or `AramgahOnline` |
| **Root Directory** | (empty) or `.` |
| **Runtime** | Python 3 |
| **Build Command** | `cd backend && pip install -r requirements.txt` |
| **Start Command** | `cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free |

### Environment Variables

| Key | Example Value |
|-----|---------------|
| `MONGO_URL` | `mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority` |
| `DB_NAME` | `earms_db` |
| `PYTHON_VERSION` | `3.11.0` |
| `CORS_ORIGINS` | `*` (or your Vercel URL) |

---

## 🔄 Redeploying After Fixes

### Auto-Deploy (Recommended)
```bash
# Make your fixes
git add .
git commit -m "Fix deployment issues"
git push origin main

# Render auto-deploys in 2-3 minutes
```

### Manual Deploy
1. Render Dashboard → Your Service
2. Click "Manual Deploy" button
3. Select branch: `main`
4. Deploy

---

## 📊 Deployment Checklist

Before deploying, verify:

- [ ] `backend/requirements.txt` does NOT contain `emergentintegrations`
- [ ] `MONGO_URL` is set in Render environment variables
- [ ] `DB_NAME` is set to `earms_db`
- [ ] MongoDB Atlas Network Access allows `0.0.0.0/0`
- [ ] Root Directory is empty or `.`
- [ ] Build Command includes `cd backend &&`
- [ ] Start Command includes `cd backend &&`
- [ ] Branch matches your Git branch name

---

## 🆘 Still Having Issues?

1. **Check official Render docs:**
   - https://render.com/docs/deploy-fastapi
   - https://render.com/docs/troubleshooting-deploys

2. **View full build logs:**
   - Dashboard → Your Service → Logs
   - Copy error message and search for solutions

3. **Test locally first:**
   ```bash
   cd backend
   pip install -r requirements.txt
   MONGO_URL="your-atlas-url" DB_NAME="earms_db" python -m uvicorn server:app
   ```
   - If local works, issue is Render-specific
   - If local fails, fix code first

---

## 📝 Quick Fix Script

Run this to prepare your repo for Render deployment:

```bash
#!/bin/bash

# Navigate to backend
cd backend

# Create minimal requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.110.1
uvicorn==0.25.0
pymongo==4.5.0
motor==3.3.1
pydantic>=2.6.4
python-dotenv>=1.0.1
python-multipart>=0.0.9
EOF

# Commit changes
cd ..
git add backend/requirements.txt
git commit -m "Fix requirements.txt for Render deployment"
git push origin main

echo "✅ Fixed! Render will auto-redeploy in 2-3 minutes."
```

---

**Last Updated:** April 2026  
**Status:** Issue resolved in latest commit
