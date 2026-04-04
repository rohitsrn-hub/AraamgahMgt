# 📋 E-ARMS Quick Start Guide

## ⚡ Quick Setup (First Time Only)

### 1. Find Your Local IP
```bash
# Windows
ipconfig

# Mac/Linux  
ifconfig
```
**Note your IPv4 address** (e.g., 192.168.1.105)

### 2. Configure Frontend
```bash
cd frontend
cp .env.local.template .env.local
```

Edit `.env.local` and replace `YOUR_LOCAL_IP`:
```
REACT_APP_BACKEND_URL=http://192.168.1.105:8001
```

---

## 🚀 Daily Startup

### Windows:
```bash
# Double-click: start-local.bat
# OR run in Command Prompt:
start-local.bat
```

### Mac/Linux:
```bash
./start-local.sh
```

### Manual Start:
```bash
# Terminal 1 - Backend
cd backend && python server.py

# Terminal 2 - Frontend
cd frontend && yarn start
```

---

## 📱 Access the App

| Device | URL |
|--------|-----|
| **Your Computer** | http://localhost:3000 |
| **Mobile/Tablet** | http://YOUR_LOCAL_IP:3000 |
| **Other PC on Network** | http://YOUR_LOCAL_IP:3000 |

**Example:** If your IP is `192.168.1.105`:
- Mobile: `http://192.168.1.105:3000`

---

## 🔧 Common Commands

### Check Services
```bash
# MongoDB status
# Windows: net start MongoDB
# Mac: brew services list | grep mongo
# Linux: sudo systemctl status mongod

# Backend running?
curl http://localhost:8001/api/status

# Frontend running?
curl http://localhost:3000
```

### Restart Services
```bash
# Backend
# Stop: Ctrl+C in backend terminal
# Start: python server.py

# Frontend
# Stop: Ctrl+C in frontend terminal
# Start: yarn start
```

### Backup Database
```bash
mongodump --db earms_db --out ./backup_$(date +%Y%m%d)
```

---

## ❗ Troubleshooting

| Problem | Solution |
|---------|----------|
| **Can't access from phone** | • Both devices on same Wi-Fi?<br>• Used local IP (not localhost)?<br>• Firewall blocking ports? |
| **MongoDB error** | • Check if MongoDB is running<br>• Windows: `net start MongoDB`<br>• Mac: `brew services start mongodb-community` |
| **Port already in use** | • Kill process using port<br>• Windows: `netstat -ano \| findstr :3000`<br>• Mac/Linux: `lsof -ti:3000 \| xargs kill` |

---

## 📞 Need Help?

Refer to detailed guide: **LOCAL_DEPLOYMENT.md**

---

## ✅ Pre-flight Checklist

- [ ] MongoDB running
- [ ] Backend started (port 8001)
- [ ] Frontend started (port 3000)
- [ ] Can access on computer (localhost:3000)
- [ ] Can access on phone (YOUR_IP:3000)

---

**🎉 You're ready to use E-ARMS offline!**
