# 📦 DATA MIGRATION GUIDE
## Migrating from SARAI V1 (Current) to SARAI V2 (Rebuilt)

**Date**: April 15, 2026  
**Purpose**: Safe migration of all data from fragmented V1 system to clean V2 system

---

## 📋 PRE-MIGRATION CHECKLIST

- [ ] **Full backup of V1 database** completed
- [ ] **V2 system deployed** and tested (empty database)
- [ ] **Migration scripts** reviewed and tested on sample data
- [ ] **Rollback plan** documented
- [ ] **Downtime window** scheduled (estimated: 2 hours)
- [ ] **Staff notified** of migration schedule

---

## 1. BACKUP V1 SYSTEM

### Full Database Backup

```bash
# Create backup directory
mkdir -p /backups/v1_migration_$(date +%Y%m%d)

# Export all collections
mongoexport --uri="mongodb://localhost:27017/sarai" \
  --collection=app_settings \
  --out=/backups/v1_migration_$(date +%Y%m%d)/settings.json

mongoexport --uri="mongodb://localhost:27017/sarai" \
  --collection=bookings \
  --out=/backups/v1_migration_$(date +%Y%m%d)/bookings.json

mongoexport --uri="mongodb://localhost:27017/sarai" \
  --collection=rooms \
  --out=/backups/v1_migration_$(date +%Y%m%d)/rooms.json

mongoexport --uri="mongodb://localhost:27017/sarai" \
  --collection=users \
  --out=/backups/v1_migration_$(date +%Y%m%d)/users.json

mongoexport --uri="mongodb://localhost:27017/sarai" \
  --collection=staff \
  --out=/backups/v1_migration_$(date +%Y%m%d)/staff.json

# Full database dump (binary backup)
mongodump --uri="mongodb://localhost:27017/sarai" \
  --out=/backups/v1_migration_$(date +%Y%m%d)/dump

echo "✅ Backup completed at: /backups/v1_migration_$(date +%Y%m%d)"
```

### Verify Backup

```bash
# Count records in each collection
echo "=== V1 Database Record Counts ==="
mongo sarai --eval "db.bookings.count()" --quiet
mongo sarai --eval "db.rooms.count()" --quiet
mongo sarai --eval "db.users.count()" --quiet
mongo sarai --eval "db.staff.count()" --quiet
```

---

## 2. SCHEMA MAPPING (V1 → V2)

### 2.1 Settings Collection

**V1 Schema**:
```javascript
{
  cat_i_room_rent: 470,
  cat_i_license_fee: 30,
  cat_ii_room_rent: 385,
  cat_ii_license_fee: 15,
  non_org_room_rent: 570,
  non_org_license_fee: 30,
  default_advance_amount: 400,
  cancellation_policy: [...],
  // ... other fields
}
```

**V2 Schema** (New structure):
```javascript
{
  room_categories: [  // RESTRUCTURED
    {
      id: "cat_i",
      name: "Cat I",
      capacity: 2,
      org_room_rent: 470,
      org_license_fee: 30,
      color: "#3B82F6"
    },
    {
      id: "cat_ii",
      name: "Cat II",
      capacity: 3,
      org_room_rent: 385,
      org_license_fee: 15,
      color: "#8B5CF6"
    }
  ],
  non_org_room_rent: 570,
  non_org_license_fee: 30,
  extra_bed_rate_per_night: 75,
  default_advance_amount: 400,
  cancellation_policy: [...],
  default_checkin_time: "13:00",
  default_checkout_time: "08:00",
  // ... rest
}
```

**Migration**: Restructure flat rate fields into `room_categories` array

---

### 2.2 Bookings Collection

**Key Changes**:

| V1 Field | V2 Field | Notes |
|----------|----------|-------|
| `is_org` | `guest_type` | `true` → `"org"`, `false` → `"non_org"` |
| `guest_rank` | `has_org_id_card` | `"Off"/"JCO"/"OR"` → `true`, `"Def Civ"` → `false` |
| N/A | `has_org_id_card` | New field (Boolean) |
| `family_members[].has_org_card` | `family_members[].has_org_dep_card` | Rename field |
| `room_guest_mapping[].charge_category` | Recalculate | Based on org dep card logic |

