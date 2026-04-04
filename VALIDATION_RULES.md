# 📋 E-ARMS Validation Rules & Guidelines

Complete validation specifications for all forms in the E-ARMS application.

---

## 🔐 **BOOKING FORM VALIDATION**

### Guest Details
| Field | Rules | Error Message |
|-------|-------|---------------|
| **Guest Name** | Required, Min 2 chars, Max 100 chars, Letters & spaces only | "Guest name is required (2-100 characters)" |
| **Mobile Number** | Optional, If provided: 10 digits, starts with 6-9 | "Enter valid 10-digit Indian mobile number" |
| **Army Number** | Optional, Alphanumeric with hyphens, Max 20 chars | "Invalid army/service number format" |
| **Aadhaar Number** | Optional, If provided: Exactly 12 digits | "Aadhaar must be exactly 12 digits" |
| **Guest Rank** | Optional, Max 50 chars | - |
| **Guest Unit** | Optional, Max 100 chars | - |

### Room & Dates
| Field | Rules | Error Message |
|-------|-------|---------------|
| **Number of Rooms** | Required, Integer 1-10 | "Select 1-10 rooms" |
| **Check-in Date** | Required, >= Today | "Check-in must be today or future date" |
| **Check-out Date** | Required, > Check-in | "Check-out must be after check-in" |
| **Room Selection** | Required, Count = Number of Rooms | "Select exactly {n} room(s)" |
| **Nights** | Auto-calculated, If > 4: Show confirmation | "Booking exceeds 4 nights - OIC approval required" |

### Payment Details
| Field | Rules | Error Message |
|-------|-------|---------------|
| **Advance Paid** | Required, Numeric, >= 0, <= Total Amount | "Enter valid advance amount" |
| **Payment Mode** | Required, Enum: [cash, upi, bank_transfer, card] | "Select payment mode" |

**Cash:**
- Receipt/Transaction ID: Required, Max 50 chars

**UPI:**
- UPI ID OR Transaction ID: At least one required
- UPI ID format: `name@bank` pattern
- Transaction ID: Alphanumeric, Max 50 chars

**Bank Transfer:**
- Bank Name: Required, Max 100 chars
- Account Number: Required, 9-18 digits
- IFSC Code: Optional, 11 chars (4 letters + 7 alphanumeric)

**Card:**
- Transaction/Auth ID: Required, Max 50 chars

---

## 🏨 **CHECK-IN FORM VALIDATION**

### Personal Information
| Field | Rules | Error Message |
|-------|-------|---------------|
| **Phone Number** | Required, 10 digits, starts with 6-9 | "Enter valid 10-digit mobile number" |
| **Age** | Required, Integer 18-120 | "Enter valid age (18-120)" |
| **Sex** | Required, Enum: [Male, Female, Other] | "Select gender" |
| **Address** | Required, Min 10 chars, Max 500 chars | "Enter complete address (min 10 characters)" |
| **Identity Card Number** | Required, Alphanumeric, Max 50 chars | "Enter valid identity card number" |

### Service Details
| Field | Rules | Error Message |
|-------|-------|---------------|
| **Service Status** | Required, Enum: [Serving, Retired] | "Select service status" |
| **Type of Service** | Optional, Max 100 chars | - |
| **Command HQ** | Optional, Max 100 chars | - |

### Family Members
| Field | Rules | Error Message |
|-------|-------|---------------|
| **Wife Count** | Integer 0-1 | "Maximum 1 wife" |
| **Children Count** | Integer 0-10 | "Maximum 10 children" |
| **Family Member Name** | Required per member, Max 100 chars | "Enter family member name" |
| **Family Member Age** | Required per member, Integer 1-100 | "Enter valid age (1-100)" |
| **Family Member Relation** | Required per member, Max 50 chars | "Enter relation" |

### Accommodation
| Field | Rules | Error Message |
|-------|-------|---------------|
| **Extra Beds** | Integer 0-5 | "Maximum 5 extra beds" |

---

## 🚪 **CHECK-OUT FORM VALIDATION**

### Payment
| Field | Rules | Error Message |
|-------|-------|---------------|
| **Final Payment** | Required, Numeric >= 0 | "Enter valid payment amount" |
| **Payment Mode** | Required if balance > 0 | "Select payment mode" |

### Feedback (Required)
| Field | Rules | Error Message |
|-------|-------|---------------|
| **Overall Rating** | Required, Integer 1-5 | "Please rate your stay" |
| **Cleanliness** | Required, Integer 1-5 | "Rate cleanliness" |
| **Staff Behavior** | Required, Integer 1-5 | "Rate staff behavior" |
| **Food Quality** | Required, Integer 1-5 | "Rate food quality" |
| **Value for Money** | Required, Integer 1-5 | "Rate value for money" |
| **Comments (English)** | Optional, Max 1000 chars | - |
| **Comments (Hindi)** | Optional, Max 1000 chars | - |

---

## ❌ **CANCELLATION FORM VALIDATION**

| Field | Rules | Error Message |
|-------|-------|---------------|
| **Reason** | Required, Min 10 chars, Max 500 chars | "Enter cancellation reason (min 10 characters)" |
| **Refund Amount** | Auto-calculated, Read-only | - |

**Cancellation Rules:**
- > 7 days before check-in: 90% refund (10% cancellation charge)
- 3-7 days: 70% refund (30% cancellation charge)
- < 3 days: 50% refund (50% cancellation charge)
- On check-in day: No refund

---

## 🔍 **GUEST HISTORY LOOKUP VALIDATION**

