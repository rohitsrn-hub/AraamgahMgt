# 🔐 Reusable Prompt: JWT Authentication with RBAC Setup

## Copy this entire prompt and paste it to the agent working on your other app:

---

**TASK: Implement a complete JWT Authentication system with Role-Based Access Control (RBAC) for this application.**

---

## 📋 **Tech Stack:**
- **Frontend**: React 19 + React Router + Axios
- **Backend**: FastAPI + Python 3.11+
- **Database**: MongoDB (via Motor async driver)
- **Deployment**: Vercel (frontend) + Render (backend)
- **Auth**: JWT tokens (python-jose + passlib with bcrypt)

---

## 🎯 **Requirements:**

### **1. Authentication System**

**Backend (`/app/backend/`):**
- Install dependencies: `python-jose[cryptography]==3.5.0`, `passlib==1.7.4`, `bcrypt==4.1.2`
- Create `/app/backend/models/user.py` with User schema (id, username, email, password_hash, name, role, is_active, created_at, last_login)
- Create `/app/backend/utils/auth.py` with:
  - `hash_password(password)` - bcrypt hashing
  - `verify_password(plain, hashed)` - verification
  - `create_access_token(data)` - JWT creation
  - `verify_token(token)` - JWT verification
  - `get_current_user(token)` - dependency for protected routes
  - `require_admin_role(user)` - dependency for admin-only routes
- Create admin seed script: `/app/backend/scripts/create_admin.py`
- Add environment variables to `/app/backend/.env`:
  ```
  JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
  JWT_ALGORITHM=HS256
  JWT_EXPIRE_MINUTES=1440
  ```
- Force Python 3.11.9 by creating `/app/backend/runtime.txt` with content: `python-3.11.9`

**API Endpoints in `server.py`:**
- `POST /api/auth/login` - Login (returns token and user info)
  - **IMPORTANT**: Search for user by `username` OR `email` using MongoDB `$or` operator
  - Allows login with either username or email address
- `GET /api/users` - List users (Admin only)
- `POST /api/users` - Create user (Admin only)
- `PUT /api/users/{user_id}` - Update user (Admin only)
- `DELETE /api/users/{user_id}` - Delete user (Admin only)
- `PUT /api/users/{user_id}/password` - Reset password (Admin only)

**Frontend (`/app/frontend/src/`):**
- Create `/app/frontend/src/contexts/AuthContext.jsx` with:
  - `login(username, password)` function
  - `logout()` function
  - `isAuthenticated()` check
  - `user` state (current logged-in user with role)
  - Axios interceptor to add `Authorization: Bearer <token>` to all requests
  - Axios interceptor to catch 401 and redirect to login

- Create `/app/frontend/src/components/ProtectedRoute.jsx` - Wrapper for authenticated routes

- Create `/app/frontend/src/pages/Login.jsx` with:
  - Username and password fields
  - Password visibility toggle (eye icon)
  - Role-based redirect after login:
    - `admin` → `/dashboard`
    - `staff` → `/` (Command Center/Splash Screen)
    - `viewer` → `/dashboard`

- Create `/app/frontend/src/pages/UserManagement.jsx` with:
  - User list table (username, name, role, status, actions)
  - Create user form (with password visibility toggle)
  - Password reset functionality:
    - Reset button for each user
    - Generate random password button
    - Copy to clipboard button
    - Show password once when created/reset
  - Toggle active/inactive status
  - Delete user

- Update `/app/frontend/src/App.js`:
  - Wrap app with `<AuthProvider>`
  - Protect all routes with `<ProtectedRoute>`
  - Check authentication BEFORE checking setup wizard
  - Add Axios interceptors for token and 401 handling

- Update `/app/frontend/src/components/Layout.jsx`:
  - Add logout button (top-right with user name)
  - RBAC for sidebar:
    - Admin: All menu items
    - Staff: Hide "User Management" and "Settings", SHOW "Backup & Restore"
    - Viewer: Hide "User Management", "Settings", "Backup & Restore"

