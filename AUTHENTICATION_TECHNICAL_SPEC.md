# SARAI Authentication Implementation - Technical Specification

## 📋 Critical Information for Authentication Setup

### **Use This Document When Prompting for Authentication Implementation**

---

## 🏗️ Current Architecture

### **Deployment Model**
- **Type**: Emergent Native Deployment (Single-service monolith)
- **Backend**: FastAPI (Python 3.11) on port 8001 → exposed via `/api` prefix
- **Frontend**: React 19 on port 3000
- **Database**: MongoDB (Motor async driver)
- **Proxy**: Kubernetes Ingress (routes `/api/*` → backend:8001, everything else → frontend:3000)

### **Critical URLs & Environment Variables**

#### Frontend (`.env`)
```bash
REACT_APP_BACKEND_URL=https://repo-reconstruction.preview.emergentagent.com
# Note: In production, this points to the SAME domain (not cross-origin)
```

#### Backend (`.env`)
```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"  # Change to specific origin in production
```

#### API Communication Pattern
```javascript
// Frontend App.js
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Example API call
await axios.get(`${API}/settings`);  // → https://domain.com/api/settings
```

---

## 🔴 **CRITICAL: Avoid These Common Pitfalls**

### **1. CORS Configuration Issues**
❌ **WRONG** (Causes CORS errors in deployment):
```python
# DO NOT DO THIS - will fail in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"]  # ❌ localhost won't work in production
)
```

✅ **CORRECT** (Works in both dev and production):
```python
# Use environment variable, defaulting to wildcard
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Current CORS Setup** (already in `/app/backend/server.py` line 3170-3175):
```python
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **2. Password Hashing - Environment Consistency**

❌ **WRONG** (Bcrypt salt in .env gets shell-expanded):
```bash
# .env file
BCRYPT_SALT="$2b$12$randomsalt"  # ❌ Shell expands $2b to empty string!
```