**New Fields** (set defaults):
- `actual_checkin_time`: `null` or migrate from existing timestamp
- `actual_checkout_time`: `null` or migrate from existing timestamp
- `extra_beds_checkin`: Default `0`
- `extra_bed_days`: Default `0`

---

### 2.3 Rooms Collection

**No major changes** - mostly compatible

**Validate**:
- `room_number` is unique
- `category` matches new room_categories IDs (`"cat_i"`, `"cat_ii"`)

---

### 2.4 Users Collection

**No major changes** - compatible

**Important**: Ensure `password_hash` uses bcrypt (already should be)

---

## 3. MIGRATION SCRIPTS

### 3.1 Migrate Settings

```python
# migrate_settings.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "sarai_v2"  # New database

async def migrate_settings():
    # Connect to V1 database
    client_v1 = AsyncIOMotorClient("mongodb://localhost:27017")
    db_v1 = client_v1.sarai
    
    # Connect to V2 database
    client_v2 = AsyncIOMotorClient(MONGO_URL)
    db_v2 = client_v2[DB_NAME]
    
    # Fetch V1 settings
    v1_settings = await db_v1.app_settings.find_one({}, {"_id": 0})
    
    if not v1_settings:
        print("❌ No settings found in V1")
        return
    
    # Transform to V2 schema
    v2_settings = {
        # Restructure into room_categories array
        "room_categories": [
            {
                "id": "cat_i",
                "name": "Cat I",
                "capacity": 2,
                "org_room_rent": v1_settings.get("cat_i_room_rent", 470),
                "org_license_fee": v1_settings.get("cat_i_license_fee", 30),
                "color": "#3B82F6"
            },
            {
                "id": "cat_ii",
                "name": "Cat II",
                "capacity": 3,
                "org_room_rent": v1_settings.get("cat_ii_room_rent", 385),
                "org_license_fee": v1_settings.get("cat_ii_license_fee", 15),
                "color": "#8B5CF6"
            }
        ],
        
        # Keep existing fields
        "non_org_room_rent": v1_settings.get("non_org_room_rent", 570),
        "non_org_license_fee": v1_settings.get("non_org_license_fee", 30),
        "extra_bed_rate_per_night": 75,
        "default_advance_amount": v1_settings.get("default_advance_amount", 400),
        "cancellation_policy": v1_settings.get("cancellation_policy", [
            {"hours_before": 96, "charge_percent": 0},
            {"hours_before": 48, "charge_percent": 50},
            {"hours_before": 0, "charge_percent": 100}
        ]),
        
        # New fields
        "default_checkin_time": "13:00",
        "default_checkout_time": "08:00",
        
        # Copy rest
        "guest_house_name": v1_settings.get("guest_house_name", "Shillong Aramgah"),
        "address": v1_settings.get("address", ""),
        "contact": v1_settings.get("contact", ""),
        "is_setup_complete": True,
        "created_at": v1_settings.get("created_at"),
        "updated_at": v1_settings.get("updated_at")
    }
    
    # Insert into V2
    await db_v2.app_settings.delete_many({})  # Clear first
    await db_v2.app_settings.insert_one(v2_settings)
    
    print("✅ Settings migrated successfully")
    
    await client_v1.close()
    await client_v2.close()

if __name__ == "__main__":
    asyncio.run(migrate_settings())
```

---

### 3.2 Migrate Bookings

