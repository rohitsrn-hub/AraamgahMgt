# 🔐 Environment Variables Quick Reference

Complete guide to all environment variables needed for E-ARMS deployment.

---

## 📁 File Locations

| Deployment Type | Backend Env File | Frontend Env File |
|----------------|------------------|-------------------|
| **Local** | `/backend/.env` | `/frontend/.env.local` |
| **Cloud (Render)** | Render Dashboard > Environment | N/A |
| **Cloud (Vercel)** | N/A | Vercel Dashboard > Environment Variables |

---

## 🖥️ Backend Environment Variables

### Required Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `MONGO_URL` | MongoDB connection string | `mongodb://localhost:27017` (local)<br>`mongodb+srv://user:pass@cluster.mongodb.net/` (cloud) |
| `DB_NAME` | Database name | `earms_db` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated) | `*` | `https://earms.vercel.app,http://localhost:3000` |

---

## 🌐 Frontend Environment Variables

### Required Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `REACT_APP_BACKEND_URL` | Backend API URL (NO trailing slash) | `http://localhost:8001` (local)<br>`https://earms-backend.onrender.com` (cloud) |

---

## 📋 Complete Setup Examples

### Local Deployment

#### Backend: `/backend/.env`
```bash
MONGO_URL=mongodb://localhost:27017
DB_NAME=earms_db
```

#### Frontend: `/frontend/.env.local`
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

**For network access (mobile/tablet on same Wi-Fi):**
```bash
# Replace with your computer's local IP
REACT_APP_BACKEND_URL=http://192.168.1.105:8001
```

---

### Cloud Deployment

#### Backend: Render Dashboard > Environment

```bash
MONGO_URL=mongodb+srv://earms_admin:SecurePass123@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
DB_NAME=earms_db
CORS_ORIGINS=https://earms-frontend.vercel.app
```

**How to add in Render:**
1. Dashboard > Your Service (earms-backend)
2. Environment > Add Environment Variable
3. Add each variable separately
4. Click "Save Changes"

#### Frontend: Vercel Dashboard > Environment Variables

```bash
REACT_APP_BACKEND_URL=https://earms-backend.onrender.com
```

**How to add in Vercel:**
1. Dashboard > Your Project (earms-frontend)
2. Settings > Environment Variables
3. Add variable
4. Environment: Production, Preview, Development (select all)
5. Click "Save"

---

## 🔍 How to Find Values

### MongoDB URL (Local)

**Windows:**
```
mongodb://localhost:27017
```

**Mac/Linux:**
```
mongodb://localhost:27017
```

**Check if MongoDB is running:**
```bash
# Windows
net start | findstr MongoDB

# Mac
brew services list | grep mongodb

# Linux
sudo systemctl status mongod
```

---

### MongoDB URL (Atlas - Cloud)

1. **Login to MongoDB Atlas:** https://cloud.mongodb.com/
2. **Navigate to:** Database > Clusters
3. **Click:** Connect button on your cluster
4. **Select:** Connect your application
5. **Copy connection string:**
   ```
   mongodb+srv://username:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
6. **Replace `<password>`** with your actual database user password

**Important:** 
- Don't include `<` and `>` symbols
- If password has special characters, URL-encode them

---

### Local IP Address (For Network Access)

**Windows:**
```bash
ipconfig
# Look for: IPv4 Address under your active network adapter
# Example: 192.168.1.105
```

**Mac:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# Example: 192.168.1.105
```

**Linux:**
```bash
hostname -I
# Example: 192.168.1.105
```

---

### Backend URL (Cloud)

After deploying to Render:
- **Format:** `https://YOUR-SERVICE-NAME.onrender.com`
- **Example:** `https://earms-backend.onrender.com`

**Find it in Render:**
1. Dashboard > Your Service
2. Copy URL shown at top (under service name)

---

## ⚠️ Common Mistakes

### ❌ WRONG: Trailing Slash
```bash
REACT_APP_BACKEND_URL=http://localhost:8001/  # ❌ Don't add trailing slash
```

### ✅ CORRECT: No Trailing Slash
```bash
REACT_APP_BACKEND_URL=http://localhost:8001  # ✅ Correct
```

---

### ❌ WRONG: Using `localhost` in Cloud
```bash
# In Vercel (frontend cloud deployment)
REACT_APP_BACKEND_URL=http://localhost:8001  # ❌ Won't work in cloud
```

### ✅ CORRECT: Using Actual Domain
```bash
# In Vercel (frontend cloud deployment)
REACT_APP_BACKEND_URL=https://earms-backend.onrender.com  # ✅ Correct
```

---

### ❌ WRONG: Using HTTP for Cloud
```bash
REACT_APP_BACKEND_URL=http://earms-backend.onrender.com  # ❌ Cloud uses HTTPS
```