---

### **2. Role-Based Access Control (RBAC)**

**Three Roles:**
1. **Admin** - Full access to everything
2. **Staff** - Can manage bookings, access most features, but NOT User Management or Settings
3. **Viewer** - Read-only access, all action buttons disabled

**Frontend Restrictions (find all action buttons and add viewer checks):**

In main feature pages (Dashboard, Bookings, etc.):
- Import `useAuth` hook
- Get `const { user } = useAuth();`
- Check `const isViewer = user?.role === 'viewer';`
- Disable these buttons for viewers:
  - **Dashboard page**: New Booking, Check In, Check Out, Cancel
  - **Bookings page**: New Booking, Check In, Check Out, Cancel, Amend
  - Any other modification actions
- Add `disabled={isViewer}` prop
- Add `title={isViewer ? "Viewers cannot perform this action" : "Normal tooltip"}` for tooltips
- Add disabled styling: `disabled:opacity-50 disabled:cursor-not-allowed`

**Backend Protection:**
- All mutation endpoints (POST/PUT/DELETE) require authentication
- User management endpoints require Admin role
- Use `Depends(get_current_user)` for auth-required routes
- Use `Depends(require_admin_role)` for admin-only routes

---

### **3. Security Best Practices**

**Password Handling:**
- NEVER store plain text passwords
- Always use bcrypt hashing
- Passwords CANNOT be retrieved (only reset)
- Minimum 8 characters validation
- Show passwords only once when created/reset (with copy button)

**Token Management:**
- Store JWT in localStorage (frontend)
- Add token to all API requests via Axios interceptor
- Token expires after 1440 minutes (24 hours)
- Redirect to login on 401 errors

**CORS Configuration:**
- Backend must allow frontend origin in `CORS_ORIGINS` env variable
- Example: `CORS_ORIGINS=https://your-app.vercel.app`

---

### **4. User Experience Enhancements**

**Login Page:**
- Clean, professional design
- Password visibility toggle (eye icon)
- Clear error messages
- Loading state while authenticating
- **No default credentials displayed** (security)

**User Management:**
- Admin can see all usernames clearly
- Password reset with one-click generation
- Copy password to clipboard
- Password visibility toggle in create and reset forms
- Warning: "Passwords shown only once - copy before closing"
- Visual role indicators (badges for Admin/Staff/Viewer)

**Role-Based Navigation:**
- Staff redirects to Command Center (splash screen) after login
- Viewers redirect to Dashboard
- Admins redirect to Dashboard
- Sidebar hides restricted menu items based on role

**Viewer Experience:**
- All data visible (tables, reports, analytics)
- Action buttons disabled (grayed out with helpful tooltips)
- Can print PDFs and export data
- Cannot create, edit, or delete anything

---

### **5. Testing Requirements**

After implementation, you MUST test:

**Authentication Flow:**
- [ ] Login page shows on first visit
- [ ] Can login with admin credentials
- [ ] Invalid credentials show error
- [ ] Token persists on page refresh
- [ ] Logout clears token and redirects to login
- [ ] Unauthorized users can't access protected routes

**RBAC Testing:**
- [ ] Admin sees all menu items and can access everything
- [ ] Staff doesn't see User Management or Settings in sidebar
- [ ] Staff CAN see Backup & Restore
- [ ] Staff redirects to Command Center after login
- [ ] Viewer redirects to Dashboard after login
- [ ] Viewer has all action buttons disabled (New Booking, Check In, Check Out, Cancel)
- [ ] Viewer can view data but cannot modify

**User Management:**
- [ ] Admin can create users (all roles)
- [ ] Password visibility toggle works in create form
- [ ] Admin can reset any user's password
- [ ] Generate password button creates 12-character random password
- [ ] Copy to clipboard works
- [ ] Can toggle user active/inactive
- [ ] Can delete users (except own account)
- [ ] New user can login with created credentials