| Field | Rules | Error Message |
|-------|-------|---------------|
| **Phone OR Army Number** | At least one required | "Enter phone number or army number" |
| **Phone Number** | If provided: 10 digits | "Enter valid phone number" |
| **Army Number** | If provided: Alphanumeric | "Enter valid army number" |

---

## 🏢 **ROOMS PAGE VALIDATION**

### Add/Edit Room
| Field | Rules | Error Message |
|-------|-------|---------------|
| **Room Number** | Required, Alphanumeric, Max 10 chars, Unique | "Room number already exists" |
| **Category** | Required, Enum: [Cat I, Cat II] | "Select room category" |
| **Status** | Required, Enum: [available, occupied, maintenance] | "Select room status" |
| **Floor** | Optional, Integer 0-10 | "Enter valid floor number" |
| **Beds** | Required, Integer 1-10 | "Enter number of beds (1-10)" |

---

## 👥 **STAFF PAGE VALIDATION**

### Add/Edit Staff
| Field | Rules | Error Message |
|-------|-------|---------------|
| **Name** | Required, Min 2 chars, Max 100 chars | "Enter staff name (2-100 characters)" |
| **Role** | Required, Max 50 chars | "Enter staff role" |
| **Phone** | Required, 10 digits, starts with 6-9 | "Enter valid 10-digit mobile number" |
| **Email** | Optional, Valid email format | "Enter valid email address" |
| **Joining Date** | Required, <= Today | "Joining date cannot be in future" |

---

## ⚙️ **SETTINGS PAGE VALIDATION**

### Room Rates
| Field | Rules | Error Message |
|-------|-------|---------------|
| **Cat I Rate** | Required, Numeric > 0, Max 10000 | "Enter valid Cat I rate" |
| **Cat II Rate** | Required, Numeric > 0, Max 10000 | "Enter valid Cat II rate" |
| **Def Civ Cat I Rate** | Required, Numeric > 0, Max 10000 | "Enter valid Def Civ Cat I rate" |
| **Def Civ Cat II Rate** | Required, Numeric > 0, Max 10000 | "Enter valid Def Civ Cat II rate" |

### License Fees
| Field | Rules | Error Message |
|-------|-------|---------------|
| **Cat I License Fee** | Required, Numeric >= 0, Max 1000 | "Enter valid license fee" |
| **Cat II License Fee** | Required, Numeric >= 0, Max 1000 | "Enter valid license fee" |
| **Def Civ License Fee** | Required, Numeric >= 0, Max 1000 | "Enter valid license fee" |

### Room Rent Breakdown
| Field | Rules | Error Message |
|-------|-------|---------------|
| **Room Rent** | Required, Numeric >= 0 | "Enter valid room rent" |
| **Auto-validate**: Room Rent + License Fee = Total Rate | - | "Room rent + license fee must equal total rate" |

### Default Settings
| Field | Rules | Error Message |
|-------|-------|---------------|
| **Default Advance Amount** | Required, Numeric > 0, Max 5000 | "Enter valid default advance (max ₹5000)" |

---

## 📊 **GENERAL VALIDATION PATTERNS**

### Common Formats
```javascript
// Phone (Indian)
/^[6-9]\d{9}$/

// Email
/^[^\s@]+@[^\s@]+\.[^\s@]+$/

// Aadhaar
/^\d{12}$/

// IFSC Code
/^[A-Z]{4}0[A-Z0-9]{6}$/

// UPI ID
/^[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}$/

// Army Number
/^[A-Z0-9\-\/]+$/

// Alphanumeric with special chars
/^[a-zA-Z0-9\s\-\.\,\/]+$/
```

### Input Sanitization
- **Trim whitespace** from all text inputs
- **Convert to uppercase** for ID fields (Army Number, IFSC, etc.)
- **Remove special characters** from numeric fields
- **Limit decimal places** to 2 for currency fields

---

## 🚨 **CRITICAL VALIDATIONS**

### Business Rules
1. **Double Booking Prevention**: Cannot book same room for overlapping dates
2. **Check-in Validation**: Can only check-in on or after booking check-in date
3. **Check-out Validation**: Can only check-out after check-in
4. **Payment Validation**: Total payments cannot exceed total amount
5. **Refund Validation**: Cannot mark refund as paid without confirmation
6. **4-Night Rule**: Bookings > 4 nights require OIC approval confirmation

### UI/UX Rules
1. **Disable past dates** in date pickers
2. **Auto-calculate** total amount, balance, nights
3. **Show field errors** on blur, not on every keystroke
4. **Clear form errors** when corrected
5. **Confirm before delete** operations
6. **Show loading states** during API calls
7. **Disable submit** while processing

---

## 📝 **IMPLEMENTATION CHECKLIST**

### For Each Form:
- [ ] Client-side validation (immediate feedback)
- [ ] Server-side validation (security)
- [ ] Error message display
- [ ] Required field indicators (*)
- [ ] Input masks/formatting
- [ ] Auto-trim whitespace
- [ ] Prevent form resubmission
- [ ] Show success/error toasts
- [ ] Clear form after successful submit
- [ ] Handle API errors gracefully

---

## 🎯 **RECOMMENDED LIBRARIES**

**Already in use:**
- React Hook Form (if needed for complex forms)
- Zod (schema validation)
- Yup (alternative to Zod)

**Current implementation:**
- Manual validation with toast messages ✓
- Input field level validation ✓

---

**Last Updated:** 2026-04-04
**Version:** 1.0
**Status:** Production Ready ✅