### ✅ CORRECT: Using HTTPS for Cloud
```bash
REACT_APP_BACKEND_URL=https://earms-backend.onrender.com  # ✅ Correct
```

---

### ❌ WRONG: Password with Special Characters Not Encoded
```bash
# If password is: P@ssw0rd!123
MONGO_URL=mongodb+srv://user:P@ssw0rd!123@cluster.mongodb.net/  # ❌ Will fail
```

### ✅ CORRECT: URL-Encoded Password
```bash
# Encoded: P%40ssw0rd%21123
MONGO_URL=mongodb+srv://user:P%40ssw0rd%21123@cluster.mongodb.net/  # ✅ Correct
```

**URL Encoding Chart:**
- `@` → `%40`
- `!` → `%21`
- `#` → `%23`
- `$` → `%24`
- `%` → `%25`
- `&` → `%26`

**Tip:** Use this tool: https://www.urlencoder.org/

---

## 🧪 Testing Environment Variables

### Test Backend Connection

**Local:**
```bash
# In backend folder
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('MONGO_URL:', os.environ.get('MONGO_URL')); print('DB_NAME:', os.environ.get('DB_NAME'))"
```

**Cloud (Render):**
- Dashboard > Your Service > Logs
- Look for startup logs showing environment variables loaded

---

### Test Frontend Configuration

**Local:**
```bash
# In frontend folder
yarn start
# Check browser console for: process.env.REACT_APP_BACKEND_URL
```

**Cloud (Vercel):**
- Open deployed site
- F12 > Console
- Type: `process.env.REACT_APP_BACKEND_URL`
- Should show your backend URL

---

## 🔄 Updating Environment Variables

### Local Deployment

1. Edit `.env` or `.env.local` files
2. **Restart servers** (changes don't apply until restart)
   ```bash
   # Stop servers (Ctrl+C)
   # Restart:
   # Backend: python server.py
   # Frontend: yarn start
   ```

---

### Cloud Deployment

#### Render (Backend)
1. Dashboard > Your Service > Environment
2. Edit variable value
3. Click "Save Changes"
4. **Service auto-redeploys** (takes 2-3 minutes)

#### Vercel (Frontend)
1. Dashboard > Project > Settings > Environment Variables
2. Edit variable value
3. Click "Save"
4. **Redeploy required:**
   - Go to Deployments tab
   - Click ⋯ menu on latest deployment
   - Click "Redeploy"

---

## 📝 Environment Variables Checklist

### Before Starting Local Deployment
- [ ] Created `/backend/.env` file
- [ ] Added `MONGO_URL=mongodb://localhost:27017`
- [ ] Added `DB_NAME=earms_db`
- [ ] Created `/frontend/.env.local` file
- [ ] Added `REACT_APP_BACKEND_URL` with correct IP
- [ ] MongoDB service is running

### Before Starting Cloud Deployment
- [ ] MongoDB Atlas cluster created
- [ ] Database user created with password saved
- [ ] Connection string copied and password replaced
- [ ] Render backend deployed
- [ ] Added `MONGO_URL` to Render
- [ ] Added `DB_NAME` to Render
- [ ] Backend URL saved from Render
- [ ] Vercel frontend deployed
- [ ] Added `REACT_APP_BACKEND_URL` to Vercel with Render URL

---

## 🆘 Troubleshooting

### Backend can't connect to database

**Error:** `MongoServerError: Authentication failed`

**Solutions:**
1. Check MongoDB Atlas > Security > Database Access
2. Verify username and password are correct
3. Check password is URL-encoded in connection string
4. Verify Network Access allows `0.0.0.0/0`

---

### Frontend can't reach backend

**Error:** `Network Error` or `Failed to fetch` in browser console

**Solutions:**
1. Verify `REACT_APP_BACKEND_URL` is set correctly
2. Check backend is running (visit `/api/health`)
3. For cloud: ensure `CORS_ORIGINS` includes frontend URL
4. Check for typos (http vs https, trailing slash)

---

### Environment variables not loaded

**Local:**
- Ensure `.env` files are in correct directories
- File must be named exactly `.env` or `.env.local`
- Restart servers after changes

**Cloud:**
- Verify variables are set in dashboard
- Redeploy service after adding variables
- Check deployment logs for errors

---

## 📞 Support

If environment variables still don't work:

1. **Check logs:**
   - Local: Terminal output
   - Render: Dashboard > Logs
   - Vercel: Deployments > View Function Logs

2. **Verify file/variable names:**
   - Must be exact (case-sensitive)
   - No spaces in variable names
   - No quotes around values (in dashboard)

3. **Test with simple values:**
   - Try hardcoding values temporarily to isolate issue

---

**Complete deployment guides:**
- Local: `LOCAL_DEPLOYMENT.md`
- Cloud: `CLOUD_DEPLOYMENT.md`