**Security:**
- [ ] API returns 401 for unauthenticated requests
- [ ] User Management APIs return 403 for non-admin users
- [ ] Passwords are hashed in database (not plain text)
- [ ] Token expires after configured time
- [ ] CORS allows only configured origins

---

### **6. Deployment Configuration**

**Backend Environment Variables (Render):**
```bash
MONGO_URL=<existing>
DB_NAME=<existing>
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
CORS_ORIGINS=<your-vercel-frontend-url>
```

**Frontend Environment Variables (Vercel):**
```bash
REACT_APP_BACKEND_URL=<your-render-backend-url>
```

**Python Runtime:**
Create `/app/backend/runtime.txt` with: `python-3.11.9`

**Dependencies:**
Add to `/app/backend/requirements.txt`:
```
python-jose[cryptography]==3.5.0
bcrypt==4.1.2
passlib==1.7.4
```

---

### **7. Known Issues to Avoid**

**DON'T:**
- ❌ Use Python 3.14 (bcrypt compatibility issues) - Force 3.11.9 via runtime.txt
- ❌ Check setup wizard before authentication - Auth check must come first
- ❌ Use `passlib[bcrypt]>=1.7.4` - Pin exact versions to avoid conflicts
- ❌ Store passwords in plain text - Always hash with bcrypt
- ❌ Skip CORS configuration - Frontend will get blocked
- ❌ Hardcode JWT secret - Use environment variable

**DO:**
- ✅ Pin Python 3.11.9 in runtime.txt
- ✅ Pin bcrypt==4.1.2 and passlib==1.7.4
- ✅ Check `isAuthenticated()` before setup wizard in App.js
- ✅ Add Axios interceptors for token and 401 handling
- ✅ Generate strong JWT_SECRET_KEY with `openssl rand -hex 32`
- ✅ Test in preview environment before production deploy

---

### **8. First Admin User Creation**

**Option 1: MongoDB Atlas Direct Insert** (Easiest)
1. Generate hash locally: `python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(pwd_context.hash('Admin@2026!'))"`
2. Insert JSON in Atlas `users` collection:
```json
{
  "id": "admin-001",
  "username": "admin",
  "email": "admin",
  "password_hash": "$2b$12$PASTE_YOUR_HASH_HERE",
  "name": "System Administrator",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-04-13T00:00:00.000000+00:00",
  "last_login": null
}
```

**Option 2: Seed Script**
Run: `python /app/backend/scripts/create_admin.py`

---

### **9. File Structure Reference**

```
/app/
├── backend/
│   ├── models/
│   │   └── user.py (NEW)
│   ├── utils/
│   │   └── auth.py (NEW)
│   ├── scripts/
│   │   └── create_admin.py (NEW)
│   ├── runtime.txt (NEW - force Python 3.11.9)
│   ├── requirements.txt (UPDATE - add JWT dependencies)
│   ├── .env (UPDATE - add JWT variables)
│   └── server.py (UPDATE - add auth endpoints and dependencies)
│
├── frontend/src/
│   ├── contexts/
│   │   └── AuthContext.jsx (NEW)
│   ├── components/
│   │   ├── ProtectedRoute.jsx (NEW)
│   │   └── Layout.jsx (UPDATE - add logout, RBAC sidebar)
│   ├── pages/
│   │   ├── Login.jsx (NEW)
│   │   ├── UserManagement.jsx (NEW)
│   │   ├── Dashboard.jsx (UPDATE - disable viewer buttons)
│   │   └── [OtherPages].jsx (UPDATE - disable viewer actions)
│   └── App.js (UPDATE - add AuthProvider, ProtectedRoute, axios interceptors)
```

---

### **10. Success Criteria**

