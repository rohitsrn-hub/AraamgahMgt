# 🏠 E-ARMS - Araamgah Management System

**ECSAG Automated Room Management System** - A comprehensive military rest house booking and management platform.

---

## 🚀 Quick Start (Local Deployment)

### For Windows Users:
1. Double-click `start-local.bat`
2. Access at `http://localhost:3000`

### For Mac/Linux Users:
1. Run `./start-local.sh`
2. Access at `http://localhost:3000`

**📱 Access from Mobile/Tablet:**
- Find your computer's IP address (shown when you run the startup script)
- Open browser on your mobile: `http://YOUR_IP:3000`
- Example: `http://192.168.1.105:3000`

---

## 📚 Documentation

- **Quick Start Guide**: [`QUICK_START.md`](QUICK_START.md) - Get up and running in 5 minutes
- **Complete Deployment Guide**: [`LOCAL_DEPLOYMENT.md`](LOCAL_DEPLOYMENT.md) - Detailed setup instructions
- **Product Requirements**: [`memory/PRD.md`](memory/PRD.md) - Full feature documentation

---

## ✨ Features

### Booking Management
- ✅ Room booking with multiple payment modes (Cash, UPI, Bank Transfer, Card)
- ✅ Phone number capture with WhatsApp confirmation message
- ✅ Check-in with comprehensive guest data capture
- ✅ Check-out with bilingual feedback (English + Hindi)
- ✅ Cancellation with auto-calculated refunds
- ✅ Pending refunds tracking

### Dashboard & Analytics
- ✅ Real-time occupancy status (Overall, Cat I, Cat II)
- ✅ Monthly calendar planner with room availability
- ✅ Analytics: bookings, guests, occupancy rates
- ✅ Fund generation tracking
- ✅ Feedback analytics with emoji ratings

### Reports & Management
- ✅ Monthly PDF reports with license fee breakdown
- ✅ Print bill/receipt functionality
- ✅ Room and staff management
- ✅ Settings: room rates, ranks, license fees

---

## 🛠️ Technology Stack

- **Frontend**: React, Tailwind CSS, shadcn/ui components
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **PDF Generation**: jsPDF with autoTable

---

## 📦 Prerequisites

- Node.js v16+
- Python 3.9+
- MongoDB 4.4+
- Yarn package manager

---

## 🔧 Manual Installation

If you prefer manual setup:

### 1. Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
yarn install
```

### 2. Configure Environment

```bash
# Frontend - Copy and edit
cd frontend
cp .env.local.template .env.local
# Edit .env.local with your local IP address
```

### 3. Start Services

```bash
# Start MongoDB
# Windows: net start MongoDB
# Mac: brew services start mongodb-community
# Linux: sudo systemctl start mongod

# Start Backend (Terminal 1)
cd backend
python server.py

# Start Frontend (Terminal 2)
cd frontend
yarn start
```

---

## 🌐 Network Access

### Works WITHOUT Internet:
- ✅ Access on same computer (localhost)
- ✅ Access from mobile/tablet on same Wi-Fi network
- ✅ All features fully functional offline

### Optional Internet Access:
- Use `ngrok` for remote access when internet is available
- See [`LOCAL_DEPLOYMENT.md`](LOCAL_DEPLOYMENT.md) for details

---

## 📂 Project Structure

```
AraamgahMgt/
├── backend/              # FastAPI backend
│   ├── server.py        # Main API server (~1750 lines)
│   ├── requirements.txt # Python dependencies
│   └── .env            # Backend configuration
├── frontend/            # React frontend
│   ├── src/
│   │   ├── pages/      # Dashboard, Bookings, Rooms, etc.
│   │   ├── components/ # Reusable UI components
│   │   └── utils/      # PDF generation utilities
│   ├── package.json
│   └── .env.local      # Frontend configuration (you create this)
├── start-local.bat      # Windows startup script
├── start-local.sh       # Mac/Linux startup script
├── deploy-production.sh # Production build script
├── QUICK_START.md       # Quick reference guide
└── LOCAL_DEPLOYMENT.md  # Complete deployment guide
```

---

## 🎯 Access URLs

| Location | URL |
|----------|-----|
| **Same Computer** | http://localhost:3000 |
| **Other Devices (Local Network)** | http://YOUR_LOCAL_IP:3000 |
| **Backend API** | http://YOUR_LOCAL_IP:8001 |
| **API Documentation** | http://YOUR_LOCAL_IP:8001/docs |

---

## 🔐 Default Setup

After first run, configure:
- Room rates (Cat I, Cat II, Def Civ)
- License fees
- Available rooms
- Staff members
- Military ranks

All settings accessible via Settings page in the app.

---

## 🐛 Troubleshooting

**Can't access from mobile?**
- Ensure both devices on same Wi-Fi network
- Check firewall settings (see LOCAL_DEPLOYMENT.md)
- Verify you're using local IP, not "localhost"

**MongoDB connection error?**
- Check MongoDB service is running
- Verify `backend/.env` has correct MONGO_URL

**Port already in use?**
- Stop any existing instances
- Check for other apps using ports 3000 or 8001

For detailed troubleshooting, see [`LOCAL_DEPLOYMENT.md`](LOCAL_DEPLOYMENT.md)

---

## 💾 Database Backup

```bash
# Backup
mongodump --db earms_db --out ./backup

# Restore
mongorestore --db earms_db ./backup/earms_db
```

---

## 📝 Recent Updates

**Latest Changes:**
- ✅ Phone number capture in booking form
- ✅ WhatsApp confirmation message generation
- ✅ UPI Transaction ID field added
- ✅ Dashboard layout improvements with colorful sections
- ✅ Prominent "New Booking" button
- ✅ Calendar planner repositioned below occupancy
- ✅ **Local deployment configuration complete**

---

## 🤝 Support

For issues or questions:
1. Check [`QUICK_START.md`](QUICK_START.md) for common solutions
2. Review [`LOCAL_DEPLOYMENT.md`](LOCAL_DEPLOYMENT.md) for detailed help
3. Check troubleshooting section above

---

## 📄 License

Internal use - Military rest house management system.

---

**Made with ❤️ for efficient Araamgah management**

🚀 **Get Started**: Run `start-local.bat` (Windows) or `./start-local.sh` (Mac/Linux)
