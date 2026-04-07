# Formation Signs Fix - Setup Wizard Update

## Date
April 7, 2026

## Issue Reported
User was asked for formation signs during setup even though they should have been pre-configured and the upload option removed.

## Root Cause
The SetupWizard still had Step 1 for "Formation Signs" with input fields for URLs, even though default formation sign images were already configured in the database.

## Solution Implemented

### 1. Removed Formation Signs Step from Setup Wizard
- **Before:** 3-step wizard (Formation Signs → Room Configuration → Room Rates)
- **After:** 2-step wizard (Room Configuration → Room Rates)

### 2. Hard-coded Formation Sign URLs
Formation signs now use pre-configured default images:
- **Formation Sign 1 (Left):** Unsplash shield emblem image
- **Formation Sign 2 (Right):** Unsplash shield emblem image

These URLs are always sent to the backend during setup - no user input required.

### 3. Changes Made

**File: `/app/frontend/src/pages/SetupWizard.jsx`**

✅ **Removed:**
- Entire Step 1 (Formation Signs UI section with input fields)
- `fmn_sign_1_url` and `fmn_sign_2_url` from formData state

✅ **Updated:**
- Progress indicator: `[1, 2, 3]` → `[1, 2]` (2 steps instead of 3)
- Step navigation: `Math.min(s + 1, 3)` → `Math.min(s + 1, 2)`
- Footer buttons: `step < 3` → `step < 2`
- handleSubmit: Now always sends `DEFAULT_FMN_1` and `DEFAULT_FMN_2`

✅ **New Step Mapping:**
- Step 1: Room Configuration (number of Cat I & Cat II rooms)
- Step 2: Room Rates (Cat I & Cat II daily rates)

## Default Formation Sign URLs

```javascript
const DEFAULT_FMN_1 = "https://images.unsplash.com/photo-1765555648802-53235276a40b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwyfHxzaGllbGQlMjBlbWJsZW18ZW58MHx8fHwxNzc1MDcwOTU4fDA&ixlib=rb-4.1.0&q=85";

const DEFAULT_FMN_2 = "https://images.unsplash.com/photo-1771456915291-58f0dee5b404?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwxfHxzaGllbGQlMjBlbWJsZW18ZW58MHx8fHwxNzc1MDcwOTU4fDA&ixlib=rb-4.1.0&q=85";
```

## User Experience

**Before (Broken):**
1. Setup Step 1: Formation Signs → User sees input fields
2. User gets confused about what URLs to provide
3. Setup Step 2: Room Configuration
4. Setup Step 3: Room Rates

**After (Fixed):**
1. Setup Step 1: Room Configuration → Directly configure rooms
2. Setup Step 2: Room Rates → Set daily rates
3. Formation signs are automatically configured with default images

## Note for Settings Screen

Formation sign URLs can still be customized later through the Settings page if needed. The setup wizard just doesn't ask for them anymore since defaults are sufficient for most users.

## Files Modified
- `/app/frontend/src/pages/SetupWizard.jsx` - Removed Formation Signs step

## Testing
✅ Linting passed
✅ Services running correctly
✅ Formation signs will be auto-configured during setup

---

**Status:** ✅ FIXED - Setup wizard now has 2 steps, formation signs pre-configured