Implementation is complete when:
- ✅ Login page shows on app visit (unauthenticated users)
- ✅ **Can login with BOTH username and email** (either format works)
- ✅ **No default credentials shown on login page** (security)
- ✅ Admin can login and access everything
- ✅ Staff can login, redirects to Command Center, hides User Mgmt/Settings
- ✅ Viewer can login, redirects to Dashboard, **all action buttons disabled on Dashboard AND feature pages**
- ✅ Admin can create/reset/delete users
- ✅ Password reset with generate/copy functionality works
- ✅ **Password visibility toggle works in login, create, and reset forms**
- ✅ All API endpoints require authentication
- ✅ Logout clears session and redirects to login
- ✅ Token persists across page refreshes
- ✅ 401 errors automatically redirect to login
- ✅ All existing app features work with authentication
- ✅ Backup warnings show accurate time (if applicable)

---

## 🚨 **CRITICAL REMINDERS:**

1. **Test thoroughly** in preview environment before production
2. **Create admin user BEFORE** enabling auth in production
3. **Save JWT_SECRET_KEY securely** - losing it locks everyone out
4. **Change default password** immediately after first login
5. **Inform users** before deploying to production
6. **Keep credentials document updated** in `/app/memory/test_credentials.md`
7. **Login must accept username OR email** - use `$or` operator in login endpoint
8. **Dashboard AND all feature pages** must disable viewer buttons - check every action button
9. **No default credentials on login page** - remove any "test credentials" text for security
10. **Backup warnings** should calculate from fresh history, not cached status

---

## ✅ **Implementation Checklist:**

Use this to track progress:

**Backend:**
- [ ] Install JWT/bcrypt dependencies
- [ ] Create User model (models/user.py)
- [ ] Create auth utilities (utils/auth.py)
- [ ] Add JWT env variables to .env
- [ ] Create runtime.txt (Python 3.11.9)
- [ ] Add auth endpoints to server.py
- [ ] **CRITICAL**: Login endpoint uses `$or` to search username OR email
- [ ] Protect existing endpoints with authentication
- [ ] Add password reset endpoint
- [ ] Create admin seed script
- [ ] Test all endpoints with Postman/curl

**Frontend:**
- [ ] Create AuthContext with login/logout
- [ ] Create ProtectedRoute component
- [ ] Create Login page with password toggle
- [ ] **CRITICAL**: Remove any default credentials text from login page
- [ ] Create UserManagement page with reset/generate
- [ ] Add password visibility toggle to create and reset forms
- [ ] Update App.js (AuthProvider, interceptors, route protection)
- [ ] Update Layout (logout button, RBAC sidebar)
- [ ] **CRITICAL**: Update Dashboard - disable all action buttons for viewer
- [ ] **CRITICAL**: Update all feature pages - disable all action buttons for viewer
- [ ] Test all user flows (Admin/Staff/Viewer)
- [ ] Verify backup warnings show accurate time (if applicable)

**Deployment:**
- [ ] Push to testing branch
- [ ] Add JWT env variables to Render test service
- [ ] Create admin user in test database
- [ ] Test preview deployment thoroughly
- [ ] Verify login works with username AND email
- [ ] Verify viewer restrictions on Dashboard and all feature pages
- [ ] Merge to main branch
- [ ] Add JWT env variables to Render production
- [ ] Create admin user in production database
- [ ] Test production deployment
- [ ] Change default admin password
- [ ] Create real user accounts
- [ ] Inform team members

---

**IMPORTANT: Follow this prompt step-by-step. This is a proven implementation that works. Don't skip steps or take shortcuts - they will cause authentication failures, bcrypt errors, CORS issues, or incomplete viewer restrictions.**

---

**Recent improvements in this version:**
- ✅ Login accepts username OR email (MongoDB `$or` operator)
- ✅ Dashboard viewer restrictions added
- ✅ No default credentials on login page (security)
- ✅ Backup warning accuracy fix (calculate from fresh history)
- ✅ Password visibility toggles in all forms
- ✅ Comprehensive testing checklist

**Good luck! This implementation took multiple iterations to perfect, so following this prompt will save you significant time and debugging.**