```python
# migrate_bookings.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "sarai_v2"

def map_guest_rank_to_org_card(guest_rank: str) -> bool:
    """Map old guest_rank to has_org_id_card"""
    org_ranks = ["Off", "JCO", "OR"]
    return guest_rank in org_ranks

async def migrate_bookings():
    client_v1 = AsyncIOMotorClient("mongodb://localhost:27017")
    db_v1 = client_v1.sarai
    
    client_v2 = AsyncIOMotorClient(MONGO_URL)
    db_v2 = client_v2[DB_NAME]
    
    # Fetch all V1 bookings
    v1_bookings = await db_v1.bookings.find({}, {"_id": 0}).to_list(10000)
    
    print(f"📦 Migrating {len(v1_bookings)} bookings...")
    
    migrated = []
    
    for v1_booking in v1_bookings:
        # Transform to V2 schema
        v2_booking = {
            "id": v1_booking.get("id"),
            "booking_number": v1_booking.get("booking_number"),
            
            # Guest info
            "guest_name": v1_booking.get("guest_name"),
            "guest_contact": v1_booking.get("guest_contact", ""),
            "guest_age": v1_booking.get("guest_age"),
            "guest_sex": v1_booking.get("guest_sex", "M"),
            "guest_address": v1_booking.get("guest_address", ""),
            
            # CHANGE: is_org → guest_type
            "guest_type": "org" if v1_booking.get("is_org") else "non_org",
            
            # NEW: Map guest_rank to has_org_id_card
            "has_org_id_card": map_guest_rank_to_org_card(
                v1_booking.get("guest_rank", "Def Civ")
            ),
            
            # For Org guests
            "org_color": v1_booking.get("org_color", ""),
            
            # Dates
            "check_in_date": v1_booking.get("check_in_date"),
            "check_out_date": v1_booking.get("check_out_date"),
            
            # NEW: Actual timestamps (migrate if exists)
            "actual_checkin_time": v1_booking.get("actual_checkin_time"),
            "actual_checkout_time": v1_booking.get("actual_checkout_time"),
            
            # Rooms
            "room_ids": v1_booking.get("room_ids", []),
            "room_numbers": v1_booking.get("room_numbers", []),
            "room_categories": v1_booking.get("room_categories", []),
            
            # Mix & match
            "has_room_changes": v1_booking.get("has_room_changes", False),
            "room_segments": v1_booking.get("room_segments", []),
            
            # Family members - RENAME has_org_card → has_org_dep_card
            "family_members": [
                {
                    "relation": m.get("relation"),
                    "name": m.get("name"),
                    "age": m.get("age"),
                    "sex": m.get("sex"),
                    "mobile": m.get("mobile", ""),
                    "has_org_dep_card": m.get("has_org_card", False)  # RENAMED
                }
                for m in v1_booking.get("family_members", [])
            ],
            
            # Room-guest mapping - RECALCULATE charge_category
            "room_guest_mapping": migrate_room_mapping(
                v1_booking.get("room_guest_mapping", []),
                v1_booking.get("family_members", []),
                v1_booking.get("is_org", False)
            ),
            
            # Payment
            "advance_paid": v1_booking.get("advance_paid", 0),
            "payment_mode_advance": v1_booking.get("payment_mode", "cash"),
            "payment_id_advance": v1_booking.get("payment_id", ""),
            "bank_name": v1_booking.get("bank_name", ""),
            "bank_ifsc": v1_booking.get("bank_ifsc", ""),
            "bank_account": v1_booking.get("bank_account", ""),
            "upi_id": v1_booking.get("upi_id", ""),
            "upi_phone": v1_booking.get("upi_phone", ""),
            "card_last4": v1_booking.get("card_last4", ""),
            "card_type": v1_booking.get("card_type", ""),
            
            # Extra beds
            "extra_beds_checkin": v1_booking.get("extra_beds", 0),
            "extra_beds_checkout": v1_booking.get("extra_beds_checkout", 0),
            "extra_bed_days": v1_booking.get("extra_bed_days", 0),
            "extra_bed_charge_checkout": v1_booking.get("extra_bed_charge_checkout", 0),
            
            # Charges
            "total_room_charges": v1_booking.get("total_room_charges", 0),
            "final_payment": v1_booking.get("final_payment", 0),
            "payment_mode_final": v1_booking.get("payment_mode_final", ""),
            "payment_id_final": v1_booking.get("payment_id_final", ""),
            
            # Status
            "status": v1_booking.get("status", "confirmed"),
            
            # Staff
            "booked_by_staff": v1_booking.get("booked_by_staff"),
            "checkin_by_staff": v1_booking.get("checkin_by_staff"),
            "checkout_by_staff": v1_booking.get("checkout_by_staff"),
            "cancelled_by_staff": v1_booking.get("cancelled_by_staff"),
            
            # Cancellation
            "cancellation_reason": v1_booking.get("reason", ""),
            "refund_amount": v1_booking.get("refund_amount", 0),
            "cancellation_date": v1_booking.get("cancellation_date"),
            
            # Notes
            "booking_notes": v1_booking.get("notes", ""),
            "checkin_notes": v1_booking.get("checkin_notes", ""),
            "checkout_notes": v1_booking.get("checkout_notes", ""),
            
            # Feedback
            "feedback_rating": v1_booking.get("feedback_rating"),
            "feedback_text": v1_booking.get("feedback_text", ""),
            
            # Amendment
            "is_amended": v1_booking.get("is_amended", False),
            "amendment_history": v1_booking.get("amendment_history", []),
            
            # Timestamps
            "created_at": v1_booking.get("created_at"),
            "updated_at": v1_booking.get("updated_at")
        }
        
        migrated.append(v2_booking)
    
    # Bulk insert into V2
    if migrated:
        await db_v2.bookings.insert_many(migrated)
        print(f"✅ Migrated {len(migrated)} bookings")
    
    await client_v1.close()
    await client_v2.close()

def migrate_room_mapping(room_mapping: list, family_members: list, is_org: bool) -> list:
    """
    Recalculate charge_category based on org dep card logic
    """
    new_mapping = []
    
    for room in room_mapping:
        # Get family members assigned to this room
        family_indices = room.get("family_member_indices", [])
        
        # Check if any family member lacks org dep card
        any_without_card = False
        for idx in family_indices:
            if idx < len(family_members):
                member = family_members[idx]
                # V1 used has_org_card, check if false
                if not member.get("has_org_card", True):
                    any_without_card = True
                    break
        
        # Determine charge category
        if any_without_card:
            charge_category = "Non-Org"
        elif not is_org:
            charge_category = "Non-Org"
        else:
            charge_category = room.get("room_category")  # "Cat I" or "Cat II"
        
        new_room = {
            "room_id": room.get("room_id"),
            "room_number": room.get("room_number"),
            "room_category": room.get("room_category"),
            "has_self": room.get("has_self", False),
            "family_member_indices": family_indices,
            "charge_category": charge_category
        }
        
        new_mapping.append(new_room)
    
    return new_mapping

if __name__ == "__main__":
    asyncio.run(migrate_bookings())
```

