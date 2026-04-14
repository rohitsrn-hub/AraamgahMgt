# 🔧 Room Rate Fix Instructions

## Issue
Cat II room rate showing ₹300 instead of ₹400 in booking form.

## Root Cause
Database settings had incorrect or missing room rate values.

## ✅ Solution Applied

### 1. Updated Default Values in Code
**File**: `/app/backend/models/settings.py`

**New hardcoded defaults**:
- **Org Cat I**: ₹500
- **Org Cat II**: ₹400
- **Non-Org Cat I**: ₹600
- **Non-Org Cat II**: ₹600
- **Default Advance**: ₹400 (fixed for all bookings)

### 2. Created Update Script
**File**: `/app/backend/scripts/update_room_rates.py`

This script updates the database settings to correct values.

---

## 🚀 How to Fix in Production

### Option A: Run Update Script (Easiest)

**If you have Render Shell access**:
```bash
cd /opt/render/project/src/backend
python scripts/update_room_rates.py
```

**If Render Shell is disabled** - Run locally:
```bash
cd /app/backend
python scripts/update_room_rates.py
```

**Output**:
```
🔧 SARAI Room Rate Update Script
==================================================
📊 Connected to database: your_database_name

✅ Updating to correct values:
  Org Cat I Rate: ₹500.0
  Org Cat II Rate: ₹400.0
  Non-Org Cat I Rate: ₹600.0
  Non-Org Cat II Rate: ₹600.0
  Default Advance: ₹400.0

🎉 Settings updated successfully!
```

---

### Option B: Update via MongoDB Atlas

1. Go to [MongoDB Atlas](https://cloud.mongodb.com) → Browse Collections
2. Select your cluster → Database: `earms_admin` (or your production DB)
3. Collection: `settings`
4. Find the settings document and click **"Edit"**
5. Update these fields:

```json
{
  "cat_i_rate": 500.0,
  "cat_ii_rate": 400.0,
  "def_civ_cat_i_rate": 600.0,
  "def_civ_cat_ii_rate": 600.0,
  "default_advance_amount": 400.0
}
```

6. Click **"Update"**

---

### Option C: Via Settings Page (Admin Only)

1. Login as Admin
2. Go to **Settings** page
3. Update room rates:
   - Org Cat I Rate: `500`
   - Org Cat II Rate: `400`
   - Non-Org Cat I Rate: `600`
   - Non-Org Cat II Rate: `600`
   - Default Advance Amount: `400`
4. Click **"Save Settings"**

---

## ✅ Verification

After updating:

1. **Refresh browser** (`Ctrl + Shift + R`)
2. Go to **Bookings** → Click **"New Booking"**
3. Select dates and view available rooms
4. **Verify room rates displayed**:
   - Cat I rooms: ₹500/night (for Org guests)
   - Cat II rooms: ₹400/night (for Org guests)
   - Both: ₹600/night (for Non-Org guests)

---

## 📝 What Was Fixed

**Before**:
- Cat II showing ₹300 (incorrect)
- Values might have been inconsistent

**After**:
- Org Cat I: ₹500 ✅
- Org Cat II: ₹400 ✅
- Non-Org Cat I: ₹600 ✅
- Non-Org Cat II: ₹600 ✅
- Default Advance: ₹400 ✅

---

## 🔄 For Future Reference

**Room rates are stored in**:
- Database: `settings` collection
- Backend default: `/app/backend/models/settings.py` (AppSettings class)
- Frontend reads from: Settings API (`/api/settings`)

**To change rates in future**:
- Admin can update via Settings page
- OR run the update script
- OR update directly in MongoDB Atlas

---

## ⚠️ Important Notes

1. **These are default values** - they're used when:
   - New installation (no settings exist)
   - Settings reset
   - Fallback if settings missing

2. **Actual rates come from database** - Admin can change via Settings page

3. **After changing rates** - Users must refresh browser to see new values

---

**Script Location**: `/app/backend/scripts/update_room_rates.py`  
**Settings Model**: `/app/backend/models/settings.py`  
**Frontend Display**: `/app/frontend/src/pages/Bookings.jsx` (lines 2035-2040)