✅ **CORRECT** (Don't store salt in .env, generate per-hash):
```python
import bcrypt

# Hash password (generates new salt each time)
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Verify password
bcrypt.checkpw(password.encode('utf-8'), hashed_password)
```

### **3. Session/Token Storage**

❌ **WRONG** (Session stored in backend memory - lost on restart):
```python
# DO NOT use in-memory sessions
sessions = {}  # ❌ Lost on pod restart in Kubernetes
```

✅ **CORRECT** (Use JWT or store sessions in MongoDB):
```python
# Option 1: JWT (stateless, recommended)
from jose import jwt
token = jwt.encode({"user_id": user_id}, SECRET_KEY, algorithm="HS256")

# Option 2: MongoDB sessions
await db.sessions.insert_one({"session_id": sid, "user_id": uid, "expires": ...})
```

---

## 📦 Dependencies Already Installed

### Backend (`requirements.txt`)
```
fastapi==0.110.1
uvicorn==0.25.0
python-dotenv>=1.0.1
pymongo==4.5.0
pydantic>=2.6.4
motor==3.3.1  # Async MongoDB driver
python-multipart>=0.0.9
APScheduler==3.10.4
pytz==2024.1
```

### Frontend (package.json - partial)
```json
{
  "dependencies": {
    "react": "^19.0.0",
    "react-router-dom": "^7.1.3",
    "axios": "^1.7.9",
    "@radix-ui/react-dialog": "^1.1.11",
    // ... other UI components
  }
}
```

**Missing Auth Dependencies (Need to Install)**:
```bash
# Backend
pip install python-jose[cryptography]  # JWT
pip install passlib[bcrypt]  # Password hashing
pip install python-multipart  # Form data (already installed)

# Frontend
yarn add jwt-decode  # Decode JWT tokens
yarn add react-hook-form  # Form handling (if not using native)
```

---

## 🗄️ Database Structure

### Current MongoDB Collections
```javascript
{
  "bookings": { /* Booking data */ },
  "rooms": { /* Room data */ },
  "staff": { /* Staff data */ },
  "app_settings": { /* App configuration */ },
  "backup_metadata": { /* Backup history */ },
  "refunds": { /* Refund records */ }
}
```

### Proposed Auth Collections
```javascript
// New collections to add:
{
  "users": {
    "id": "uuid",
    "email": "user@example.com",
    "password_hash": "bcrypt_hash",
    "role": "admin|staff|viewer",
    "name": "Full Name",
    "is_active": true,
    "created_at": "ISO timestamp",
    "last_login": "ISO timestamp"
  },
  
  "sessions": {  // Optional, only if using session-based auth
    "session_id": "uuid",
    "user_id": "user_uuid",
    "token": "jwt_token",
    "expires_at": "ISO timestamp",
    "created_at": "ISO timestamp"
  }
}
```

---

## 🔐 Authentication Requirements

### **User Roles** (Recommended)
```python
class UserRole(str, Enum):
    ADMIN = "admin"      # Full access (manage users, settings, bookings)
    STAFF = "staff"      # Booking operations (check-in/out, view reports)
    VIEWER = "viewer"    # Read-only (view bookings, reports)
```

### **Protected Routes** (Existing routes that need auth)
```
Public (No Auth Required):
  - POST /api/auth/login
  - POST /api/auth/register (maybe only for first admin)

Protected (Require Authentication):
  ALL ADMIN:
    - POST /api/bookings
    - PUT /api/bookings/*
    - DELETE /api/bookings/*
    - POST /api/backups/*
    - PUT /api/settings
    - POST /api/staff
    
  STAFF:
    - GET /api/bookings
    - POST /api/bookings/check-in
    - POST /api/bookings/check-out
    
  VIEWER:
    - GET /api/bookings
    - GET /api/reports/*
```

---

## 🛠️ Implementation Approach (Recommended)

### **Option 1: JWT-Based Authentication (Recommended for Emergent)**

**Why JWT?**
- ✅ Stateless (no server memory, works with Kubernetes pod restarts)
- ✅ No cross-origin cookie issues
- ✅ Works with Emergent's proxy setup
- ✅ Simple to implement

**Backend Flow**:
```python
# 1. Login endpoint
@api_router.post("/auth/login")
async def login(email: str, password: str):
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    
    token = create_jwt_token({"user_id": user["id"], "role": user["role"]})
    return {"access_token": token, "user": {...}}

# 2. Protected route dependency
async def get_current_user(token: str = Header(..., alias="Authorization")):
    try:
        payload = jwt.decode(token.replace("Bearer ", ""), SECRET_KEY)
        return payload
    except:
        raise HTTPException(401, "Invalid token")

# 3. Use in routes
@api_router.get("/bookings", dependencies=[Depends(get_current_user)])
async def get_bookings():
    ...
```

**Frontend Flow**:
```javascript
// 1. Login
const response = await axios.post(`${API}/auth/login`, {email, password});
localStorage.setItem("token", response.data.access_token);
localStorage.setItem("user", JSON.stringify(response.data.user));

// 2. Add token to all requests (axios interceptor)
axios.interceptors.request.use(config => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 3. Handle 401 (logout)
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.clear();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
```

### **Option 2: Emergent-Managed Google OAuth**

**Why?**
- ✅ No password management
- ✅ Pre-built by Emergent
- ✅ Secure and tested

**How to Request**:
```
Ask Emergent agent for "Emergent-managed Google OAuth integration"
Provide: redirect_uri (your app domain)
Receive: Client credentials + integration guide
```

---

## 🚨 Deployment-Specific Considerations

### **1. Environment Variables in Production**

**Backend `.env.production`**:
```bash
MONGO_URL="<PRODUCTION_MONGODB_URL>"
DB_NAME="sarai_production"
CORS_ORIGINS="https://your-deployed-domain.com"
JWT_SECRET_KEY="<GENERATE_STRONG_SECRET>"  # openssl rand -hex 32
JWT_ALGORITHM="HS256"
JWT_EXPIRE_MINUTES="1440"  # 24 hours
```

**Frontend `.env.production`**:
```bash
REACT_APP_BACKEND_URL=https://your-deployed-domain.com
```

### **2. First Admin User Setup**

**Approach**: Seed script or special registration endpoint

```python
# /backend/scripts/create_admin.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
import uuid
from datetime import datetime, timezone

async def create_admin():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Check if admin exists
    existing = await db.users.find_one({"role": "admin"})
    if existing:
        print("Admin user already exists")
        return
    
    # Create first admin
    admin_user = {
        "id": str(uuid.uuid4()),
        "email": "admin@sarai.com",
        "password_hash": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
        "role": "admin",
        "name": "Admin User",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(admin_user)
    print(f"✅ Admin user created: {admin_user['email']}")
    print(f"⚠️  Password: admin123 (CHANGE IMMEDIATELY)")

if __name__ == "__main__":
    asyncio.run(create_admin())
```

Run once after deployment:
```bash
cd /app/backend
python scripts/create_admin.py
```

### **3. Session Cleanup (If using DB sessions)**

Add to existing scheduler in `scheduler_service.py`:
```python
# Clean expired sessions daily
scheduler.add_job(
    cleanup_sessions,
    trigger=CronTrigger(hour=3, minute=30, timezone=IST),
    id='session_cleanup',
    replace_existing=True
)

async def cleanup_sessions():
    """Remove expired sessions"""
    await db.sessions.delete_many({
        "expires_at": {"$lt": datetime.now(timezone.utc).isoformat()}
    })
```

---

## 📝 Recommended Prompt for Authentication Implementation

Use this template when asking for auth implementation:

```
TASK: Implement JWT-based user authentication for SARAI app

REQUIREMENTS:
1. User roles: admin, staff, viewer
2. JWT tokens (stateless, 24hr expiry)
3. Protected routes with role-based access control
4. Login/logout functionality
5. Password hashing with bcrypt (NOT stored in .env)
6. First admin user seed script

TECHNICAL CONSTRAINTS:
- Backend: FastAPI + Motor (async MongoDB)
- Frontend: React 19 + React Router + Axios
- Current API prefix: /api (all routes must use this)
- CORS already configured (lines 3170-3175 in server.py)
- Environment: Emergent Native Deployment (Kubernetes)
- MongoDB: Async driver (Motor), no _id in responses

CRITICAL DEPLOYMENT REQUIREMENTS:
1. JWT_SECRET_KEY must be in .env (generate with openssl rand -hex 32)
2. Use existing CORS middleware (line 3170 in server.py) - DO NOT modify
3. Tokens in Authorization header: "Bearer <token>"
4. Store tokens in localStorage (frontend)
5. Axios interceptors for auto-token injection
6. 401 response = auto-redirect to /login

EXISTING CODE TO PRESERVE:
- MongoDB connection (lines 35-38 in server.py)
- API router with /api prefix (line 30 in server.py)  
- CORS middleware (lines 3170-3175 in server.py)
- Frontend API setup in App.js (line 23)

FILE STRUCTURE:
Backend:
  - /app/backend/server.py (add auth routes here)
  - /app/backend/utils/auth.py (NEW: JWT helpers, password hashing)
  - /app/backend/scripts/create_admin.py (NEW: seed first admin)
  
Frontend:
  - /app/frontend/src/pages/Login.jsx (NEW)
  - /app/frontend/src/contexts/AuthContext.jsx (NEW)
  - /app/frontend/src/App.js (UPDATE: add auth routes, interceptors)

DEPENDENCIES TO INSTALL:
Backend: python-jose[cryptography], passlib[bcrypt]
Frontend: jwt-decode

DO NOT:
- Store bcrypt salt in .env (use bcrypt.gensalt() per hash)
- Use in-memory sessions (will break on pod restart)
- Hardcode localhost URLs
- Modify existing CORS setup
- Use cookies (stick to Bearer tokens)

TEST AFTER IMPLEMENTATION:
1. Create admin user with seed script
2. Login via /api/auth/login
3. Verify token in Authorization header
4. Test protected route access
5. Test logout (clear token)
6. Test role-based access (admin vs staff vs viewer)
```

---

## 🧪 Testing Checklist

After auth is implemented, verify:

- [ ] Admin user can be created via seed script
- [ ] Login returns JWT token
- [ ] Token is stored in localStorage
- [ ] Token is sent in Authorization header
- [ ] Protected routes return 401 without token
- [ ] Protected routes work with valid token
- [ ] Role-based access works (admin can do X, staff cannot)
- [ ] Logout clears token and redirects
- [ ] Token expiry works (401 after 24 hours)
- [ ] CORS works in deployed environment
- [ ] Password hashing works (login with correct password succeeds)

---

## 📞 Support

If authentication fails in deployment:
1. Check browser console for CORS errors
2. Check backend logs: `tail -f /var/log/supervisor/backend.*.log`
3. Verify CORS_ORIGINS matches your domain
4. Verify JWT_SECRET_KEY is set in backend/.env
5. Test API directly: `curl -X POST https://domain.com/api/auth/login -d '{"email":"...","password":"..."}'`

---

**Last Updated**: April 12, 2026
**App Version**: SARAI v2.1
**Document Purpose**: Guide for implementing authentication without repeating past deployment failures