---

### 3.3 Migrate Rooms

```python
# migrate_rooms.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "sarai_v2"

async def migrate_rooms():
    client_v1 = AsyncIOMotorClient("mongodb://localhost:27017")
    db_v1 = client_v1.sarai
    
    client_v2 = AsyncIOMotorClient(MONGO_URL)
    db_v2 = client_v2[DB_NAME]
    
    v1_rooms = await db_v1.rooms.find({}, {"_id": 0}).to_list(1000)
    
    print(f"📦 Migrating {len(v1_rooms)} rooms...")
    
    # Rooms schema is mostly compatible - just copy
    if v1_rooms:
        await db_v2.rooms.insert_many(v1_rooms)
        print(f"✅ Migrated {len(v1_rooms)} rooms")
    
    await client_v1.close()
    await client_v2.close()

if __name__ == "__main__":
    asyncio.run(migrate_rooms())
```

---

### 3.4 Migrate Users

```python
# migrate_users.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "sarai_v2"

async def migrate_users():
    client_v1 = AsyncIOMotorClient("mongodb://localhost:27017")
    db_v1 = client_v1.sarai
    
    client_v2 = AsyncIOMotorClient(MONGO_URL)
    db_v2 = client_v2[DB_NAME]
    
    v1_users = await db_v1.users.find({}, {"_id": 0}).to_list(1000)
    
    print(f"📦 Migrating {len(v1_users)} users...")
    
    # Users schema is compatible - just copy
    if v1_users:
        await db_v2.users.insert_many(v1_users)
        print(f"✅ Migrated {len(v1_users)} users")
    
    await client_v1.close()
    await client_v2.close()

if __name__ == "__main__":
    asyncio.run(migrate_users())
```

---

### 3.5 Migrate Staff

