# 🏠 E-ARMS Local Deployment Guide

Complete guide to deploy E-ARMS on your local computer for use without internet.

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Find Your Local IP Address](#find-your-local-ip-address)
4. [Configure Frontend](#configure-frontend)
5. [Start the Application](#start-the-application)
6. [Access from Other Devices](#access-from-other-devices)
7. [Optional: Internet Access via Tunneling](#optional-internet-access-via-tunneling)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

Ensure you have the following installed on your computer:

- ✅ **Node.js** (v16 or higher) - [Download](https://nodejs.org/)
- ✅ **Python** (v3.9 or higher) - [Download](https://www.python.org/)
- ✅ **MongoDB** (v4.4 or higher) - [Download](https://www.mongodb.com/try/download/community)
- ✅ **Yarn** package manager - Install via: `npm install -g yarn`

---

## 🚀 Initial Setup

### 1. MongoDB Setup

**Start MongoDB service:**

**Windows:**
```bash
# Start MongoDB as a service (run as Administrator)
net start MongoDB

# OR manually start:
"C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe" --dbpath "C:\data\db"
```

**Mac:**
```bash
brew services start mongodb-community
```

**Linux:**
```bash
sudo systemctl start mongod
sudo systemctl enable mongod  # Auto-start on boot
```

**Verify MongoDB is running:**
```bash
mongo --eval "db.version()"
# OR
mongosh --eval "db.version()"
```

### 2. Install Dependencies

```bash
# Backend dependencies
cd /path/to/AraamgahMgt/backend
pip install -r requirements.txt

# Frontend dependencies  
cd /path/to/AraamgahMgt/frontend
yarn install
```

---

## 🌐 Find Your Local IP Address

You need your computer's **local network IP address** to access from other devices.

### Windows
```bash
ipconfig
```
Look for **IPv4 Address** under your active network adapter (usually starts with `192.168.x.x` or `10.0.x.x`)

Example output:
```
Wireless LAN adapter Wi-Fi:
   IPv4 Address. . . . . . . . . . . : 192.168.1.105  ← THIS IS YOUR IP
```

### Mac / Linux
```bash
ifconfig
# OR
ip addr show
```
Look for **inet** address (e.g., `192.168.1.105`)

### Note Your IP
```
My Local IP: _____________________ (e.g., 192.168.1.105)
```

---

## ⚙️ Configure Frontend

### Create Local Environment File

```bash
cd frontend
cp .env.local.template .env.local
```

### Edit `.env.local`

Open `frontend/.env.local` and replace `YOUR_LOCAL_IP` with your actual IP:

```bash
# Before:
REACT_APP_BACKEND_URL=http://YOUR_LOCAL_IP:8001

# After (example with IP 192.168.1.105):
REACT_APP_BACKEND_URL=http://192.168.1.105:8001
```

**Important:** Use your **local network IP** (not localhost) if you want to access from other devices!

---

## 🎯 Start the Application

### Option 1: Using Supervisor (Recommended)

If supervisor is already configured:

```bash
sudo supervisorctl restart all
```

### Option 2: Manual Start (for local computer deployment)

**Terminal 1 - Start Backend:**
```bash
cd backend
python server.py
# Backend will run on http://0.0.0.0:8001
```

**Terminal 2 - Start Frontend (Development Mode):**
```bash
cd frontend
yarn start
# Frontend will open at http://localhost:3000
```

**Terminal 3 - Start Frontend (Production Mode - Better Performance):**
```bash
cd frontend

# Build for production
yarn build

# Serve the build
npx serve -s build -l 3000
```

---

## 📱 Access from Other Devices

Once the application is running:

### From the Same Computer:
```
http://localhost:3000
```

### From Other Devices on Same Network:
```
http://YOUR_LOCAL_IP:3000

Example: http://192.168.1.105:3000
```

### On Mobile Phone/Tablet:
1. Connect your phone to the **same Wi-Fi network** as your computer
2. Open browser and go to: `http://YOUR_LOCAL_IP:3000`
3. Bookmark it for easy access

**Example:** If your IP is `192.168.1.105`:
- Open mobile browser
- Go to: `http://192.168.1.105:3000`
- App should load and work perfectly!

---

## 🌍 Optional: Internet Access via Tunneling

If you want to access the app from outside your local network (requires internet):

### Using ngrok (Easiest)

1. **Install ngrok:** [Download](https://ngrok.com/download)

2. **Expose Backend:**
```bash
ngrok http 8001
```
You'll get a URL like: `https://abc123.ngrok.io`

3. **Update Frontend .env.local:**
```bash
REACT_APP_BACKEND_URL=https://abc123.ngrok.io
```

4. **Expose Frontend:**
```bash
ngrok http 3000
```
You'll get a URL like: `https://xyz789.ngrok.io`

5. **Access from anywhere:** `https://xyz789.ngrok.io`

### Using Port Forwarding (Advanced)

1. Log into your router (usually `192.168.1.1`)
2. Set up port forwarding:
   - External Port: 8001 → Internal Port: 8001 → Your Computer's IP
   - External Port: 3000 → Internal Port: 3000 → Your Computer's IP
3. Find your public IP: https://whatismyipaddress.com/
4. Access via: `http://YOUR_PUBLIC_IP:3000`

**⚠️ Security Warning:** Port forwarding exposes your app to the internet. Use with caution!

---

## 🛠️ Troubleshooting

### Issue 1: Cannot access from mobile device

**Solution:**
- Ensure both devices are on the **same Wi-Fi network**
- Check if your computer's firewall is blocking port 3000 and 8001

**Windows Firewall:**
```bash
# Allow ports in Windows Firewall
netsh advfirewall firewall add rule name="E-ARMS Frontend" dir=in action=allow protocol=TCP localport=3000
netsh advfirewall firewall add rule name="E-ARMS Backend" dir=in action=allow protocol=TCP localport=8001
```

**Mac Firewall:**
```bash
# Go to System Preferences → Security & Privacy → Firewall → Firewall Options
# Add Python and Node to allowed apps
```

### Issue 2: MongoDB connection failed

**Solution:**
```bash
# Check if MongoDB is running
# Windows:
net start MongoDB

# Mac:
brew services start mongodb-community

# Linux:
sudo systemctl start mongod

# Verify:
mongo --eval "db.version()"
```

### Issue 3: Backend not accessible

**Solution:**
- Check backend is running: `curl http://localhost:8001/api/status`
- Verify backend .env has correct MongoDB URL
- Check MongoDB is running

### Issue 4: "Network Error" in frontend

**Solution:**
1. Check `frontend/.env.local` has correct backend URL
2. Verify backend is running on the specified IP:port
3. Clear browser cache and hard refresh (Ctrl + Shift + R)

### Issue 5: App works on computer but not on phone

**Solution:**
- Double-check you're using **local IP** (not localhost) in `.env.local`
- Restart frontend after changing `.env.local`
- Ensure both devices on same Wi-Fi network
- Check firewall settings

---

## 📊 Quick Reference

| Component | Local Access | Network Access | 
|-----------|--------------|----------------|
| **Frontend** | http://localhost:3000 | http://YOUR_IP:3000 |
| **Backend API** | http://localhost:8001 | http://YOUR_IP:8001 |
| **MongoDB** | mongodb://localhost:27017 | (Internal only) |

---

## 🔄 Daily Usage

### Starting the App:

```bash
# 1. Start MongoDB (if not auto-starting)
# Windows: net start MongoDB
# Mac: brew services start mongodb-community
# Linux: sudo systemctl start mongod

# 2. Start Backend
cd backend && python server.py

# 3. Start Frontend
cd frontend && yarn start
# OR for production: yarn build && npx serve -s build -l 3000
```

### Accessing the App:

- **From your computer:** http://localhost:3000
- **From your mobile:** http://YOUR_LOCAL_IP:3000

---

## 💡 Tips

1. **Create Desktop Shortcuts:**
   - Create batch files (Windows) or shell scripts (Mac/Linux) to start all services
   - Pin to desktop for one-click startup

2. **Auto-start on Boot:**
   - Set MongoDB to start automatically
   - Use Windows Task Scheduler or systemd to auto-start backend/frontend

3. **Static IP:**
   - Configure your router to assign a static IP to your computer
   - This prevents your IP from changing and breaking mobile access

4. **Backup Database:**
   ```bash
   mongodump --db earms_db --out /path/to/backup
   ```

---

## ✅ Success Checklist

- [ ] MongoDB installed and running
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Found local IP address
- [ ] Created and configured `.env.local`
- [ ] Backend running on port 8001
- [ ] Frontend running on port 3000
- [ ] Can access app on computer (localhost:3000)
- [ ] Can access app on mobile (YOUR_IP:3000)
- [ ] Firewall configured to allow ports 3000 and 8001

---

## 🎉 You're All Set!

Your E-ARMS app is now running locally and accessible from any device on your network, with or without internet!

For issues or questions, refer to the Troubleshooting section above.