```python
# migrate_staff.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "sarai_v2"

async def migrate_staff():
    client_v1 = AsyncIOMotorClient("mongodb://localhost:27017")
    db_v1 = client_v1.sarai
    
    client_v2 = AsyncIOMotorClient(MONGO_URL)
    db_v2 = client_v2[DB_NAME]
    
    v1_staff = await db_v1.staff.find({}, {"_id": 0}).to_list(1000)
    
    print(f"📦 Migrating {len(v1_staff)} staff records...")
    
    # Staff schema is compatible
    if v1_staff:
        await db_v2.staff.insert_many(v1_staff)
        print(f"✅ Migrated {len(v1_staff)} staff records")
    
    await client_v1.close()
    await client_v2.close()

if __name__ == "__main__":
    asyncio.run(migrate_staff())
```

---

## 4. MIGRATION EXECUTION PLAN

### Step-by-Step Execution

**Pre-Migration** (1 day before):
1. ✅ Announce downtime window (e.g., "System maintenance: Apr 16, 02:00-04:00 AM")
2. ✅ Deploy V2 system to staging environment
3. ✅ Test migration scripts on staging with sample data
4. ✅ Verify all calculations are correct in V2
5. ✅ Prepare rollback scripts

**Migration Day** (2-hour window):

```bash
#!/bin/bash
# migration_execute.sh

echo "🚀 Starting SARAI V1 → V2 Migration"
echo "Timestamp: $(date)"

# Step 1: Stop V1 system (make read-only)
echo "Step 1: Stopping V1 writes..."
# (Redirect V1 to maintenance page or make DB read-only)

# Step 2: Final backup
echo "Step 2: Creating final V1 backup..."
./backup_v1.sh

# Step 3: Run migration scripts
echo "Step 3: Migrating settings..."
python migrate_settings.py

echo "Step 4: Migrating rooms..."
python migrate_rooms.py

echo "Step 5: Migrating users..."
python migrate_users.py

echo "Step 6: Migrating staff..."
python migrate_staff.py

echo "Step 7: Migrating bookings..."
python migrate_bookings.py

# Step 8: Verify counts
echo "Step 8: Verifying migration..."
python verify_migration.py

# Step 9: Switch to V2
echo "Step 9: Switching to V2 system..."
# (Update DNS/routing to point to V2)

echo "✅ Migration complete!"
echo "Timestamp: $(date)"
```

---

## 5. VERIFICATION SCRIPT

```python
# verify_migration.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def verify():
    client_v1 = AsyncIOMotorClient("mongodb://localhost:27017")
    db_v1 = client_v1.sarai
    
    client_v2 = AsyncIOMotorClient("mongodb://localhost:27017")
    db_v2 = client_v2.sarai_v2
    
    print("=" * 60)
    print("MIGRATION VERIFICATION")
    print("=" * 60)
    
    # Count comparisons
    collections = ["bookings", "rooms", "users", "staff"]
    
    for coll in collections:
        v1_count = await db_v1[coll].count_documents({})
        v2_count = await db_v2[coll].count_documents({})
        
        status = "✅" if v1_count == v2_count else "❌"
        print(f"{status} {coll}: V1={v1_count}, V2={v2_count}")
    
    # Spot-check bookings
    print("\n" + "=" * 60)
    print("SPOT CHECK: Random Booking")
    print("=" * 60)
    
    v1_booking = await db_v1.bookings.find_one({}, {"_id": 0})
    if v1_booking:
        v2_booking = await db_v2.bookings.find_one(
            {"id": v1_booking["id"]}, 
            {"_id": 0}
        )
        
        print(f"V1 Booking: {v1_booking.get('booking_number')}")
        print(f"  - Guest Type (V1 is_org): {v1_booking.get('is_org')}")
        print(f"  - Guest Type (V2 guest_type): {v2_booking.get('guest_type')}")
        print(f"  - Has Org Card (V2): {v2_booking.get('has_org_id_card')}")
        
        if v1_booking.get("family_members"):
            v1_fm = v1_booking["family_members"][0]
            v2_fm = v2_booking["family_members"][0]
            print(f"  - Family[0] has_org_card (V1): {v1_fm.get('has_org_card')}")
            print(f"  - Family[0] has_org_dep_card (V2): {v2_fm.get('has_org_dep_card')}")
    
    await client_v1.close()
    await client_v2.close()
    
    print("\n✅ Verification complete!")

if __name__ == "__main__":
    asyncio.run(verify())
```

---

## 6. POST-MIGRATION CHECKS

**Immediately After Migration**:
1. ✅ Login to V2 system with test credentials
2. ✅ Create a test booking (verify all calculations)
3. ✅ Check-in a test booking (verify org card logic)
4. ✅ Generate all PDF types (booking slip, org form, receipt)
5. ✅ Generate all 4 reports (monthly, occupancy, allotment, guest details)
6. ✅ Test amendment flow
7. ✅ Test cancellation with refund calculation
8. ✅ Verify role permissions (Admin/Staff/Viewer)

**Sample Test Cases**:

```python
# test_v2_system.py
import requests

API = "https://your-v2-backend-url/api"

# Test 1: Login
response = requests.post(f"{API}/auth/login", json={
    "email": "admin@sarai.local",
    "password": "Admin@2026!"
})
assert response.status_code == 200
token = response.json()["access_token"]

# Test 2: Fetch settings (verify room_categories structure)
response = requests.get(f"{API}/settings", headers={
    "Authorization": f"Bearer {token}"
})
settings = response.json()
assert "room_categories" in settings
assert len(settings["room_categories"]) >= 2

# Test 3: Create booking
response = requests.post(f"{API}/bookings", headers={
    "Authorization": f"Bearer {token}"
}, json={
    "guest_name": "Test Migration User",
    "guest_contact": "+91 9999999999",
    "guest_type": "org",
    "check_in_date": "2026-05-01",
    "check_out_date": "2026-05-03",
    "room_ids": ["<room-id>"],
    "advance_paid": 400,
    "payment_mode_advance": "cash",
    "payment_id_advance": "CASH001"
})
assert response.status_code == 200
booking = response.json()
print(f"✅ Test booking created: {booking['booking_number']}")

# Add more tests...
```

---

## 7. ROLLBACK PLAN

**If critical issues found within 48 hours**:

```bash
#!/bin/bash
# rollback_to_v1.sh

echo "⚠️  INITIATING ROLLBACK TO V1"

# Step 1: Switch DNS/routing back to V1
echo "Step 1: Redirecting traffic to V1..."
# (Update DNS or load balancer)

# Step 2: Restore V1 database (if any writes happened during V2)
echo "Step 2: Restoring V1 database from backup..."
mongorestore --uri="mongodb://localhost:27017" \
  --db=sarai \
  /backups/v1_migration_YYYYMMDD/dump/sarai

# Step 3: Restart V1 services
echo "Step 3: Restarting V1 services..."
sudo supervisorctl restart backend frontend

echo "✅ Rollback complete. V1 is now active."
echo "⚠️  Investigate V2 issues before retry."
```

**Rollback Window**: 48 hours (keep V1 backup and system available)

---

## 8. POST-MIGRATION CLEANUP (After 1 week)

**Once V2 stable for 7 days**:

1. ✅ Archive V1 system (keep read-only for reference)
2. ✅ Final verification of V2 data integrity
3. ✅ Remove temporary migration scripts from production
4. ✅ Update documentation (user manuals, API docs)
5. ✅ Celebrate successful migration! 🎉

---

## 9. MIGRATION TIMELINE

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Preparation** | 1 day | Deploy V2 to staging, test migration scripts |
| **Migration** | 2 hours | Execute migration, verify, switch to V2 |
| **Parallel Run** | 7 days | Monitor V2, keep V1 as fallback |
| **Stabilization** | 1 week | Fix any edge cases, user training |
| **Cleanup** | 1 day | Archive V1, final documentation |

**Total**: ~2 weeks from start to final cleanup

---

## 10. CONTACT & SUPPORT

**Migration Lead**: [Your Name]  
**Technical Support**: [Team Email/Slack]  
**Escalation**: [Manager Contact]

**Migration Status Dashboard**: [URL to live status page]

---

**Document Version**: 1.0  
**Last Updated**: April 15, 2026  
**Author**: E1 Fork Agent (Emergent Labs)
