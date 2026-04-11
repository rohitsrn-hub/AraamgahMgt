from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum

# Import backup services
from services import backup_service, restore_service, scheduler_service
from services.migration_service import run_startup_migrations

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="SARAI API", description="Shillong Aramgah Room Automation Interface")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============= VALIDATION HELPERS =============
import re

def validate_ifsc(ifsc: str) -> bool:
    """Validate IFSC code format: 4 letters + 0 + 6 alphanumeric"""
    if not ifsc:
        return True  # Optional field
    return bool(re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', ifsc))

def validate_indian_mobile(mobile: str) -> bool:
    """Validate Indian mobile number (10 digits starting with 6-9)"""
    if not mobile:
        return True  # Optional field
    cleaned = mobile.replace(" ", "").replace("+91", "").replace("-", "")
    return bool(re.match(r'^[6-9]\d{9}$', cleaned))

def normalize_uppercase_fields(data: dict) -> dict:
    """Force uppercase on ID fields (bank_ifsc, org_id for family members)"""
    if "bank_ifsc" in data and data["bank_ifsc"]:
        data["bank_ifsc"] = data["bank_ifsc"].upper()
    # For family members - normalize org_id (formerly dependent_id)
    if "family_members" in data:
        for member in data["family_members"]:
            if "org_id" in member and member["org_id"]:
                member["org_id"] = member["org_id"].upper()
    return data

# ============= HELPER FUNCTIONS =============
async def generate_booking_number():
    """Generate sequential booking number starting from BK0001"""
    # Get the latest booking number
    latest_booking = await db.bookings.find_one(
        {},
        {"_id": 0, "booking_number": 1},
        sort=[("created_at", -1)]
    )
    
    if not latest_booking or not latest_booking.get("booking_number"):
        return "BK0001"
    
    try:
        # Extract the number from the booking number (e.g., BK0001 -> 1)
        current_number = int(latest_booking["booking_number"].replace("BK", ""))
        next_number = current_number + 1
        # Format with leading zeros (e.g., 1 -> BK0001)
        return f"BK{next_number:04d}"
    except (ValueError, KeyError):
        # Fallback to counting all bookings if format is unexpected
        count = await db.bookings.count_documents({})
        return f"BK{count + 1:04d}"

# ============= ENUMS =============
class RoomCategory(str, Enum):
    CAT_I = "Cat I"
    CAT_II = "Cat II"

class RoomStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"

class BookingStatus(str, Enum):
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"

class StaffType(str, Enum):
    ARMY = "Army"
    CIVILIAN = "Civilian"

class RefundStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"

# ============= MODELS =============

# App Settings
class CancellationSlab(BaseModel):
    hours_before: int  # Hours before check-in
    charge_percent: float  # Percentage of advance to deduct

# Color categories for Organization guests
COLOR_OPTIONS = [
    "Red", "Green", "Brown", "Orange", "Yellow", 
    "Violet", "Black", "Blue", "White", "Light Blue"
]

class AppSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_setup_complete: bool = False
    fmn_sign_1_url: Optional[str] = None
    fmn_sign_2_url: Optional[str] = None
    cat_i_rate: float = 500.0
    cat_ii_rate: float = 400.0
    def_civ_cat_i_rate: float = 600.0
    def_civ_cat_ii_rate: float = 600.0
    cat_i_room_rent: float = 470.0
    cat_i_license_fee: float = 30.0
    cat_ii_room_rent: float = 385.0
    cat_ii_license_fee: float = 15.0
    def_civ_room_rent: float = 570.0
    def_civ_license_fee: float = 30.0
    cat_i_rooms_count: int = 6
    cat_ii_rooms_count: int = 9
    default_advance_amount: float = 400.0
    colors: List[str] = Field(default_factory=lambda: COLOR_OPTIONS.copy())
    cancellation_policy: List[dict] = Field(default_factory=lambda: [
        {"hours_before": 96, "charge_percent": 0},
        {"hours_before": 48, "charge_percent": 50},
        {"hours_before": 0, "charge_percent": 100}
    ])
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # P4: Dynamic room categories
    room_categories: List[dict] = Field(default_factory=lambda: [
        {
            "id": "cat-i",
            "name": "Cat I",
            "rate": 500.0,
            "def_civ_rate": 600.0,
            "room_count": 6,
            "prefix": "C1",
            "capacity": 2  # Number of people per room
        },
        {
            "id": "cat-ii",
            "name": "Cat II",
            "rate": 400.0,
            "def_civ_rate": 600.0,
            "room_count": 9,
            "prefix": "C2",
            "capacity": 2
        }
    ])

class AppSettingsUpdate(BaseModel):
    fmn_sign_1_url: Optional[str] = None
    fmn_sign_2_url: Optional[str] = None
    cat_i_rate: Optional[float] = None
    cat_ii_rate: Optional[float] = None
    def_civ_cat_i_rate: Optional[float] = None
    def_civ_cat_ii_rate: Optional[float] = None
    cat_i_room_rent: Optional[float] = None
    cat_i_license_fee: Optional[float] = None
    cat_ii_room_rent: Optional[float] = None
    cat_ii_license_fee: Optional[float] = None
    def_civ_room_rent: Optional[float] = None
    def_civ_license_fee: Optional[float] = None
    cat_i_rooms_count: Optional[int] = None
    cat_ii_rooms_count: Optional[int] = None
    default_advance_amount: Optional[float] = None
    colors: Optional[List[str]] = None
    cancellation_policy: Optional[List[dict]] = None

class SetupRequest(BaseModel):
    fmn_sign_1_url: Optional[str] = None
    fmn_sign_2_url: Optional[str] = None
    cat_i_rate: float = 500.0
    cat_ii_rate: float = 400.0
    def_civ_cat_i_rate: float = 600.0
    def_civ_cat_ii_rate: float = 600.0
    cat_i_room_rent: float = 470.0
    cat_i_license_fee: float = 30.0
    cat_ii_room_rent: float = 385.0
    cat_ii_license_fee: float = 15.0
    def_civ_room_rent: float = 570.0
    def_civ_license_fee: float = 30.0
    cat_i_rooms_count: int = 6
    cat_ii_rooms_count: int = 9
    default_advance_amount: float = 400.0
    colors: Optional[List[str]] = None
    cancellation_policy: Optional[List[dict]] = None

# Room
class Room(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_number: str
    category: RoomCategory
    status: RoomStatus = RoomStatus.AVAILABLE
    floor: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RoomCreate(BaseModel):
    room_number: str
    category: RoomCategory
    floor: int = 1

class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    category: Optional[RoomCategory] = None
    status: Optional[RoomStatus] = None
    floor: Optional[int] = None

# Guest
class Guest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    contact_number: Optional[str] = None
    id_proof_type: Optional[str] = None
    id_proof_number: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GuestCreate(BaseModel):
    name: str
    contact_number: str
    id_proof_type: Optional[str] = None
    id_proof_number: Optional[str] = None
    address: Optional[str] = None

# Booking
class Booking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    booking_number: str  # Will be set manually using generate_booking_number()
    guest_id: str
    guest_name: str
    guest_contact: Optional[str] = None
    # NEW: Organization classification (replaces rank/command system)
    is_org: bool = False  # True = Organization personnel, False = Non-Org
    org_color: Optional[str] = None  # Color category for Org guests (Red, Green, etc.)
    room_ids: List[str] = []
    room_numbers: List[str] = []
    room_categories: List[str] = []
    # NEW: Mix & Match Rooms - per-night room assignments
    room_segments: Optional[List[dict]] = None  # [{"night_date": "2026-04-11", "rooms": [...]}]
    has_room_changes: bool = False  # Flag indicating if guest changes rooms during stay
    num_guests: int = 1
    num_rooms: int = 1
    check_in_date: str  # ISO date string
    check_out_date: str  # ISO date string
    actual_check_in: Optional[str] = None
    actual_check_out: Optional[str] = None
    status: BookingStatus = BookingStatus.CONFIRMED
    total_amount: float
    advance_paid: float = 0.0
    balance_amount: float = 0.0
    payment_mode: Optional[str] = None
    payment_id: Optional[str] = None
    bank_details: Optional[str] = None
    upi_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_account: Optional[str] = None
    upi_id: Optional[str] = None
    upi_phone: Optional[str] = None
    extra_beds: int = 0
    extra_bed_charge: float = 0.0
    extra_beds_checkout: Optional[int] = 0  # NEW: Extra beds added during stay
    extra_bed_days: Optional[int] = 0  # NEW: Days extra beds used during stay
    extra_bed_charge_checkout: Optional[float] = 0.0  # NEW: Charge for extra beds during stay
    final_payment: Optional[float] = 0.0  # NEW: Final payment amount at checkout
    guest_age: Optional[int] = None
    guest_sex: Optional[str] = None
    guest_address: Optional[str] = None
    aadhaar_number: Optional[str] = None
    wife_count: int = 0
    children_count: int = 0
    family_members: List[dict] = Field(default_factory=list)
    room_guest_mapping: List[dict] = Field(default_factory=list)  # Room-wise guest assignments
    room_rent_total: float = 0.0
    license_fee_total: float = 0.0
    notes: Optional[str] = None
    amendment_log: List[dict] = Field(default_factory=list)  # Track amendments
    checked_in_by: Optional[str] = None
    checked_out_by: Optional[str] = None
    total_members: Optional[int] = None  # NEW: For party composition
    member_ages: Optional[List[int]] = None  # NEW: Ages of all members
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BookingCreate(BaseModel):
    guest_name: str
    guest_contact: Optional[str] = None
    # NEW: Organization classification
    is_org: bool = False  # Organization personnel or Non-Org
    org_color: Optional[str] = None  # Color category (only for Org guests)
    room_ids: List[str]
    # NEW: Mix & Match Rooms support
    room_segments: Optional[List[dict]] = None  # Alternative to room_ids for segmented bookings
    num_guests: int = 1
    num_rooms: int = 1
    check_in_date: str
    check_out_date: str
    advance_paid: float = 0.0
    payment_mode: Optional[str] = None
    payment_id: Optional[str] = None
    bank_details: Optional[str] = None
    upi_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_account: Optional[str] = None
    upi_id: Optional[str] = None
    upi_phone: Optional[str] = None
    guest_age: Optional[int] = None
    guest_sex: Optional[str] = None
    guest_address: Optional[str] = None
    aadhaar_number: Optional[str] = None
    wife_count: int = 0
    children_count: int = 0
    family_members: List[dict] = Field(default_factory=list)
    notes: Optional[str] = None
    total_members: Optional[int] = None  # NEW: For party composition
    member_ages: Optional[List[int]] = None  # NEW: Ages of all members

class CheckInRequest(BaseModel):
    booking_id: str
    staff_id: str
    extra_beds: int = 0
    notes: Optional[str] = None
    # Personal details captured at check-in
    guest_contact: Optional[str] = None
    guest_age: Optional[int] = None
    guest_sex: Optional[str] = None
    guest_address: Optional[str] = None
    # Organization color (if not set during booking)
    org_color: Optional[str] = None
    bank_name: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_account: Optional[str] = None
    upi_id: Optional[str] = None
    upi_phone: Optional[str] = None
    family_members: List[dict] = Field(default_factory=list)
    room_guest_mapping: List[dict] = Field(default_factory=list)  # NEW: Room-wise guest assignments

class CheckOutRequest(BaseModel):
    booking_id: str
    staff_id: str
    final_payment: float = 0.0
    payment_mode: Optional[str] = None
    notes: Optional[str] = None
    # Organization color (to be filled at checkout if Org guest)
    org_color: Optional[str] = None
    # Extra bed fields for actual usage at checkout
    extra_beds_checkout: Optional[int] = 0
    extra_bed_days: Optional[int] = 0

class CancelBookingRequest(BaseModel):
    booking_id: str
    reason: Optional[str] = None

class AmendBookingRequest(BaseModel):
    booking_id: str
    # Amendable fields
    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None
    room_ids: Optional[List[str]] = None
    num_rooms: Optional[int] = None
    total_members: Optional[int] = None
    member_ages: Optional[List[int]] = None
    # Payment adjustment
    additional_advance: float = 0.0
    payment_mode: Optional[str] = None
    payment_id: Optional[str] = None
    bank_name: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_account: Optional[str] = None
    upi_id: Optional[str] = None
    upi_phone: Optional[str] = None
    # Amendment metadata
    amendment_reason: Optional[str] = None

    refund_amount: float = 0.0

# Staff
class Staff(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    staff_type: StaffType
    designation: Optional[str] = None
    contact_number: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StaffCreate(BaseModel):
    name: str
    staff_type: StaffType
    designation: Optional[str] = None
    contact_number: Optional[str] = None

class StaffUpdate(BaseModel):
    name: Optional[str] = None
    staff_type: Optional[StaffType] = None
    designation: Optional[str] = None
    contact_number: Optional[str] = None
    is_active: Optional[bool] = None

# Refund
class Refund(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    booking_id: str
    booking_number: str
    guest_name: str
    amount: float
    status: RefundStatus = RefundStatus.PENDING
    bank_details: Optional[str] = None
    upi_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_account: Optional[str] = None
    upi_id: Optional[str] = None
    upi_phone: Optional[str] = None
    transaction_ref: Optional[str] = None
    refund_date: Optional[str] = None
    processed_at: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RefundUpdate(BaseModel):
    status: RefundStatus
    transaction_ref: Optional[str] = None
    refund_date: Optional[str] = None
    notes: Optional[str] = None

# Toiletry
class ToiletryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    quantity: int = 0
    unit: str = "pcs"
    min_stock_level: int = 10
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ToiletryItemCreate(BaseModel):
    name: str
    quantity: int = 0
    unit: str = "pcs"
    min_stock_level: int = 10

class ToiletryItemUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    min_stock_level: Optional[int] = None

class ToiletryTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str
    item_name: str
    transaction_type: str  # "stock_in" or "consumption"
    quantity: int
    booking_id: Optional[str] = None
    room_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StockInRequest(BaseModel):
    item_id: str
    quantity: int
    notes: Optional[str] = None

class ConsumptionRequest(BaseModel):
    item_id: str
    quantity: int
    booking_id: Optional[str] = None
    room_number: Optional[str] = None
    notes: Optional[str] = None

# Payment tracking
class Payment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    booking_id: str
    booking_number: str
    amount: float
    payment_type: str  # "advance", "final", "refund"
    payment_mode: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============= HELPER FUNCTIONS =============

def serialize_datetime(obj):
    """Convert datetime to ISO string for MongoDB storage"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def serialize_doc(doc: dict) -> dict:
    """Serialize document for MongoDB storage"""
    result = {}
    for k, v in doc.items():
        if k == '_id':  # Skip MongoDB ObjectId
            continue
        if isinstance(v, datetime):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result

def serialize_response(doc: dict) -> dict:
    """Serialize document for API response, excluding _id"""
    if doc is None:
        return None
    result = {}
    for k, v in doc.items():
        if k == '_id':  # Skip MongoDB ObjectId
            continue
        result[k] = v
    return result

async def get_room_rate(category: RoomCategory, is_org: bool = True, is_license_fee: bool = False) -> float:
    """
    Get room rate from settings based on Org/Non-Org classification
    
    Args:
        category: Room category (CAT_I or CAT_II)
        is_org: True for Organization personnel, False for Non-Org
        is_license_fee: If True, return license fee instead of room rent
    
    Returns:
        float: Room rent or license fee amount
    """
    settings = await db.app_settings.find_one({}, {"_id": 0})
    
    if settings:
        if is_org:
            # Organization personnel - use Cat I or Cat II rates
            if category == RoomCategory.CAT_I:
                if is_license_fee:
                    return settings.get("cat_i_license_fee", 30.0)
                return settings.get("cat_i_room_rent", 470.0)
            else:  # CAT_II
                if is_license_fee:
                    return settings.get("cat_ii_license_fee", 15.0)
                return settings.get("cat_ii_room_rent", 385.0)
        else:
            # Non-Org - use Non-Org rates
            if is_license_fee:
                return settings.get("non_org_license_fee", 30.0)
            return settings.get("non_org_room_rent", 570.0)
    
    # Fallback defaults if settings not found
    if is_org:
        if category == RoomCategory.CAT_I:
            return 30.0 if is_license_fee else 470.0
        else:
            return 15.0 if is_license_fee else 385.0
    else:
        return 30.0 if is_license_fee else 570.0

def calculate_nights(check_in: str, check_out: str) -> int:
    """Calculate number of nights between dates"""
    try:
        ci = datetime.fromisoformat(check_in.replace('Z', '+00:00'))
        co = datetime.fromisoformat(check_out.replace('Z', '+00:00'))
        return max(1, (co - ci).days)
    except (ValueError, TypeError):
        return 1

# ============= API ROUTES =============

# Health check
@api_router.get("/")
async def root():
    return {"message": "SARAI API is running", "version": "1.0.0"}

# ============= APP SETTINGS =============

@api_router.get("/settings")
async def get_settings():
    settings = await db.app_settings.find_one({}, {"_id": 0})
    if not settings:
        # Return default settings
        default = AppSettings()
        return default.model_dump()
    return settings

@api_router.post("/settings/setup")
async def complete_setup(request: SetupRequest):
    """Complete first-time setup"""
    existing = await db.app_settings.find_one({})
    
    # Default cancellation policy (hours-based)
    # >96 hours (4 days): 100% refund
    # 48-96 hours (2-4 days): 50% refund
    # <48 hours (2 days): 0% refund
    default_cancellation_policy = [
        {"hours_before": 96, "charge_percent": 0},   # More than 96 hours: 0% charge (100% refund)
        {"hours_before": 48, "charge_percent": 50},  # 48-96 hours: 50% charge (50% refund)
        {"hours_before": 0, "charge_percent": 100}   # Less than 48 hours: 100% charge (0% refund)
    ]
    
    settings = AppSettings(
        is_setup_complete=True,
        fmn_sign_1_url=request.fmn_sign_1_url,
        fmn_sign_2_url=request.fmn_sign_2_url,
        cat_i_rate=request.cat_i_rate,
        cat_ii_rate=request.cat_ii_rate,
        def_civ_cat_i_rate=request.def_civ_cat_i_rate,
        def_civ_cat_ii_rate=request.def_civ_cat_ii_rate,
        cat_i_room_rent=request.cat_i_room_rent,
        cat_i_license_fee=request.cat_i_license_fee,
        cat_ii_room_rent=request.cat_ii_room_rent,
        cat_ii_license_fee=request.cat_ii_license_fee,
        def_civ_room_rent=request.def_civ_room_rent,
        def_civ_license_fee=request.def_civ_license_fee,
        cat_i_rooms_count=request.cat_i_rooms_count,
        cat_ii_rooms_count=request.cat_ii_rooms_count,
        default_advance_amount=request.default_advance_amount,
        colors=request.colors or COLOR_OPTIONS.copy(),
        cancellation_policy=request.cancellation_policy or default_cancellation_policy
    )
    
    doc = serialize_doc(settings.model_dump())
    
    if existing:
        await db.app_settings.update_one({}, {"$set": doc})
    else:
        await db.app_settings.insert_one(doc)
    
    # Create rooms based on configuration
    await db.rooms.delete_many({})  # Clear existing rooms
    
    # Create Cat I rooms (C1-01 to C1-06)
    for i in range(1, request.cat_i_rooms_count + 1):
        room = Room(
            room_number=f"C1-{i:02d}",
            category=RoomCategory.CAT_I,
            floor=1 if i <= 3 else 2
        )
        await db.rooms.insert_one(serialize_doc(room.model_dump()))
    
    # Create Cat II rooms (continuing from Cat I count, e.g., C2-07 to C2-15)
    start_num = request.cat_i_rooms_count + 1
    for i in range(request.cat_ii_rooms_count):
        room_num = start_num + i
        room = Room(
            room_number=f"C2-{room_num:02d}",
            category=RoomCategory.CAT_II,
            floor=1 if (i + 1) <= 5 else 2
        )
        await db.rooms.insert_one(serialize_doc(room.model_dump()))
    
    # Fetch the updated settings without _id
    settings_response = await db.app_settings.find_one({}, {"_id": 0})
    
    return {"message": "Setup completed successfully", "settings": settings_response}

@api_router.put("/settings")
async def update_settings(request: AppSettingsUpdate):
    """Update app settings"""
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.app_settings.update_one({}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    return await get_settings()

@api_router.post("/settings/reset-setup")
async def reset_setup():
    """P3: Reset is_setup_complete flag to show setup wizard again"""
    result = await db.app_settings.update_one({}, {"$set": {"is_setup_complete": False}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    return {"message": "Setup reset successfully. Please reload the page."}

@api_router.put("/settings/categories")
async def update_room_categories(categories: List[dict]):
    """P4: Update room categories configuration"""
    # Validate categories
    for cat in categories:
        if not all(k in cat for k in ["id", "name", "rate", "def_civ_rate", "room_count", "prefix", "capacity"]):
            raise HTTPException(status_code=400, detail="Invalid category structure - missing required fields")
    
    # Update settings
    result = await db.app_settings.update_one(
        {},
        {"$set": {
            "room_categories": categories,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    return {"message": "Room categories updated successfully", "categories": categories}

# ============= ROOMS =============

@api_router.get("/rooms", response_model=List[dict])
async def get_rooms(category: Optional[RoomCategory] = None, status: Optional[RoomStatus] = None):
    query = {}
    if category:
        query["category"] = category.value
    if status:
        query["status"] = status.value
    
    rooms = await db.rooms.find(query, {"_id": 0}).to_list(100)
    return rooms

@api_router.get("/rooms/available")
async def get_available_rooms(
    check_in: str = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: str = Query(..., description="Check-out date (YYYY-MM-DD)"),
    exclude_booking_id: Optional[str] = Query(None, description="Booking ID to exclude from conflict check")
):
    """Get available rooms for given date range, optionally excluding a specific booking
    
    Booking Time Logic:
    - Check-in: 1300h (1 PM) on check-in date
    - Check-out: 0800h (8 AM) on check-out date  
    - Room Available: 0900h (9 AM) on check-out date
    
    Availability Logic:
    - Room is occupied: check-in date through check-out date (inclusive)
    - Room becomes available: FROM check-out date for NEW bookings
    - Example: Booking 8-Apr to 9-Apr → Room occupied 8-Apr and 9-Apr until 08:00
               → Room available for NEW booking starting 9-Apr (from 13:00)
    """
    # Get all rooms
    all_rooms = await db.rooms.find({}, {"_id": 0}).to_list(100)
    
    # Get bookings that overlap with requested dates
    # OLD LOGIC: check_out_date > check_in (excludes same-day availability)
    # NEW LOGIC: check_out_date >= check_in (allows booking on check-out date)
    # However, we need to think about this carefully:
    # - Existing booking: 8-Apr to 9-Apr (guest checks out at 08:00 on 9-Apr)
    # - New booking request: 9-Apr to 10-Apr (guest checks in at 13:00 on 9-Apr)
    # - These should NOT conflict because check-out is 08:00 and check-in is 13:00
    # So we keep the original logic where check_out_date > check_in
    # This way, a booking ending on 9-Apr does NOT block a booking starting on 9-Apr
    booking_query = {
        "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
        "check_in_date": {"$lt": check_out},
        "check_out_date": {"$gt": check_in}
    }
    
    # Exclude the specified booking if provided (for room modification during check-in)
    if exclude_booking_id:
        booking_query["id"] = {"$ne": exclude_booking_id}
    
    overlapping_bookings = await db.bookings.find(booking_query, {"_id": 0}).to_list(1000)
    
    # Collect all booked room IDs
    booked_room_ids = set()
    for b in overlapping_bookings:
        for rid in b.get("room_ids", []):
            booked_room_ids.add(rid)
        if b.get("room_id"):
            booked_room_ids.add(b["room_id"])
    
    # Filter available rooms (not booked and not under maintenance)
    available_rooms = [
        r for r in all_rooms 
        if r["id"] not in booked_room_ids and r["status"] != RoomStatus.MAINTENANCE.value
    ]
    
    return available_rooms

@api_router.get("/rooms/{room_id}")
async def get_room(room_id: str):
    room = await db.rooms.find_one({"id": room_id}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@api_router.post("/rooms")
async def create_room(room: RoomCreate):
    room_obj = Room(**room.model_dump())
    doc = serialize_doc(room_obj.model_dump())
    await db.rooms.insert_one(doc)
    # Return the created room by fetching it back without _id
    created_room = await db.rooms.find_one({"id": doc["id"]}, {"_id": 0})
    return created_room

@api_router.put("/rooms/{room_id}")
async def update_room(room_id: str, update: RoomUpdate):
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    result = await db.rooms.update_one({"id": room_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return await get_room(room_id)

@api_router.delete("/rooms/{room_id}")
async def delete_room(room_id: str):
    result = await db.rooms.delete_one({"id": room_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"message": "Room deleted successfully"}

@api_router.post("/rooms/find-optimal-combination")
async def find_optimal_room_combination(
    check_in: str = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: str = Query(..., description="Check-out date (YYYY-MM-DD)"),
    num_rooms: int = Query(..., ge=1, description="Number of rooms needed per night"),
    exclude_booking_id: Optional[str] = Query(None, description="Booking ID to exclude from conflict check")
):
    """
    Find optimal room combination for date range when single rooms aren't available for entire duration.
    
    Algorithm:
    1. For each night, find available rooms
    2. Prioritize rooms available for longest consecutive periods
    3. Minimize total room changes during stay
    4. Return structured segments with room assignments per night
    
    Example Response:
    {
        "optimal_combination": [
            {
                "night_date": "2026-04-11",
                "rooms": [
                    {"id": "...", "room_number": "C1-01", "category": "Cat I"},
                    {"id": "...", "room_number": "C1-02", "category": "Cat I"}
                ]
            },
            ...
        ],
        "total_room_changes": 2,
        "availability_status": "full",
        "message": "Optimal combination found with minimal room changes"
    }
    """
    from datetime import datetime, timedelta
    
    # Parse dates
    start_date = datetime.strptime(check_in, "%Y-%m-%d").date()
    end_date = datetime.strptime(check_out, "%Y-%m-%d").date()
    nights = (end_date - start_date).days
    
    if nights <= 0:
        raise HTTPException(status_code=400, detail="Check-out must be after check-in")
    
    # Get all rooms
    all_rooms = await db.rooms.find(
        {"status": {"$ne": RoomStatus.MAINTENANCE.value}}, 
        {"_id": 0}
    ).to_list(100)
    
    # Build availability map for each night
    # night_availability[night_date] = [available_room_objects]
    night_availability = {}
    
    for i in range(nights):
        night_date = start_date + timedelta(days=i)
        night_date_str = night_date.strftime("%Y-%m-%d")
        
        # Get bookings that overlap with this specific night
        booking_query = {
            "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
            "check_in_date": {"$lte": night_date_str},
            "check_out_date": {"$gt": night_date_str}
        }
        
        if exclude_booking_id:
            booking_query["id"] = {"$ne": exclude_booking_id}
        
        overlapping_bookings = await db.bookings.find(booking_query, {"_id": 0}).to_list(1000)
        
        # Collect booked room IDs for this night
        booked_room_ids = set()
        for b in overlapping_bookings:
            for rid in b.get("room_ids", []):
                booked_room_ids.add(rid)
            if b.get("room_id"):
                booked_room_ids.add(b["room_id"])
        
        # Available rooms for this night
        available_for_night = [
            r for r in all_rooms 
            if r["id"] not in booked_room_ids
        ]
        
        night_availability[night_date_str] = available_for_night
    
    # Check if we have enough rooms for ANY night
    min_available = min(len(rooms) for rooms in night_availability.values())
    if min_available < num_rooms:
        return {
            "optimal_combination": [],
            "total_room_changes": None,
            "availability_status": "insufficient",
            "message": f"Insufficient rooms. Need {num_rooms} rooms per night, but only {min_available} available on some nights.",
            "night_availability_summary": {
                date: len(rooms) for date, rooms in night_availability.items()
            }
        }
    
    # OPTIMIZATION ALGORITHM: Find room combination that minimizes changes
    # Strategy: Greedy approach - find rooms available for longest consecutive periods
    
    # Calculate "availability spans" for each room
    # span[room_id] = list of consecutive night ranges where room is available
    room_spans = {}
    for room in all_rooms:
        room_id = room["id"]
        consecutive_nights = []
        current_span = []
        
        for i in range(nights):
            night_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            available_rooms_tonight = night_availability[night_date]
            
            if any(r["id"] == room_id for r in available_rooms_tonight):
                current_span.append(night_date)
            else:
                if current_span:
                    consecutive_nights.append(current_span)
                    current_span = []
        
        if current_span:
            consecutive_nights.append(current_span)
        
        if consecutive_nights:
            room_spans[room_id] = {
                "room": room,
                "spans": consecutive_nights,
                "total_nights": sum(len(span) for span in consecutive_nights),
                "max_consecutive": max(len(span) for span in consecutive_nights)
            }
    
    # Greedy allocation: Pick rooms with longest availability first
    # Sort rooms by max consecutive nights (descending)
    sorted_rooms = sorted(
        room_spans.items(),
        key=lambda x: (x[1]["max_consecutive"], x[1]["total_nights"]),
        reverse=True
    )
    
    # Allocate rooms greedily
    allocated_segments = {night: [] for night in night_availability.keys()}
    used_rooms_per_night = {night: set() for night in night_availability.keys()}
    
    for _ in range(num_rooms):
        # For each room slot, find the best room that hasn't been allocated yet
        best_room = None
        best_coverage = 0
        
        for room_id, span_data in sorted_rooms:
            # Check how many nights this room can cover without being already allocated
            coverage = 0
            for span in span_data["spans"]:
                for night in span:
                    if room_id not in used_rooms_per_night[night] and len(allocated_segments[night]) < num_rooms:
                        coverage += 1
            
            if coverage > best_coverage:
                best_coverage = coverage
                best_room = (room_id, span_data)
        
        if best_room:
            room_id, span_data = best_room
            room_obj = span_data["room"]
            
            # Allocate this room to all nights where it's available and not yet allocated
            for span in span_data["spans"]:
                for night in span:
                    if room_id not in used_rooms_per_night[night] and len(allocated_segments[night]) < num_rooms:
                        allocated_segments[night].append({
                            "id": room_obj["id"],
                            "room_number": room_obj["room_number"],
                            "category": room_obj["category"]
                        })
                        used_rooms_per_night[night].add(room_id)
    
    # Build final segments structure
    optimal_combination = []
    for i in range(nights):
        night_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        optimal_combination.append({
            "night_date": night_date,
            "rooms": allocated_segments[night_date]
        })
    
    # Calculate total room changes
    total_changes = 0
    for i in range(1, nights):
        prev_rooms = set(r["id"] for r in optimal_combination[i-1]["rooms"])
        curr_rooms = set(r["id"] for r in optimal_combination[i]["rooms"])
        if prev_rooms != curr_rooms:
            total_changes += 1
    
    # Determine status
    all_nights_fulfilled = all(len(segment["rooms"]) == num_rooms for segment in optimal_combination)
    status = "full" if all_nights_fulfilled else "partial"
    
    return {
        "optimal_combination": optimal_combination,
        "total_room_changes": total_changes,
        "availability_status": status,
        "message": f"Found optimal combination with {total_changes} room change(s)" if status == "full" else "Partial availability",
        "summary": {
            "total_nights": nights,
            "rooms_per_night": num_rooms,
            "total_room_changes": total_changes
        }
    }


# ============= BOOKINGS =============

@api_router.get("/bookings", response_model=List[dict])
async def get_bookings(
    status: Optional[BookingStatus] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    query = {}
    if status:
        query["status"] = status.value
    if from_date:
        query["check_in_date"] = {"$gte": from_date}
    if to_date:
        if "check_in_date" in query:
            query["check_in_date"]["$lte"] = to_date
        else:
            query["check_in_date"] = {"$lte": to_date}
    
    bookings = await db.bookings.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return bookings

@api_router.get("/bookings/{booking_id}")
async def get_booking(booking_id: str):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

async def process_room_segments(room_segments: List[dict], check_in_date: str, check_out_date: str, is_org: bool):
    """
    Process room segments for mix & match bookings.
    
    Returns:
        tuple: (room_ids, room_numbers, room_categories, total_amount, has_room_changes)
    """
    from datetime import datetime, timedelta
    
    # Extract all unique room IDs from segments
    all_room_ids = set()
    for segment in room_segments:
        for room in segment.get("rooms", []):
            all_room_ids.add(room["id"])
    
    room_ids = list(all_room_ids)
    room_numbers = []
    room_categories = []
    
    # Validate that all rooms exist
    for rid in room_ids:
        room = await db.rooms.find_one({"id": rid}, {"_id": 0})
        if not room:
            raise HTTPException(status_code=404, detail=f"Room {rid} not found")
        if room["status"] == RoomStatus.MAINTENANCE.value:
            raise HTTPException(status_code=400, detail=f"Room {room['room_number']} is under maintenance")
        room_numbers.append(room["room_number"])
        room_categories.append(room["category"])
    
    # Calculate total amount from segments
    total_amount = 0.0
    start_date = datetime.strptime(check_in_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(check_out_date, "%Y-%m-%d").date()
    nights = (end_date - start_date).days
    
    # Validate segments coverage
    if len(room_segments) != nights:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid room segments: Need {nights} night(s) but got {len(room_segments)} segment(s)"
        )
    
    # Calculate cost for each night
    for segment in room_segments:
        for room_data in segment.get("rooms", []):
            room_category = RoomCategory(room_data["category"])
            rate = await get_room_rate(room_category, is_org)
            license_fee = await get_room_rate(room_category, is_org, is_license_fee=True)
            total_amount += rate + license_fee
    
    # Check if rooms change during stay
    has_room_changes = False
    for i in range(1, len(room_segments)):
        prev_room_ids = set(r["id"] for r in room_segments[i-1]["rooms"])
        curr_room_ids = set(r["id"] for r in room_segments[i]["rooms"])
        if prev_room_ids != curr_room_ids:
            has_room_changes = True
            break
    
    return room_ids, room_numbers, room_categories, total_amount, has_room_changes


@api_router.post("/bookings")
async def create_booking(booking: BookingCreate):
    # Normalize uppercase fields FIRST (army_number, bank_ifsc)
    booking_data = booking.model_dump()
    booking_data = normalize_uppercase_fields(booking_data)
    booking = BookingCreate(**booking_data)
    
    # Validate IFSC code format (after uppercase conversion)
    if booking.bank_ifsc and not validate_ifsc(booking.bank_ifsc):
        raise HTTPException(status_code=400, detail="Invalid IFSC code format. Expected format: ABCD0123456 (4 letters + 0 + 6 alphanumeric)")
    
    # Validate mobile numbers
    if booking.guest_contact and not validate_indian_mobile(booking.guest_contact):
        raise HTTPException(status_code=400, detail="Invalid mobile number. Must be 10 digits starting with 6-9")
    if booking.upi_phone and not validate_indian_mobile(booking.upi_phone):
        raise HTTPException(status_code=400, detail="Invalid UPI phone number. Must be 10 digits starting with 6-9")
    
    # Determine booking type: traditional (room_ids) or segmented (room_segments)
    is_segmented = booking.room_segments is not None and len(booking.room_segments) > 0
    
    if not is_segmented:
        # Traditional booking validation
        if not booking.room_ids or len(booking.room_ids) == 0:
            raise HTTPException(status_code=400, detail="At least one room must be selected")

        # Validate all rooms exist and are available
        room_numbers = []
        room_categories = []
        total_amount = 0.0
        nights = calculate_nights(booking.check_in_date, booking.check_out_date)

        for rid in booking.room_ids:
            room = await db.rooms.find_one({"id": rid}, {"_id": 0})
            if not room:
                raise HTTPException(status_code=404, detail=f"Room {rid} not found")
            if room["status"] == RoomStatus.MAINTENANCE.value:
                raise HTTPException(status_code=400, detail=f"Room {room['room_number']} is under maintenance")

            # Check for overlapping bookings (check both old room_id and new room_ids fields)
            overlapping = await db.bookings.find_one({
                "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
                "$or": [
                    {"room_ids": rid},
                    {"room_id": rid}  # backward compat with old records
                ],
                "check_in_date": {"$lte": booking.check_out_date},
                "check_out_date": {"$gte": booking.check_in_date}
            })
            if overlapping:
                raise HTTPException(status_code=400, detail=f"Room {room['room_number']} is already booked for these dates")

            rate = await get_room_rate(RoomCategory(room["category"]), booking.is_org)
            license_fee = await get_room_rate(RoomCategory(room["category"]), booking.is_org, is_license_fee=True)
            total_amount += (rate + license_fee) * nights
            room_numbers.append(room["room_number"])
            room_categories.append(room["category"])
        
        has_room_changes = False
        room_segments = None
    
    else:
        # Segmented booking (Mix & Match)
        room_ids, room_numbers, room_categories, total_amount, has_room_changes = await process_room_segments(
            booking.room_segments,
            booking.check_in_date,
            booking.check_out_date,
            booking.is_org
        )
        booking.room_ids = room_ids  # For backward compatibility
        room_segments = booking.room_segments

    # Create or find guest
    guest = None
    if booking.guest_contact:
        guest = await db.guests.find_one({"contact_number": booking.guest_contact}, {"_id": 0})
    if not guest:
        guest_obj = Guest(
            name=booking.guest_name,
            contact_number=booking.guest_contact
        )
        guest_doc = serialize_doc(guest_obj.model_dump())
        await db.guests.insert_one(guest_doc)
        guest = guest_doc

    # Generate sequential booking number
    booking_number = await generate_booking_number()

    booking_obj = Booking(
        booking_number=booking_number,
        guest_id=guest["id"],
        guest_name=booking.guest_name,
        guest_contact=booking.guest_contact,
        is_org=booking.is_org,
        org_color=booking.org_color,
        room_ids=booking.room_ids,
        room_numbers=room_numbers,
        room_categories=room_categories,
        room_segments=room_segments,
        has_room_changes=has_room_changes,
        num_guests=booking.num_guests,
        num_rooms=len(booking.room_ids),
        check_in_date=booking.check_in_date,
        check_out_date=booking.check_out_date,
        total_amount=total_amount,
        advance_paid=booking.advance_paid,
        balance_amount=total_amount - booking.advance_paid,
        payment_mode=booking.payment_mode,
        payment_id=booking.payment_id,
        bank_details=booking.bank_details,
        upi_number=booking.upi_number,
        bank_name=booking.bank_name,
        bank_ifsc=booking.bank_ifsc,
        bank_account=booking.bank_account,
        upi_id=booking.upi_id,
        upi_phone=booking.upi_phone,
        guest_age=booking.guest_age,
        guest_sex=booking.guest_sex,
        guest_address=booking.guest_address,
        aadhaar_number=booking.aadhaar_number,
        wife_count=booking.wife_count,
        children_count=booking.children_count,
        family_members=booking.family_members,
        notes=booking.notes
    )

    doc = serialize_doc(booking_obj.model_dump())
    await db.bookings.insert_one(doc)

    # Record advance payment if any
    if booking.advance_paid > 0:
        payment = Payment(
            booking_id=doc["id"],
            booking_number=doc["booking_number"],
            amount=booking.advance_paid,
            payment_type="advance",
            payment_mode=booking.payment_mode
        )
        await db.payments.insert_one(serialize_doc(payment.model_dump()))

    created_booking = await db.bookings.find_one({"id": doc["id"]}, {"_id": 0})
    return created_booking

@api_router.post("/bookings/check-in")
async def check_in(request: CheckInRequest):
    # Normalize uppercase fields FIRST (dependent_id in family members, bank_ifsc)
    request_data = request.model_dump()
    request_data = normalize_uppercase_fields(request_data)
    request = CheckInRequest(**request_data)
    
    # Validate IFSC code format (after uppercase conversion)
    if request.bank_ifsc and not validate_ifsc(request.bank_ifsc):
        raise HTTPException(status_code=400, detail="Invalid IFSC code format. Expected format: ABCD0123456 (4 letters + 0 + 6 alphanumeric)")
    
    # Validate mobile numbers
    if request.guest_contact and not validate_indian_mobile(request.guest_contact):
        raise HTTPException(status_code=400, detail="Invalid mobile number. Must be 10 digits starting with 6-9")
    if request.upi_phone and not validate_indian_mobile(request.upi_phone):
        raise HTTPException(status_code=400, detail="Invalid UPI phone number. Must be 10 digits starting with 6-9")
    
    # Validate family member mobiles
    if request.family_members:
        for member in request.family_members:
            if member.get("mobile") and not validate_indian_mobile(member["mobile"]):
                raise HTTPException(status_code=400, detail=f"Invalid mobile number for family member {member.get('name', 'Unknown')}")
    
    booking = await db.bookings.find_one({"id": request.booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking["status"] != BookingStatus.CONFIRMED.value:
        raise HTTPException(status_code=400, detail="Booking cannot be checked in")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Get settings for rate calculation
    settings = await db.app_settings.find_one({}, {"_id": 0})
    
    # Recalculate room charges based on room_guest_mapping (NEW STRUCTURE)
    new_room_rent_total = 0.0
    if request.room_guest_mapping and len(request.room_guest_mapping) > 0:
        # Calculate nights
        check_in_date = datetime.fromisoformat(booking["check_in_date"].replace('Z', '+00:00'))
        check_out_date = datetime.fromisoformat(booking["check_out_date"].replace('Z', '+00:00'))
        nights = (check_out_date - check_in_date).days
        
        for room in request.room_guest_mapping:
            room_category = room.get("room_category", "Cat I")
            charge_category = room.get("charge_category", room_category)
            
            # Determine rate per night based on charge category
            if charge_category == "Def Civ":
                # Defense Civilian rates
                if room_category == "Cat I":
                    rate_per_night = settings.get("def_civ_cat_i_rate", 600.0)
                else:
                    rate_per_night = settings.get("def_civ_cat_ii_rate", 600.0)
            else:
                # Regular Cat I/II rates
                if room_category == "Cat I":
                    rate_per_night = settings.get("cat_i_rate", 500.0)
                else:
                    rate_per_night = settings.get("cat_ii_rate", 400.0)
            
            new_room_rent_total += rate_per_night * nights
    else:
        # Fallback to original total if no mapping provided (backward compatibility)
        new_room_rent_total = booking.get("room_rent_total", 0.0)
    
    # Calculate extra bed charge
    extra_bed_charge = request.extra_beds * 75.0
    
    # Recalculate total and balance
    new_total_amount = new_room_rent_total + booking.get("license_fee_total", 0.0)
    new_balance = new_total_amount + extra_bed_charge - booking.get("advance_paid", 0.0)

    # Build update fields — only overwrite non-None values
    update_fields = {
        "status": BookingStatus.CHECKED_IN.value,
        "actual_check_in": now,
        "checked_in_by": request.staff_id,
        "extra_beds": request.extra_beds,
        "extra_bed_charge": extra_bed_charge,
        "room_rent_total": new_room_rent_total,  # Update room rent based on new pricing
        "total_amount": new_total_amount,  # Update total amount
        "balance_amount": new_balance,  # Update balance
        "updated_at": now
    }
    optional_fields = {
        "guest_contact": request.guest_contact,
        "guest_age": request.guest_age,
        "guest_sex": request.guest_sex,
        "guest_address": request.guest_address,
        "org_color": request.org_color,  # Organization color if Org guest
        "bank_name": request.bank_name,
        "bank_ifsc": request.bank_ifsc,
        "bank_account": request.bank_account,
        "upi_id": request.upi_id,
        "upi_phone": request.upi_phone,
    }
    for k, v in optional_fields.items():
        if v is not None:
            update_fields[k] = v
    if request.family_members:
        update_fields["family_members"] = request.family_members
    if request.room_guest_mapping:
        update_fields["room_guest_mapping"] = request.room_guest_mapping  # Store the mapping (NEW STRUCTURE)
    if request.notes:
        update_fields["notes"] = request.notes

    # Update booking
    await db.bookings.update_one(
        {"id": request.booking_id},
        {"$set": update_fields}
    )
    
    # Update room status for all rooms in this booking
    room_ids = booking.get("room_ids", [])
    # backward compat: old bookings may have single room_id
    if not room_ids and booking.get("room_id"):
        room_ids = [booking["room_id"]]
    for rid in room_ids:
        await db.rooms.update_one(
            {"id": rid},
            {"$set": {"status": RoomStatus.OCCUPIED.value}}
        )
    
    updated_booking = await db.bookings.find_one({"id": request.booking_id}, {"_id": 0})
    return {"message": "Check-in successful", "booking_id": request.booking_id, "booking": updated_booking}

@api_router.put("/bookings/{booking_id}/update-rooms")
async def update_booking_rooms(booking_id: str, request: dict):
    """P2: Update room assignments for a confirmed booking before check-in"""
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking["status"] != BookingStatus.CONFIRMED.value:
        raise HTTPException(status_code=400, detail="Can only modify rooms for confirmed bookings")
    
    new_room_ids = request.get("room_ids", [])
    if not new_room_ids or len(new_room_ids) != len(booking.get("room_ids", [])):
        raise HTTPException(status_code=400, detail="Invalid room_ids - must match number of originally booked rooms")
    
    # Get new room details
    new_rooms = []
    for room_id in new_room_ids:
        room = await db.rooms.find_one({"id": room_id}, {"_id": 0})
        if not room:
            raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
        new_rooms.append(room)
    
    # Extract room details for booking
    room_numbers = [r["room_number"] for r in new_rooms]
    room_categories = [r["category"] for r in new_rooms]
    
    # Update booking with new room assignments
    now = datetime.now(timezone.utc).isoformat()
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {
            "room_ids": new_room_ids,
            "room_numbers": room_numbers,
            "room_categories": room_categories,
            "updated_at": now
        }}
    )
    
    updated_booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    return {"message": "Room assignments updated", "booking": updated_booking}

@api_router.post("/bookings/check-out")
async def check_out(request: CheckOutRequest):
    booking = await db.bookings.find_one({"id": request.booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking["status"] != BookingStatus.CHECKED_IN.value:
        raise HTTPException(status_code=400, detail="Booking is not checked in")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Calculate final balance
    new_balance = booking["balance_amount"] - request.final_payment
    
    # Update booking
    await db.bookings.update_one(
        {"id": request.booking_id},
        {"$set": {
            "status": BookingStatus.CHECKED_OUT.value,
            "actual_check_out": now,
            "checked_out_by": request.staff_id,
            "balance_amount": new_balance,
            "final_payment": request.final_payment,
            "extra_beds_checkout": request.extra_beds_checkout,
            "extra_bed_days": request.extra_bed_days,
            "extra_bed_charge_checkout": (request.extra_beds_checkout or 0) * (request.extra_bed_days or 0) * 75,
            "updated_at": now
        }}
    )
    
    # Update room status for all rooms in this booking
    room_ids = booking.get("room_ids", [])
    if not room_ids and booking.get("room_id"):
        room_ids = [booking["room_id"]]
    for rid in room_ids:
        await db.rooms.update_one(
            {"id": rid},
            {"$set": {"status": RoomStatus.AVAILABLE.value}}
        )
    
    # Record final payment if any
    if request.final_payment > 0:
        payment = Payment(
            booking_id=booking["id"],
            booking_number=booking["booking_number"],
            amount=request.final_payment,
            payment_type="final",
            payment_mode=request.payment_mode
        )
        await db.payments.insert_one(serialize_doc(payment.model_dump()))
    
    updated_booking = await db.bookings.find_one({"id": request.booking_id}, {"_id": 0})
    return {"message": "Check-out successful", "booking_id": request.booking_id, "booking": updated_booking}

@api_router.get("/bookings/{booking_id}/calculate-refund")
async def calculate_refund(booking_id: str):
    """Calculate refund amount based on cancellation policy (hours-based)
    
    Policy:
    - >96 hours before check-in: 0% charge (100% refund)
    - 48-96 hours before check-in: 50% charge (50% refund)
    - <48 hours before check-in: 100% charge (0% refund)
    """
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    settings = await db.app_settings.find_one({}, {"_id": 0})
    cancellation_policy = settings.get("cancellation_policy", [
        {"hours_before": 96, "charge_percent": 0},
        {"hours_before": 48, "charge_percent": 50},
        {"hours_before": 0, "charge_percent": 100}
    ])
    
    # Calculate hours until check-in
    check_in_date = datetime.fromisoformat(booking["check_in_date"].replace('Z', '+00:00'))
    if isinstance(check_in_date, datetime) and check_in_date.tzinfo is None:
        check_in_date = check_in_date.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    hours_until_checkin = (check_in_date - now).total_seconds() / 3600
    
    # Find applicable charge percent
    charge_percent = 100  # Default: no refund
    for slab in sorted(cancellation_policy, key=lambda x: x["hours_before"], reverse=True):
        if hours_until_checkin >= slab["hours_before"]:
            charge_percent = slab["charge_percent"]
            break
    
    advance_paid = booking.get("advance_paid", 0)
    cancellation_charge = (advance_paid * charge_percent) / 100
    refund_amount = advance_paid - cancellation_charge
    
    return {
        "booking_id": booking_id,
        "booking_number": booking["booking_number"],
        "guest_name": booking["guest_name"],
        "check_in_date": booking["check_in_date"],
        "hours_until_checkin": round(hours_until_checkin, 1),
        "advance_paid": advance_paid,
        "charge_percent": charge_percent,
        "cancellation_charge": cancellation_charge,
        "refund_amount": max(0, refund_amount)
    }

@api_router.post("/bookings/cancel")
async def cancel_booking(request: CancelBookingRequest):
    booking = await db.bookings.find_one({"id": request.booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking["status"] not in [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]:
        raise HTTPException(status_code=400, detail="Booking cannot be cancelled")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Update booking
    await db.bookings.update_one(
        {"id": request.booking_id},
        {"$set": {
            "status": BookingStatus.CANCELLED.value,
            "notes": f"{booking.get('notes', '') or ''} | Cancelled: {request.reason or 'No reason provided'}",
            "updated_at": now
        }}
    )
    
    # Update room status if was occupied (checked_in)
    if booking["status"] == BookingStatus.CHECKED_IN.value:
        room_ids = booking.get("room_ids", [])
        if not room_ids and booking.get("room_id"):
            room_ids = [booking["room_id"]]
        for rid in room_ids:
            await db.rooms.update_one(
                {"id": rid},
                {"$set": {"status": RoomStatus.AVAILABLE.value}}
            )
    
    # Create refund record if advance was paid
    if request.refund_amount > 0:
        refund = Refund(
            booking_id=booking["id"],
            booking_number=booking["booking_number"],
            guest_name=booking["guest_name"],
            amount=request.refund_amount,
            bank_details=booking.get("bank_details"),
            upi_number=booking.get("upi_number"),
            bank_name=booking.get("bank_name"),
            bank_ifsc=booking.get("bank_ifsc"),
            bank_account=booking.get("bank_account"),
            upi_id=booking.get("upi_id"),
            upi_phone=booking.get("upi_phone"),
        )
        await db.refunds.insert_one(serialize_doc(refund.model_dump()))
    
    return {"message": "Booking cancelled successfully", "booking_id": request.booking_id}

@api_router.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: str):
    """
    Permanently delete a booking (NOT cancellation - complete removal)
    
    Use case: Wrong entry that needs to be completely removed from system
    
    This will:
    - Delete booking from database
    - Free up occupied rooms
    - Remove from all analytics (automatic via database query)
    - Remove from planner (automatic via database query)
    - Remove associated payments/refunds (optional - kept for audit)
    
    WARNING: This is irreversible. Use cancellation for normal booking cancellations.
    """
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Free up rooms if booking is confirmed or checked_in
    if booking["status"] in [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]:
        room_ids = booking.get("room_ids", [])
        if not room_ids and booking.get("room_id"):
            room_ids = [booking["room_id"]]
        
        for rid in room_ids:
            await db.rooms.update_one(
                {"id": rid},
                {"$set": {"status": RoomStatus.AVAILABLE.value}}
            )
    
    # Delete the booking
    result = await db.bookings.delete_one({"id": booking_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found or already deleted")
    
    return {
        "message": "Booking permanently deleted",
        "booking_id": booking_id,
        "booking_number": booking.get("booking_number"),
        "guest_name": booking.get("guest_name")
    }

@api_router.post("/bookings/amend")
async def amend_booking(request: AmendBookingRequest):
    """
    Amend a confirmed booking without cancellation charges
    
    Allows changes to: dates, rooms, party composition
    Restrictions: Only CONFIRMED bookings can be amended
    Payment: Collects additional advance if cost increases
    """
    from datetime import date as date_type
    
    # Fetch existing booking
    booking = await db.bookings.find_one({"id": request.booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Restriction: Only CONFIRMED bookings
    if booking["status"] != BookingStatus.CONFIRMED.value:
        raise HTTPException(
            status_code=400, 
            detail=f"Only CONFIRMED bookings can be amended. Current status: {booking['status']}"
        )
    
    # Prepare amendment data
    amendment_data = {
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Track changes for amendment log
    changes = []
    
    # Amend dates
    if request.check_in_date and request.check_in_date != booking["check_in_date"]:
        changes.append(f"Check-in: {booking['check_in_date']} → {request.check_in_date}")
        amendment_data["check_in_date"] = request.check_in_date
    
    if request.check_out_date and request.check_out_date != booking["check_out_date"]:
        changes.append(f"Check-out: {booking['check_out_date']} → {request.check_out_date}")
        amendment_data["check_out_date"] = request.check_out_date
    
    # Amend rooms
    if request.room_ids and request.room_ids != booking.get("room_ids", []):
        # Validate room availability for new dates
        check_in = request.check_in_date or booking["check_in_date"]
        check_out = request.check_out_date or booking["check_out_date"]
        
        # Check if new rooms are available
        for new_room_id in request.room_ids:
            conflicting = await db.bookings.find_one({
                "id": {"$ne": request.booking_id},
                "room_ids": new_room_id,
                "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
                "$or": [
                    {"check_in_date": {"$lt": check_out}, "check_out_date": {"$gt": check_in}},
                ]
            })
            if conflicting:
                room = await db.rooms.find_one({"id": new_room_id}, {"_id": 0})
                raise HTTPException(
                    status_code=400,
                    detail=f"Room {room.get('room_number') if room else new_room_id} not available for selected dates"
                )
        
        # Fetch new room details
        new_rooms = []
        new_room_numbers = []
        new_room_categories = []
        for room_id in request.room_ids:
            room = await db.rooms.find_one({"id": room_id}, {"_id": 0})
            if room:
                new_rooms.append(room["id"])
                new_room_numbers.append(room["room_number"])
                new_room_categories.append(room["category"])
        
        changes.append(f"Rooms: {', '.join(booking.get('room_numbers', []))} → {', '.join(new_room_numbers)}")
        amendment_data["room_ids"] = new_rooms
        amendment_data["room_numbers"] = new_room_numbers
        amendment_data["room_categories"] = new_room_categories
        if request.num_rooms:
            amendment_data["num_rooms"] = request.num_rooms
    
    # Amend party composition
    if request.total_members and request.total_members != booking.get("total_members"):
        changes.append(f"Members: {booking.get('total_members', 1)} → {request.total_members}")
        amendment_data["total_members"] = request.total_members
    
    if request.member_ages:
        amendment_data["member_ages"] = request.member_ages
    
    # Recalculate total amount
    if "check_in_date" in amendment_data or "check_out_date" in amendment_data or "room_ids" in amendment_data:
        from datetime import date as date_type
        
        # FIX: Use correct collection name 'app_settings'
        settings = await db.app_settings.find_one({}, {"_id": 0})
        if not settings:
            settings = {}
        
        print(f"DEBUG: Settings fetched from app_settings: {bool(settings)}, Keys: {list(settings.keys()) if settings else []}")
        
        check_in = date_type.fromisoformat(amendment_data.get("check_in_date", booking["check_in_date"]))
        check_out = date_type.fromisoformat(amendment_data.get("check_out_date", booking["check_out_date"]))
        nights = (check_out - check_in).days
        
        print("=== BACKEND COST CALCULATION ===")
        print(f"Check-in: {check_in}, Check-out: {check_out}, Nights: {nights}")
        
        # Get room categories (either new or existing)
        room_categories = amendment_data.get("room_categories", booking.get("room_categories", []))
        print(f"Room categories: {room_categories}")
        
        # Calculate total for each category
        cat_i_count = sum(1 for cat in room_categories if cat == "Cat I")
        cat_ii_count = sum(1 for cat in room_categories if cat == "Cat II")
        print(f"Cat I count: {cat_i_count}, Cat II count: {cat_ii_count}")
        
        # Use is_org to determine rates
        is_org = booking.get("is_org", False)
        print(f"Is Org: {is_org}")
        print(f"Settings keys: {list(settings.keys())}")
        print(f"Raw cat_i_rate from settings: {settings.get('cat_i_rate')}")
        print(f"Raw cat_ii_rate from settings: {settings.get('cat_ii_rate')}")
        
        if is_org:
            cat_i_rate = float(settings.get("cat_i_rate", 500))
            cat_ii_rate = float(settings.get("cat_ii_rate", 400))
        else:
            # Non-Org uses same rate for both Cat I and Cat II (570+30=600)
            non_org_room_rent = float(settings.get("non_org_room_rent", 570))
            non_org_license_fee = float(settings.get("non_org_license_fee", 30))
            cat_i_rate = non_org_room_rent + non_org_license_fee
            cat_ii_rate = non_org_room_rent + non_org_license_fee
        
        print(f"Cat I rate: {cat_i_rate}, Cat II rate: {cat_ii_rate}")
        
        new_total = (cat_i_count * cat_i_rate + cat_ii_count * cat_ii_rate) * nights
        old_total = booking.get("total_amount", 0)
        
        print(f"Calculation: ({cat_i_count} × {cat_i_rate} + {cat_ii_count} × {cat_ii_rate}) × {nights} = {new_total}")
        print(f"Old Total: {old_total}, New Total: {new_total}, Difference: {new_total - old_total}")
        print("=== END BACKEND CALCULATION ===")
        
        amendment_data["total_amount"] = new_total
        
        # Calculate payment difference
        if new_total > old_total:
            # Increased cost - collect additional advance
            additional_required = new_total - old_total
            if request.additional_advance < additional_required:
                raise HTTPException(
                    status_code=400,
                    detail=f"Additional advance required: ₹{additional_required}. Provided: ₹{request.additional_advance}"
                )
            
            # Update advance paid
            amendment_data["advance_paid"] = booking.get("advance_paid", 0) + request.additional_advance
            
            # Update payment details if provided
            if request.payment_mode:
                amendment_data["payment_mode"] = request.payment_mode
            if request.payment_id:
                amendment_data["payment_id"] = request.payment_id
            if request.bank_name:
                amendment_data["bank_name"] = request.bank_name
            if request.bank_ifsc:
                amendment_data["bank_ifsc"] = request.bank_ifsc.upper()
            if request.bank_account:
                amendment_data["bank_account"] = request.bank_account
            if request.upi_id:
                amendment_data["upi_id"] = request.upi_id
            if request.upi_phone:
                amendment_data["upi_phone"] = request.upi_phone
            
            changes.append(f"Amount: ₹{old_total} → ₹{new_total} (Additional ₹{request.additional_advance} paid)")
        else:
            # Decreased cost - refund at check-in
            changes.append(f"Amount: ₹{old_total} → ₹{new_total} (₹{old_total - new_total} to be refunded at check-in)")
        
        # Recalculate balance
        amendment_data["balance_amount"] = new_total - amendment_data.get("advance_paid", booking.get("advance_paid", 0))
    
    # Add amendment log
    amendment_log = booking.get("amendment_log", [])
    amendment_log.append({
        "amended_at": datetime.now(timezone.utc).isoformat(),
        "changes": changes,
        "reason": request.amendment_reason or "No reason provided"
    })
    amendment_data["amendment_log"] = amendment_log
    
    # Add notes
    notes = booking.get("notes", "") or ""
    notes += f"\n[AMENDED {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}]: {'; '.join(changes)}"
    amendment_data["notes"] = notes.strip()
    
    # Update booking
    await db.bookings.update_one(
        {"id": request.booking_id},
        {"$set": amendment_data}
    )
    
    # Fetch updated booking
    updated_booking = await db.bookings.find_one({"id": request.booking_id}, {"_id": 0})
    
    return {
        "message": "Booking amended successfully",
        "booking": updated_booking,
        "changes": changes
    }

# ============= GUEST HISTORY =============

@api_router.get("/bookings/guest-history")
async def get_guest_history(
    phone_number: Optional[str] = Query(None, description="Guest phone number")
):
    """
    Get booking history for a guest by phone number.
    Returns all bookings, statistics, and guest information.
    """
    if not phone_number:
        raise HTTPException(
            status_code=400, 
            detail="Please provide phone_number"
        )
    
    # Build query - search by phone number
    phone_clean = phone_number.replace(" ", "").replace("+91", "").replace("-", "")
    query = {
        "$or": [
            {"guest_contact": {"$regex": phone_clean, "$options": "i"}},
            {"guest_contact": {"$regex": f"\\+91.*{phone_clean}", "$options": "i"}}
        ]
    }
    
    # Fetch all bookings for this guest
    bookings = await db.bookings.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    if not bookings:
        return {
            "found": False,
            "guest_info": None,
            "bookings": [],
            "statistics": None
        }
    
    # Extract guest info from first booking
    first_booking = bookings[0]
    guest_info = {
        "guest_name": first_booking.get("guest_name"),
        "guest_contact": first_booking.get("guest_contact"),
        "is_org": first_booking.get("is_org", False),
        "org_color": first_booking.get("org_color")
    }
    
    # Calculate statistics
    total_bookings = len(bookings)
    completed_stays = len([b for b in bookings if b.get("status") == "checked_out"])
    cancelled_bookings = len([b for b in bookings if b.get("status") == "cancelled"])
    current_bookings = len([b for b in bookings if b.get("status") in ["confirmed", "checked_in"]])
    
    total_spent = sum(b.get("total_amount", 0) for b in bookings if b.get("status") == "checked_out")
    total_advance_paid = sum(b.get("advance_paid", 0) for b in bookings)
    
    # Calculate total nights stayed
    total_nights = 0
    for booking in bookings:
        if booking.get("status") == "checked_out":
            try:
                checkin = datetime.fromisoformat(booking["check_in_date"].replace('Z', '+00:00'))
                checkout = datetime.fromisoformat(booking["check_out_date"].replace('Z', '+00:00'))
                nights = (checkout - checkin).days
                total_nights += nights
            except:
                pass
    
    statistics = {
        "total_bookings": total_bookings,
        "completed_stays": completed_stays,
        "cancelled_bookings": cancelled_bookings,
        "current_bookings": current_bookings,
        "total_spent": round(total_spent, 2),
        "total_advance_paid": round(total_advance_paid, 2),
        "total_nights_stayed": total_nights,
        "first_visit": bookings[-1].get("created_at") if bookings else None,
        "last_visit": bookings[0].get("created_at") if bookings else None
    }
    
    # Format bookings for response
    formatted_bookings = []
    for booking in bookings:
        formatted_bookings.append({
            "id": booking.get("id"),
            "booking_number": booking.get("booking_number"),
            "check_in_date": booking.get("check_in_date"),
            "check_out_date": booking.get("check_out_date"),
            "actual_check_in": booking.get("actual_check_in"),
            "actual_check_out": booking.get("actual_check_out"),
            "room_numbers": booking.get("room_numbers", []),
            "room_categories": booking.get("room_categories", []),
            "num_rooms": booking.get("num_rooms", 0),
            "num_guests": booking.get("num_guests", 1),
            "status": booking.get("status"),
            "total_amount": booking.get("total_amount", 0),
            "advance_paid": booking.get("advance_paid", 0),
            "balance_amount": booking.get("balance_amount", 0),
            "payment_mode": booking.get("payment_mode"),
            "created_at": booking.get("created_at"),
            "extra_beds": booking.get("extra_beds", 0)
        })
    
    return {
        "found": True,
        "guest_info": guest_info,
        "bookings": formatted_bookings,
        "statistics": statistics
    }

# ============= STAFF =============

@api_router.get("/staff", response_model=List[dict])
async def get_staff(staff_type: Optional[StaffType] = None, active_only: bool = True):
    query = {}
    if staff_type:
        query["staff_type"] = staff_type.value
    if active_only:
        query["is_active"] = True
    
    staff = await db.staff.find(query, {"_id": 0}).to_list(100)
    return staff

@api_router.get("/staff/{staff_id}")
async def get_staff_member(staff_id: str):
    staff = await db.staff.find_one({"id": staff_id}, {"_id": 0})
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    return staff

@api_router.post("/staff")
async def create_staff(staff: StaffCreate):
    staff_obj = Staff(**staff.model_dump())
    doc = serialize_doc(staff_obj.model_dump())
    await db.staff.insert_one(doc)
    # Return the created staff by fetching it back without _id
    created_staff = await db.staff.find_one({"id": doc["id"]}, {"_id": 0})
    return created_staff

@api_router.put("/staff/{staff_id}")
async def update_staff(staff_id: str, update: StaffUpdate):
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    result = await db.staff.update_one({"id": staff_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    return await get_staff_member(staff_id)

@api_router.delete("/staff/{staff_id}")
async def delete_staff(staff_id: str):
    result = await db.staff.delete_one({"id": staff_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Staff not found")
    return {"message": "Staff deleted successfully"}

# ============= REFUNDS =============

@api_router.get("/refunds", response_model=List[dict])
async def get_refunds(status: Optional[RefundStatus] = None):
    query = {}
    if status:
        query["status"] = status.value
    
    refunds = await db.refunds.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return refunds

@api_router.put("/refunds/{refund_id}")
async def update_refund(refund_id: str, update: RefundUpdate):
    now = datetime.now(timezone.utc).isoformat()
    
    update_data = {"status": update.status.value}
    if update.notes:
        update_data["notes"] = update.notes
    if update.transaction_ref:
        update_data["transaction_ref"] = update.transaction_ref
    if update.refund_date:
        update_data["refund_date"] = update.refund_date
    if update.status == RefundStatus.COMPLETED:
        update_data["processed_at"] = now
    
    result = await db.refunds.update_one({"id": refund_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Refund not found")
    
    refund = await db.refunds.find_one({"id": refund_id}, {"_id": 0})
    
    # Record refund payment
    if update.status == RefundStatus.COMPLETED:
        payment = Payment(
            booking_id=refund["booking_id"],
            booking_number=refund["booking_number"],
            amount=-refund["amount"],  # Negative for refund
            payment_type="refund"
        )
        await db.payments.insert_one(serialize_doc(payment.model_dump()))
    
    return refund

# ============= TOILETRY =============

@api_router.get("/toiletry/items", response_model=List[dict])
async def get_toiletry_items():
    items = await db.toiletry_inventory.find({}, {"_id": 0}).to_list(100)
    return items

@api_router.post("/toiletry/items")
async def create_toiletry_item(item: ToiletryItemCreate):
    item_obj = ToiletryItem(**item.model_dump())
    doc = serialize_doc(item_obj.model_dump())
    await db.toiletry_inventory.insert_one(doc)
    # Return the created item by fetching it back without _id
    created_item = await db.toiletry_inventory.find_one({"id": doc["id"]}, {"_id": 0})
    return created_item

@api_router.put("/toiletry/items/{item_id}")
async def update_toiletry_item(item_id: str, update: ToiletryItemUpdate):
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.toiletry_inventory.update_one({"id": item_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return await db.toiletry_inventory.find_one({"id": item_id}, {"_id": 0})

@api_router.delete("/toiletry/items/{item_id}")
async def delete_toiletry_item(item_id: str):
    result = await db.toiletry_inventory.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}

@api_router.post("/toiletry/stock-in")
async def stock_in(request: StockInRequest):
    item = await db.toiletry_inventory.find_one({"id": request.item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    new_quantity = item["quantity"] + request.quantity
    await db.toiletry_inventory.update_one(
        {"id": request.item_id},
        {"$set": {"quantity": new_quantity, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Record transaction
    transaction = ToiletryTransaction(
        item_id=request.item_id,
        item_name=item["name"],
        transaction_type="stock_in",
        quantity=request.quantity,
        notes=request.notes
    )
    await db.toiletry_transactions.insert_one(serialize_doc(transaction.model_dump()))
    
    return {"message": "Stock added successfully", "new_quantity": new_quantity}

@api_router.post("/toiletry/consumption")
async def record_consumption(request: ConsumptionRequest):
    item = await db.toiletry_inventory.find_one({"id": request.item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item["quantity"] < request.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    new_quantity = item["quantity"] - request.quantity
    await db.toiletry_inventory.update_one(
        {"id": request.item_id},
        {"$set": {"quantity": new_quantity, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Record transaction
    transaction = ToiletryTransaction(
        item_id=request.item_id,
        item_name=item["name"],
        transaction_type="consumption",
        quantity=request.quantity,
        booking_id=request.booking_id,
        room_number=request.room_number,
        notes=request.notes
    )
    await db.toiletry_transactions.insert_one(serialize_doc(transaction.model_dump()))
    
    return {"message": "Consumption recorded", "new_quantity": new_quantity}

@api_router.get("/toiletry/transactions")
async def get_toiletry_transactions(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    query = {}
    if from_date or to_date:
        query["created_at"] = {}
        if from_date:
            query["created_at"]["$gte"] = from_date
        if to_date:
            query["created_at"]["$lte"] = to_date
    
    transactions = await db.toiletry_transactions.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return transactions

# ============= DASHBOARD =============

@api_router.get("/dashboard/occupancy")
async def get_occupancy():
    """Get real-time occupancy data"""
    rooms = await db.rooms.find({}, {"_id": 0}).to_list(100)
    
    total_rooms = len(rooms)
    cat_i_rooms = [r for r in rooms if r["category"] == RoomCategory.CAT_I.value]
    cat_ii_rooms = [r for r in rooms if r["category"] == RoomCategory.CAT_II.value]
    
    occupied_rooms = [r for r in rooms if r["status"] == RoomStatus.OCCUPIED.value]
    occupied_cat_i = [r for r in cat_i_rooms if r["status"] == RoomStatus.OCCUPIED.value]
    occupied_cat_ii = [r for r in cat_ii_rooms if r["status"] == RoomStatus.OCCUPIED.value]
    
    return {
        "overall": {
            "total": total_rooms,
            "occupied": len(occupied_rooms),
            "available": total_rooms - len(occupied_rooms),
            "occupancy_percent": round((len(occupied_rooms) / total_rooms * 100) if total_rooms > 0 else 0, 1)
        },
        "cat_i": {
            "total": len(cat_i_rooms),
            "occupied": len(occupied_cat_i),
            "available": len(cat_i_rooms) - len(occupied_cat_i),
            "occupancy_percent": round((len(occupied_cat_i) / len(cat_i_rooms) * 100) if len(cat_i_rooms) > 0 else 0, 1)
        },
        "cat_ii": {
            "total": len(cat_ii_rooms),
            "occupied": len(occupied_cat_ii),
            "available": len(cat_ii_rooms) - len(occupied_cat_ii),
            "occupancy_percent": round((len(occupied_cat_ii) / len(cat_ii_rooms) * 100) if len(cat_ii_rooms) > 0 else 0, 1)
        }
    }

@api_router.get("/dashboard/bookings")
async def get_dashboard_bookings():
    """Get today's and upcoming bookings"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Today's bookings
    today_bookings = await db.bookings.find({
        "check_in_date": {"$lte": today},
        "check_out_date": {"$gte": today},
        "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]}
    }, {"_id": 0}).to_list(100)
    
    # Upcoming bookings (next 7 days)
    next_week = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
    upcoming_bookings = await db.bookings.find({
        "check_in_date": {"$gt": today, "$lte": next_week},
        "status": BookingStatus.CONFIRMED.value
    }, {"_id": 0}).sort("check_in_date", 1).to_list(100)
    
    return {
        "today": today_bookings,
        "upcoming": upcoming_bookings
    }

@api_router.get("/dashboard/analytics")
async def get_analytics(
    month: Optional[int] = None,
    year: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """Get analytics for specified period"""
    now = datetime.now(timezone.utc)
    
    # Default to current month
    if not from_date and not to_date:
        if not month:
            month = now.month
        if not year:
            year = now.year
        from_date = f"{year}-{month:02d}-01"
        # Calculate last day of month
        if month == 12:
            to_date = f"{year + 1}-01-01"
        else:
            to_date = f"{year}-{month + 1:02d}-01"
    
    # Get bookings in period
    bookings = await db.bookings.find({
        "created_at": {"$gte": from_date, "$lt": to_date}
    }, {"_id": 0}).to_list(1000)
    
    # Calculate metrics
    total_bookings = len(bookings)
    checked_out_bookings = [b for b in bookings if b["status"] == BookingStatus.CHECKED_OUT.value]
    
    # Get unique guests
    guest_ids = set(b["guest_id"] for b in bookings)
    
    return {
        "period": {"from": from_date, "to": to_date},
        "total_bookings": total_bookings,
        "completed_stays": len(checked_out_bookings),
        "total_guests": len(guest_ids),
        "average_occupancy": round((len(checked_out_bookings) / total_bookings * 100) if total_bookings > 0 else 0, 1)
    }

@api_router.get("/dashboard/funds")
async def get_fund_dashboard(
    month: Optional[int] = None,
    year: Optional[int] = None
):
    """Get fund generation dashboard"""
    now = datetime.now(timezone.utc)
    
    if not month:
        month = now.month
    if not year:
        year = now.year
    
    from_date = f"{year}-{month:02d}-01"
    if month == 12:
        to_date = f"{year + 1}-01-01"
    else:
        to_date = f"{year}-{month + 1:02d}-01"
    
    # Get all payments in period
    payments = await db.payments.find({
        "created_at": {"$gte": from_date, "$lt": to_date}
    }, {"_id": 0}).to_list(1000)
    
    # Calculate totals    
    advance_amount = sum(
        p["amount"] for p in payments 
        if p["payment_type"] == "advance"
    )
    
    refunds_amount = abs(sum(
        p["amount"] for p in payments 
        if p["payment_type"] == "refund"
    ))
    
    # Get refund status
    pending_refunds = await db.refunds.find({
        "status": RefundStatus.PENDING.value,
        "created_at": {"$gte": from_date, "$lt": to_date}
    }, {"_id": 0}).to_list(100)
    
    completed_refunds = await db.refunds.find({
        "status": RefundStatus.COMPLETED.value,
        "created_at": {"$gte": from_date, "$lt": to_date}
    }, {"_id": 0}).to_list(100)
    
    # Also get completed bookings amount
    completed_bookings = await db.bookings.find({
        "status": BookingStatus.CHECKED_OUT.value,
        "actual_check_out": {"$gte": from_date, "$lt": to_date}
    }, {"_id": 0}).to_list(1000)
    
    total_from_completed = sum(b["total_amount"] - b.get("balance_amount", 0) for b in completed_bookings)
    
    net_revenue = total_from_completed + advance_amount - refunds_amount
    
    return {
        "period": {"month": month, "year": year},
        "completed_stays_amount": total_from_completed,
        "advance_booking_amount": advance_amount,
        "refunds_issued": refunds_amount,
        "net_revenue": net_revenue,
        "cancellations": {
            "total": len(pending_refunds) + len(completed_refunds),
            "pending_refunds": len(pending_refunds),
            "pending_refunds_amount": sum(r["amount"] for r in pending_refunds),
            "completed_refunds": len(completed_refunds)
        }
    }

@api_router.get("/dashboard/room-availability")
async def check_room_availability(
    check_in_date: str,
    check_out_date: str,
    category: Optional[RoomCategory] = None
):
    """Check available rooms for given dates"""
    query = {}
    if category:
        query["category"] = category.value
    
    all_rooms = await db.rooms.find(query, {"_id": 0}).to_list(100)
    
    # Get bookings that overlap with requested dates
    overlapping_bookings = await db.bookings.find({
        "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
        "$or": [
            {"check_in_date": {"$lte": check_out_date}, "check_out_date": {"$gte": check_in_date}}
        ]
    }, {"_id": 0}).to_list(1000)
    
    booked_room_ids = set()
    for b in overlapping_bookings:
        # Handle new format (room_ids array)
        for rid in b.get("room_ids", []):
            booked_room_ids.add(rid)
        # Backward compat: old format (single room_id)
        if b.get("room_id"):
            booked_room_ids.add(b["room_id"])
    
    available_rooms = [r for r in all_rooms if r["id"] not in booked_room_ids and r["status"] != RoomStatus.MAINTENANCE.value]
    
    return {
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "available_rooms": available_rooms,
        "total_available": len(available_rooms)
    }

@api_router.get("/dashboard/calendar")
async def get_calendar_data(month: int, year: int):
    """Get calendar/planner data for a given month showing room bookings per day
    
    Booking Time Logic:
    - Check-in: 1300h (1 PM) on check-in date
    - Check-out: 0800h (8 AM) on check-out date
    - Room Available: 0900h (9 AM) on check-out date
    
    Calendar Display:
    - Room shows as occupied on check-in date
    - Room shows as occupied on check-out date (until 08:00)
    - Room becomes available for NEW bookings from check-out date
    """
    import calendar
    
    days_in_month = calendar.monthrange(year, month)[1]
    first_day = f"{year}-{month:02d}-01"
    last_day = f"{year}-{month:02d}-{days_in_month:02d}"
    
    # Get all rooms
    all_rooms = await db.rooms.find({}, {"_id": 0}).sort("room_number", 1).to_list(100)
    
    # Get bookings overlapping with this month (active ones + checked_out for history)
    bookings = await db.bookings.find({
        "status": {"$in": [
            BookingStatus.CONFIRMED.value,
            BookingStatus.CHECKED_IN.value,
            BookingStatus.CHECKED_OUT.value
        ]},
        "check_in_date": {"$lte": last_day},
        "check_out_date": {"$gte": first_day}
    }, {"_id": 0}).to_list(5000)
    
    # Build a mapping: room_id -> list of {date_range, status, guest_name, booking_id}
    # Also build room_number -> room_id mapping for fallback (handles room ID mismatches)
    room_number_to_id = {r["room_number"]: r["id"] for r in all_rooms}
    
    room_bookings = {}
    for b in bookings:
        # Get room IDs (handle both old and new format)
        rids = b.get("room_ids", [])
        if not rids and b.get("room_id"):
            rids = [b["room_id"]]
        
        # Also try to get room numbers if available (fallback for ID mismatches)
        room_numbers = b.get("room_numbers", [])
        if not room_numbers and b.get("room_number"):
            room_numbers = [b["room_number"]]
        
        # Map room numbers to IDs (fallback mechanism for data migration)
        if room_numbers:
            for rnum in room_numbers:
                if rnum in room_number_to_id:
                    rid = room_number_to_id[rnum]
                    if rid not in rids:
                        rids.append(rid)
        
        for rid in rids:
            if rid not in room_bookings:
                room_bookings[rid] = []
            room_bookings[rid].append({
                "booking_id": b["id"],
                "booking_number": b.get("booking_number", ""),
                "guest_name": b["guest_name"],
                "check_in_date": b["check_in_date"],
                "check_out_date": b["check_out_date"],
                "status": b["status"]
            })
    
    # Build per-room per-day grid
    calendar_data = []
    for room in all_rooms:
        room_entry = {
            "room_id": room["id"],
            "room_number": room["room_number"],
            "category": room["category"],
            "days": {}
        }
        rb = room_bookings.get(room["id"], [])
        for day in range(1, days_in_month + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            day_status = "available"
            day_info = None
            for bk in rb:
                # UPDATED LOGIC: Show booking on both check-in and check-out date
                # Room is occupied until check-out date (08:00), available from 09:00 same day
                # For calendar display, we include the check-out date as occupied
                if bk["check_in_date"] <= date_str <= bk["check_out_date"]:
                    day_status = bk["status"]
                    day_info = {
                        "booking_id": bk["booking_id"],
                        "booking_number": bk["booking_number"],
                        "guest_name": bk["guest_name"],
                        "is_checkin_date": date_str == bk["check_in_date"],
                        "is_checkout_date": date_str == bk["check_out_date"]
                    }
                    break
            room_entry["days"][date_str] = {
                "status": day_status,
                "booking": day_info
            }
        calendar_data.append(room_entry)
    
    return {
        "month": month,
        "year": year,
        "days_in_month": days_in_month,
        "rooms": calendar_data
    }


# ============= GUESTS =============

@api_router.get("/guests", response_model=List[dict])
async def get_guests(search: Optional[str] = None):
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"contact_number": {"$regex": search, "$options": "i"}}
        ]
    
    guests = await db.guests.find(query, {"_id": 0}).to_list(100)
    return guests

@api_router.get("/guests/{guest_id}")
async def get_guest(guest_id: str):
    guest = await db.guests.find_one({"id": guest_id}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest

# ====== FEEDBACK ======
class FeedbackCreate(BaseModel):
    booking_id: str
    cleanliness: int
    room_comfort: int
    basic_amenities: int
    check_in_procedure: int
    check_out_procedure: int
    overall_stay: int
    staff_behaviour: int
    enjoyed_most: Optional[str] = None
    issues_problems: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    additional_comments: Optional[str] = None
    would_recommend: bool = True

@api_router.post("/feedback")
async def create_feedback(fb: FeedbackCreate):
    # Validate ratings
    for field in ["cleanliness", "room_comfort", "basic_amenities", "check_in_procedure",
                  "check_out_procedure", "overall_stay", "staff_behaviour"]:
        val = getattr(fb, field)
        if not (1 <= val <= 5):
            raise HTTPException(status_code=400, detail=f"{field} rating must be between 1 and 5")
    
    booking = await db.bookings.find_one({"id": fb.booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Compute duration
    try:
        nights = calculate_nights(booking.get("check_in_date", ""), booking.get("check_out_date", ""))
    except Exception:
        nights = 0
    
    feedback_doc = {
        "id": str(uuid.uuid4()),
        "booking_id": fb.booking_id,
        "booking_number": booking.get("booking_number", ""),
        "guest_name": booking.get("guest_name", ""),
        "guest_contact": booking.get("guest_contact"),
        "is_org": booking.get("is_org", False),
        "org_color": booking.get("org_color"),
        "check_in_date": booking.get("check_in_date", ""),
        "check_out_date": booking.get("check_out_date", ""),
        "duration_nights": nights,
        "cleanliness": fb.cleanliness,
        "room_comfort": fb.room_comfort,
        "basic_amenities": fb.basic_amenities,
        "check_in_procedure": fb.check_in_procedure,
        "check_out_procedure": fb.check_out_procedure,
        "overall_stay": fb.overall_stay,
        "staff_behaviour": fb.staff_behaviour,
        "enjoyed_most": fb.enjoyed_most,
        "issues_problems": fb.issues_problems,
        "improvement_suggestions": fb.improvement_suggestions,
        "additional_comments": fb.additional_comments,
        "would_recommend": fb.would_recommend,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.feedbacks.insert_one(feedback_doc)
    return {"message": "Feedback submitted successfully", "feedback_id": feedback_doc["id"]}

@api_router.get("/feedback")
async def get_feedbacks(booking_id: Optional[str] = None):
    query = {}
    if booking_id:
        query["booking_id"] = booking_id
    feedbacks = await db.feedbacks.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return feedbacks

@api_router.get("/feedback/analysis")
async def get_feedback_analysis():
    feedbacks = await db.feedbacks.find({}, {"_id": 0}).to_list(1000)
    if not feedbacks:
        return {
            "total_count": 0,
            "average_score": 0,
            "category_averages": {},
            "recommendation_rate": 0,
            "recent_feedbacks": []
        }
    
    categories = ["cleanliness", "room_comfort", "basic_amenities", "check_in_procedure",
                  "check_out_procedure", "overall_stay", "staff_behaviour"]
    
    cat_sums = {c: 0 for c in categories}
    total_score = 0
    recommend_count = 0
    
    for fb in feedbacks:
        for c in categories:
            cat_sums[c] += fb.get(c, 0)
        avg = sum(fb.get(c, 0) for c in categories) / 7
        total_score += avg
        if fb.get("would_recommend", False):
            recommend_count += 1
    
    n = len(feedbacks)
    category_averages = {c: round(cat_sums[c] / n, 2) for c in categories}
    overall_average = round(total_score / n, 2)
    
    return {
        "total_count": n,
        "average_score": overall_average,
        "category_averages": category_averages,
        "recommendation_rate": round((recommend_count / n) * 100, 1),
        "recent_feedbacks": feedbacks[:10]
    }

# ====== MONTHLY REPORT ======
from datetime import date as date_type

@api_router.get("/reports/monthly")
async def get_monthly_report(month: int = Query(..., ge=1, le=12), year: int = Query(..., ge=2000)):
    import calendar as cal_mod
    days_in_month = cal_mod.monthrange(year, month)[1]
    month_start_str = f"{year}-{month:02d}-01"
    month_end_str = f"{year}-{month:02d}-{days_in_month:02d}"
    month_start = date_type(year, month, 1)
    month_end = date_type(year, month, days_in_month)

    bookings = await db.bookings.find(
        {"status": {"$in": ["checked_in", "checked_out"]},
         "check_in_date": {"$lte": month_end_str},
         "check_out_date": {"$gt": month_start_str}},
        {"_id": 0}
    ).to_list(2000)

    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}
    
    # Color-based grouping for Org guests + Non-Org category
    colors_list = settings.get("colors", COLOR_OPTIONS)
    color_stats = {color: {"guests": 0, "days": 0} for color in colors_list}
    color_stats["Non-Org"] = {"guests": 0, "days": 0}  # For non-organization guests
    color_stats["Unassigned"] = {"guests": 0, "days": 0}  # For Org guests without color yet
    
    org_cat_i_days = 0  # Organization Cat I
    org_cat_ii_days = 0  # Organization Cat II
    non_org_days = 0  # Non-Org (all categories)
    extra_beds_total = 0
    
    for bk in bookings:
        checkin = date_type.fromisoformat(bk.get("check_in_date", month_start_str))
        checkout = date_type.fromisoformat(bk.get("check_out_date", month_end_str))
        eff_in = max(checkin, month_start)
        eff_out = min(checkout, month_end + timedelta(days=1))
        nights = max(0, (eff_out - eff_in).days)
        if nights == 0:
            continue
        
        is_org = bk.get("is_org", False)
        org_color = bk.get("org_color")
        
        # Categorize by Org/Non-Org and color
        if is_org:
            if org_color and org_color in color_stats:
                color_key = org_color
            else:
                color_key = "Unassigned"  # Org guest but no color assigned yet
        else:
            color_key = "Non-Org"
        
        if color_key in color_stats:
            color_stats[color_key]["guests"] += 1
            color_stats[color_key]["days"] += nights
        
        # Calculate room-days by category for revenue
        cats = bk.get("room_categories", [])
        if is_org:
            # Organization rates - Cat I or Cat II
            for cat in (cats or ["Cat II"]):
                if cat == "Cat I":
                    org_cat_i_days += nights
                else:
                    org_cat_ii_days += nights
        else:
            # Non-Org rates (flat rate regardless of category)
            non_org_days += nights * max(1, len(cats))
        
        extra_beds_total += bk.get("extra_beds", 0) * nights
    
    s = settings
    cat_i_lf = s.get("cat_i_license_fee", 30)
    cat_ii_lf = s.get("cat_ii_license_fee", 15)
    non_org_lf = s.get("non_org_license_fee", 30)
    cat_i_rr = s.get("cat_i_room_rent", 470)
    cat_ii_rr = s.get("cat_ii_room_rent", 385)
    non_org_rr = s.get("non_org_room_rent", 570)
    
    room_rent_total = round(org_cat_i_days * cat_i_rr + org_cat_ii_days * cat_ii_rr + non_org_days * non_org_rr, 2)
    lf_org_cat_i = round(org_cat_i_days * cat_i_lf, 2)
    lf_org_cat_ii = round(org_cat_ii_days * cat_ii_lf, 2)
    lf_non_org = round(non_org_days * non_org_lf, 2)
    total_license_fee = round(lf_org_cat_i + lf_org_cat_ii + lf_non_org, 2)
    extra_bed_amount = round(extra_beds_total * 75, 2)
    grand_total = round(room_rent_total + total_license_fee + extra_bed_amount, 2)
    
    # Advance received for bookings made/checked-in this month
    adv_bk = await db.bookings.find(
        {"check_in_date": {"$gte": month_start_str, "$lte": month_end_str}},
        {"_id": 0, "advance_paid": 1}
    ).to_list(2000)
    advance_received = round(sum(b.get("advance_paid", 0) for b in adv_bk), 2)
    advance_adjusted = round(sum(
        b.get("advance_paid", 0) for b in bookings
        if b.get("status") == "checked_out" and 
        (b.get("actual_check_out") or "")[:7] == f"{year}-{month:02d}"
    ), 2)
    
    total_rooms = s.get("cat_i_rooms_count", 6) + s.get("cat_ii_rooms_count", 9)
    total_booked_days = sum(v["days"] for v in color_stats.values())
    avg_occ = round(total_booked_days / (total_rooms * days_in_month) * 100, 2) if total_rooms * days_in_month > 0 else 0
    
    no_shows = await db.bookings.count_documents({
        "status": "cancelled", "advance_paid": {"$gt": 0},
        "check_in_date": {"$gte": month_start_str, "$lte": month_end_str}
    })
    
    return {
        "month": month, "year": year,
        "month_name": cal_mod.month_name[month],
        "days_in_month": days_in_month, "total_rooms": total_rooms,
        "color_breakdown": [
            {"color": c, "guests": color_stats[c]["guests"], "days": color_stats[c]["days"]}
            for c in color_stats.keys() if color_stats[c]["guests"] > 0 or color_stats[c]["days"] > 0
        ],
        "total_guests": sum(v["guests"] for v in color_stats.values()),
        "total_days": total_booked_days,
        "org_cat_i_days": org_cat_i_days, "org_cat_ii_days": org_cat_ii_days, "non_org_days": non_org_days,
        "extra_beds_total": extra_beds_total,
        "license_fees": {
            "org_cat_i": {"days": org_cat_i_days, "rate": cat_i_lf, "total": lf_org_cat_i},
            "org_cat_ii": {"days": org_cat_ii_days, "rate": cat_ii_lf, "total": lf_org_cat_ii},
            "non_org": {"days": non_org_days, "rate": non_org_lf, "total": lf_non_org}
        },
        "room_rent_total": room_rent_total,
        "total_license_fee": total_license_fee,
        "extra_bed_amount": extra_bed_amount,
        "grand_total": grand_total,
        "advance_received": advance_received,
        "advance_adjusted": advance_adjusted,
        "balance_advance": round(advance_received - advance_adjusted, 2),
        "no_shows": no_shows,
        "total_booked_days": total_booked_days,
        "avg_occupancy": avg_occ,
        "rates": {
            "cat_i_room_rent": cat_i_rr, "cat_ii_room_rent": cat_ii_rr, "non_org_room_rent": non_org_rr,
            "cat_i_license_fee": cat_i_lf, "cat_ii_license_fee": cat_ii_lf, "non_org_license_fee": non_org_lf
        }
    }

# ============= NEW REPORT ENDPOINTS =============

@api_router.get("/reports/room-occupancy")
async def get_room_occupancy_report(
    filter_type: str = Query(...),
    month: Optional[int] = None,
    year: Optional[int] = None,
    quarter: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get room occupancy report with flexible date filters"""
    import calendar as cal_mod
    
    # Determine date range based on filter type
    if filter_type == "daily":
        if not start_date:
            start_date = date_type.today().isoformat()
        end_date = start_date
        period_label = f"Daily Report - {start_date}"
    elif filter_type == "monthly":
        if not month or not year:
            raise HTTPException(400, "Month and year required for monthly filter")
        days_in_month = cal_mod.monthrange(year, month)[1]
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{days_in_month:02d}"
        period_label = f"{cal_mod.month_name[month]} {year}"
    elif filter_type == "quarterly":
        if not quarter or not year:
            raise HTTPException(400, "Quarter and year required for quarterly filter")
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2
        start_date = f"{year}-{start_month:02d}-01"
        days_in_end_month = cal_mod.monthrange(year, end_month)[1]
        end_date = f"{year}-{end_month:02d}-{days_in_end_month:02d}"
        period_label = f"Q{quarter} {year}"
    elif filter_type == "annual":
        if not year:
            raise HTTPException(400, "Year required for annual filter")
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        period_label = f"Year {year}"
    elif filter_type == "custom":
        if not start_date or not end_date:
            raise HTTPException(400, "Start and end dates required for custom filter")
        period_label = f"{start_date} to {end_date}"
    else:
        raise HTTPException(400, "Invalid filter type")
    
    # Get all rooms
    all_rooms = await db.rooms.find({}, {"_id": 0}).sort("room_number", 1).to_list(100)
    
    # Get bookings in the date range (checked_in or checked_out)
    bookings = await db.bookings.find({
        "status": {"$in": ["checked_in", "checked_out"]},
        "check_in_date": {"$lte": end_date},
        "check_out_date": {"$gt": start_date}
    }, {"_id": 0}).to_list(5000)
    
    # Calculate total days in period
    start_dt = date_type.fromisoformat(start_date)
    end_dt = date_type.fromisoformat(end_date)
    total_days = (end_dt - start_dt).days + 1
    
    # Get settings for rates
    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}
    cat_i_rr = settings.get("cat_i_room_rent", 470)
    cat_ii_rr = settings.get("cat_ii_room_rent", 385)
    non_org_rr = settings.get("non_org_room_rent", 570)
    cat_i_lf = settings.get("cat_i_license_fee", 30)
    cat_ii_lf = settings.get("cat_ii_license_fee", 15)
    non_org_lf = settings.get("non_org_license_fee", 30)
    
    # Calculate room-wise occupancy
    room_details = []
    total_occupied = 0
    total_revenue = 0
    
    for room in all_rooms:
        room_id = room["id"]
        room_number = room["room_number"]
        category = room["category"]
        
        # Find bookings for this room
        room_bookings = []
        for bk in bookings:
            room_ids = bk.get("room_ids", [])
            if not room_ids and bk.get("room_id"):
                room_ids = [bk["room_id"]]
            if room_id in room_ids:
                room_bookings.append(bk)
        
        # Calculate occupied days and build detailed booking list
        occupied_days = 0
        room_revenue = 0
        bookings_detail = []
        
        for bk in room_bookings:
            checkin = date_type.fromisoformat(bk["check_in_date"])
            checkout = date_type.fromisoformat(bk["check_out_date"])
            eff_in = max(checkin, start_dt)
            eff_out = min(checkout, end_dt + timedelta(days=1))
            nights = max(0, (eff_out - eff_in).days)
            occupied_days += nights
            
            # Calculate revenue for this booking
            is_org = bk.get("is_org", False)
            
            if is_org:
                # Organization rates based on category
                if category == "Cat I":
                    rate_per_day = cat_i_rr + cat_i_lf
                else:
                    rate_per_day = cat_ii_rr + cat_ii_lf
            else:
                # Non-Org flat rate
                rate_per_day = non_org_rr + non_org_lf
            
            booking_revenue = nights * rate_per_day
            room_revenue += booking_revenue
            
            # Count total members (main guest + family)
            total_members = 1 + len(bk.get("family_members", []))
            
            # Build detailed booking info for expandable row
            bookings_detail.append({
                "booking_number": bk.get("booking_number", "N/A"),
                "is_org": is_org,
                "org_color": bk.get("org_color", "N/A"),
                "name": bk.get("guest_name", "N/A"),
                "from_date": bk["check_in_date"],
                "to_date": bk["check_out_date"],
                "days": nights,
                "total_members": total_members,
                "rate_per_day": rate_per_day,
                "total_revenue_due": round(booking_revenue, 2),
                "bill_no": bk.get("booking_number", "N/A"),  # Using booking number as bill number
                "advance_paid": bk.get("advance_paid", 0),
                "final_amount_paid": bk.get("balance_amount", 0) if bk.get("status") == "checked_out" else 0
            })
        
        available_days = total_days - occupied_days
        occupancy_percent = round((occupied_days / total_days) * 100, 2) if total_days > 0 else 0
        
        room_details.append({
            "room_number": room_number,
            "category": category,
            "occupied_days": occupied_days,
            "available_days": available_days,
            "occupancy_percent": occupancy_percent,
            "revenue": round(room_revenue, 2),
            "bookings_detail": bookings_detail  # NEW: Expandable booking details
        })
        
        total_occupied += occupied_days
        total_revenue += room_revenue
    
    total_available = (len(all_rooms) * total_days) - total_occupied
    avg_occupancy = round((total_occupied / (len(all_rooms) * total_days)) * 100, 2) if len(all_rooms) * total_days > 0 else 0
    
    return {
        "period_label": period_label,
        "start_date": start_date,
        "end_date": end_date,
        "total_rooms": len(all_rooms),
        "total_days": total_days,
        "total_occupied_days": total_occupied,
        "total_available_days": total_available,
        "avg_occupancy": avg_occupancy,
        "total_bookings": len(bookings),
        "total_revenue": round(total_revenue, 2),
        "room_details": room_details
    }


@api_router.get("/reports/room-allotment")
async def get_room_allotment_report(
    filter_type: str = Query(...),
    month: Optional[int] = None,
    year: Optional[int] = None,
    quarter: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get room allotment report showing all bookings with room assignments"""
    import calendar as cal_mod
    
    # Determine date range based on filter type (same logic as occupancy)
    if filter_type == "daily":
        if not start_date:
            start_date = date_type.today().isoformat()
        end_date = start_date
        period_label = f"Daily Report - {start_date}"
    elif filter_type == "monthly":
        if not month or not year:
            raise HTTPException(400, "Month and year required for monthly filter")
        days_in_month = cal_mod.monthrange(year, month)[1]
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{days_in_month:02d}"
        period_label = f"{cal_mod.month_name[month]} {year}"
    elif filter_type == "quarterly":
        if not quarter or not year:
            raise HTTPException(400, "Quarter and year required for quarterly filter")
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2
        start_date = f"{year}-{start_month:02d}-01"
        days_in_end_month = cal_mod.monthrange(year, end_month)[1]
        end_date = f"{year}-{end_month:02d}-{days_in_end_month:02d}"
        period_label = f"Q{quarter} {year}"
    elif filter_type == "annual":
        if not year:
            raise HTTPException(400, "Year required for annual filter")
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        period_label = f"Year {year}"
    elif filter_type == "custom":
        if not start_date or not end_date:
            raise HTTPException(400, "Start and end dates required for custom filter")
        period_label = f"{start_date} to {end_date}"
    else:
        raise HTTPException(400, "Invalid filter type")
    
    # Get bookings in the date range
    bookings = await db.bookings.find({
        "status": {"$in": ["confirmed", "checked_in", "checked_out"]},
        "check_in_date": {"$lte": end_date},
        "check_out_date": {"$gt": start_date}
    }, {"_id": 0}).sort("check_in_date", 1).to_list(5000)
    
    # Get settings for financial calculations
    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}
    
    allotments = []
    for bk in bookings:
        checkin = date_type.fromisoformat(bk["check_in_date"])
        checkout = date_type.fromisoformat(bk["check_out_date"])
        nights = (checkout - checkin).days
        
        # Calculate total amount
        is_org = bk.get("is_org", False)
        cats = bk.get("room_categories", [])
        num_rooms = len(bk.get("room_ids", [])) or 1
        
        if is_org:
            # Organization rates based on category
            if "Cat I" in cats:
                room_rent = settings.get("cat_i_room_rent", 470)
                license_fee = settings.get("cat_i_license_fee", 30)
            else:
                room_rent = settings.get("cat_ii_room_rent", 385)
                license_fee = settings.get("cat_ii_license_fee", 15)
        else:
            # Non-Org flat rate
            room_rent = settings.get("non_org_room_rent", 570)
            license_fee = settings.get("non_org_license_fee", 30)
        
        total_amount = (room_rent + license_fee) * nights * num_rooms
        total_amount += bk.get("extra_beds", 0) * 75 * nights
        
        # Calculate party composition
        self_count = 1  # Main guest
        wife_count = 0
        child_count = 0
        dependents_count = 0  # Those WITH org_id (formerly dependent_id)
        non_dependents_count = 0  # Those WITHOUT org_id
        
        family_members = bk.get("family_members", [])
        for fm in family_members:
            relation = (fm.get("relation") or "").lower()
            has_org_card = fm.get("has_org_card", False)
            org_id = fm.get("org_id", "")
            
            # Count by relationship
            if "w/o" in relation or "wife" in relation:
                wife_count += 1
            elif "s/o" in relation or "d/o" in relation or "son" in relation or "daughter" in relation or "child" in relation:
                child_count += 1
            
            # Count dependents vs non-dependents
            if has_org_card and org_id:
                dependents_count += 1
            else:
                non_dependents_count += 1
        
        allotments.append({
            "booking_id": bk["id"],
            "booking_number": bk.get("booking_number", "N/A"),
            "guest_name": bk.get("guest_name", "N/A"),
            "is_org": is_org,
            "org_color": bk.get("org_color", "N/A"),
            "room_numbers": bk.get("room_numbers", []),
            "room_categories": bk.get("room_categories", []),
            "check_in_date": bk["check_in_date"],
            "check_out_date": bk["check_out_date"],
            "nights": nights,
            "self_count": self_count,
            "wife_count": wife_count,
            "child_count": child_count,
            "dependents": dependents_count,
            "non_dependents": non_dependents_count,
            "aadhaar_no": bk.get("aadhaar_number", "N/A"),
            "mobile_no": bk.get("guest_contact", "N/A"),
            "total_amount": round(total_amount, 2)
        })
    
    return {
        "period_label": period_label,
        "start_date": start_date,
        "end_date": end_date,
        "total_allotments": len(allotments),
        "allotments": allotments
    }


@api_router.get("/reports/guest-details")
async def get_guest_details_report(
    filter_type: str = Query(...),
    month: Optional[int] = None,
    year: Optional[int] = None,
    quarter: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get comprehensive guest details report - includes ALL party members"""
    import calendar as cal_mod
    
    # Determine date range based on filter type
    if filter_type == "daily":
        if not start_date:
            start_date = date_type.today().isoformat()
        end_date = start_date
        period_label = f"Daily Report - {start_date}"
    elif filter_type == "monthly":
        if not month or not year:
            raise HTTPException(400, "Month and year required for monthly filter")
        days_in_month = cal_mod.monthrange(year, month)[1]
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{days_in_month:02d}"
        period_label = f"{cal_mod.month_name[month]} {year}"
    elif filter_type == "quarterly":
        if not quarter or not year:
            raise HTTPException(400, "Quarter and year required for quarterly filter")
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2
        start_date = f"{year}-{start_month:02d}-01"
        days_in_end_month = cal_mod.monthrange(year, end_month)[1]
        end_date = f"{year}-{end_month:02d}-{days_in_end_month:02d}"
        period_label = f"Q{quarter} {year}"
    elif filter_type == "annual":
        if not year:
            raise HTTPException(400, "Year required for annual filter")
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        period_label = f"Year {year}"
    elif filter_type == "custom":
        if not start_date or not end_date:
            raise HTTPException(400, "Start and end dates required for custom filter")
        period_label = f"{start_date} to {end_date}"
    else:
        raise HTTPException(400, "Invalid filter type")
    
    # Get bookings in the date range
    bookings = await db.bookings.find({
        "status": {"$in": ["confirmed", "checked_in", "checked_out"]},
        "check_in_date": {"$lte": end_date},
        "check_out_date": {"$gt": start_date}
    }, {"_id": 0}).sort("check_in_date", 1).to_list(5000)
    
    # Get settings for financial calculations
    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}
    
    guest_party_members = []
    total_nights = 0
    total_revenue = 0
    total_party_members = 0
    
    for bk in bookings:
        checkin = date_type.fromisoformat(bk["check_in_date"])
        checkout = date_type.fromisoformat(bk["check_out_date"])
        nights = (checkout - checkin).days
        total_nights += nights
        
        # Calculate total amount
        is_org = bk.get("is_org", False)
        cats = bk.get("room_categories", [])
        num_rooms = len(bk.get("room_ids", [])) or 1
        
        if is_org:
            # Organization rates based on category
            if "Cat I" in cats:
                room_rent = settings.get("cat_i_room_rent", 470)
                license_fee = settings.get("cat_i_license_fee", 30)
            else:
                room_rent = settings.get("cat_ii_room_rent", 385)
                license_fee = settings.get("cat_ii_license_fee", 15)
        else:
            # Non-Org flat rate
            room_rent = settings.get("non_org_room_rent", 570)
            license_fee = settings.get("non_org_license_fee", 30)
        
        total_amount = (room_rent + license_fee) * nights * num_rooms
        total_amount += bk.get("extra_beds", 0) * 75 * nights
        total_revenue += total_amount
        
        # Add main guest (Self)
        guest_party_members.append({
            "booking_number": bk.get("booking_number", "N/A"),
            "room_numbers": ", ".join(bk.get("room_numbers", [])),
            "is_org": "Org" if is_org else "Non-Org",
            "org_color": bk.get("org_color", "—"),
            "name": bk.get("guest_name", "N/A"),
            "age": bk.get("guest_age") or "—",
            "sex": bk.get("guest_sex") or "—",
            "relationship": "Self",
            "address": bk.get("guest_address") or "—",
            "aadhaar_no": bk.get("aadhaar_number") or "—",
            "mobile_no": bk.get("guest_contact") or "—",
            "check_in_date": bk["check_in_date"],
            "check_out_date": bk["check_out_date"],
            "nights": nights,
            "total_amount": round(total_amount, 2)
        })
        total_party_members += 1
        
        # Add family members
        family_members = bk.get("family_members", [])
        for fm in family_members:
            guest_party_members.append({
                "booking_number": bk.get("booking_number", "N/A"),
                "room_numbers": ", ".join(bk.get("room_numbers", [])),
                "is_org": "—",  # Family members inherit from main guest
                "org_color": "—",
                "name": fm.get("name", "—"),
                "age": fm.get("age", "—"),
                "sex": fm.get("sex", "—"),
                "relationship": fm.get("relation", "—").title(),
                "address": bk.get("guest_address") or "—",  # Same as main guest
                "aadhaar_no": "—",  # Not stored for family members
                "mobile_no": fm.get("mobile", "—"),
                "check_in_date": bk["check_in_date"],
                "check_out_date": bk["check_out_date"],
                "nights": nights,
                "total_amount": "—"  # Amount is for the whole booking
            })
            total_party_members += 1
    
    return {
        "period_label": period_label,
        "start_date": start_date,
        "end_date": end_date,
        "total_party_members": total_party_members,
        "total_bookings": len(bookings),
        "total_nights": total_nights,
        "total_revenue": round(total_revenue, 2),
        "guest_party_members": guest_party_members
    }

# Health check endpoint for Render
@api_router.get("/health")
async def health_check():
    """Health check endpoint for cloud deployment monitoring"""
    try:
        # Test database connection
        await db.command("ping")
        return {
            "status": "healthy",
            "service": "SARAI Backend",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# ============= CORS & ROUTER SETUP =============
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= STARTUP & SHUTDOWN EVENTS =============
@app.on_event("startup")
async def startup_event():
    """Initialize scheduler, run migrations, and check for missed backups on startup"""
    logger.info("🚀 Application starting up...")
    
    try:
        # Run one-time database migrations
        logger.info("🔄 Running database migrations...")
        migration_result = await run_startup_migrations(db)
        
        if migration_result["status"] == "success":
            logger.info(f"✅ Migration completed: {migration_result['message']}")
        elif migration_result["status"] == "already_completed":
            logger.info("✅ Migrations already completed")
        else:
            logger.warning(f"⚠️ Migration status: {migration_result['status']}")
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}", exc_info=True)
        logger.warning("⚠️ Application will continue despite migration failure")
    
    try:
        # Initialize backup scheduler
        scheduler_service.init_scheduler(db)
        logger.info("Backup scheduler initialized")
        
        # Check for missed backups
        missed_check = await scheduler_service.check_missed_backups(db)
        if missed_check.get("missed"):
            logger.warning(f"Backup warning: {missed_check.get('message')}")
    except Exception as e:
        logger.error(f"Startup initialization error: {str(e)}")
    
    logger.info("✅ Application startup complete")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


# ============= BACKUP & RESTORE APIs =============

@api_router.post("/backups/manual/full")
async def trigger_full_backup():
    """Manually trigger a full backup"""
    try:
        metadata = await backup_service.perform_full_backup(db)
        return {
            "success": True,
            "message": "Full backup completed successfully",
            "backup": metadata
        }
    except Exception as e:
        logger.error(f"Manual full backup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@api_router.post("/backups/manual/incremental")
async def trigger_incremental_backup():
    """Manually trigger an incremental backup"""
    try:
        metadata = await backup_service.perform_incremental_backup(db)
        return {
            "success": True,
            "message": "Incremental backup completed successfully",
            "backup": metadata
        }
    except Exception as e:
        logger.error(f"Manual incremental backup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@api_router.get("/backups/status")
async def get_backup_status():
    """Get current backup status and statistics"""
    try:
        # Get last backup
        last_backup = await backup_service.get_last_backup_metadata(db)
        
        # Get total backup count
        total_backups = await db.backup_metadata.count_documents({"status": "SUCCESS"})
        
        # Get first backup date
        first_backup = await db.backup_metadata.find_one(
            {"status": "SUCCESS"},
            {"_id": 0, "timestamp": 1},
            sort=[("timestamp", 1)]
        )
        
        # Check for missed backups
        missed_check = await scheduler_service.check_missed_backups(db)
        
        # Get scheduler status
        scheduler_status = scheduler_service.get_scheduler_status()
        
        return {
            "last_backup": last_backup,
            "total_backups": total_backups,
            "first_backup_date": first_backup.get("timestamp") if first_backup else None,
            "missed_backup_warning": missed_check,
            "scheduler": scheduler_status
        }
    except Exception as e:
        logger.error(f"Error fetching backup status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/backups/history")
async def get_backup_history(limit: int = Query(50, ge=1, le=100)):
    """Get backup history"""
    try:
        history = await backup_service.get_backup_history(db, limit=limit)
        return {
            "backups": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Error fetching backup history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/backups/restore/full/{backup_id}")
async def restore_full_backup(backup_id: str):
    """Restore a specific backup (MERGE strategy)"""
    try:
        result = await restore_service.restore_full(backup_id, db)
        return {
            "success": True,
            "message": "Restore completed successfully",
            "result": result
        }
    except Exception as e:
        logger.error(f"Restore failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@api_router.post("/backups/restore/last")
async def restore_last_backup():
    """Restore the most recent successful backup"""
    try:
        result = await restore_service.restore_last_backup(db)
        return {
            "success": True,
            "message": "Last backup restored successfully",
            "result": result
        }
    except Exception as e:
        logger.error(f"Restore failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


class DateRangeRestore(BaseModel):
    start_date: str
    end_date: str

@api_router.post("/backups/restore/range")
async def restore_date_range(request: DateRangeRestore):
    """Restore all backups within a date range"""
    try:
        start = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
        
        result = await restore_service.restore_by_date_range(start, end, db)
        return {
            "success": True,
            "message": "Date range restore completed",
            "result": result
        }
    except Exception as e:
        logger.error(f"Date range restore failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


class ScheduleUpdate(BaseModel):
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(..., ge=0, le=59)

@api_router.put("/backups/schedule")
async def update_backup_schedule(request: ScheduleUpdate):
    """Update scheduled backup time"""
    try:
        result = await scheduler_service.update_backup_schedule(
            request.hour,
            request.minute,
            db
        )
        return result
    except Exception as e:
        logger.error(f"Failed to update schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/backups/restore-history")
async def get_restore_history(limit: int = Query(20, ge=1, le=50)):
    """Get restore operation history"""
    try:
        history = await restore_service.get_restore_history(db, limit=limit)
        return {
            "restores": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Error fetching restore history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= MIGRATION ENDPOINTS =============

@api_router.get("/migration/status")
async def get_migration_status():
    """Get status of one-time data sanitization migration"""
    try:
        status = await db.migration_status.find_one(
            {"migration_id": "2026_04_10_sanitize_defense_data"},
            {"_id": 0}
        )
        
        if not status:
            return {
                "status": "pending",
                "message": "Migration not yet run"
            }
        
        return status
    except Exception as e:
        logger.error(f"Error fetching migration status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/migration/download-archive")
async def download_migration_archive():
    """Download the defense data archive file"""
    try:
        # Get migration status to find archive file
        status = await db.migration_status.find_one(
            {"migration_id": "2026_04_10_sanitize_defense_data"},
            {"_id": 0}
        )
        
        if not status or not status.get("archive_file"):
            raise HTTPException(
                status_code=404,
                detail="Archive file not found. Migration may not have completed yet."
            )
        
        archive_filename = status["archive_file"]
        migrations_dir = Path(__file__).parent / "migrations"
        archive_path = migrations_dir / archive_filename
        
        if not archive_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Archive file {archive_filename} not found on server"
            )
        
        return FileResponse(
            path=str(archive_path),
            filename=archive_filename,
            media_type="text/csv"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading archive: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/migration/delete-archive")
async def delete_migration_archive():
    """Delete the migration archive file (after verification)"""
    try:
        # Get migration status to find archive file
        status = await db.migration_status.find_one(
            {"migration_id": "2026_04_10_sanitize_defense_data"},
            {"_id": 0}
        )
        
        if not status or not status.get("archive_file"):
            raise HTTPException(
                status_code=404,
                detail="Archive file not found"
            )
        
        archive_filename = status["archive_file"]
        migrations_dir = Path(__file__).parent / "migrations"
        archive_path = migrations_dir / archive_filename
        
        if archive_path.exists():
            archive_path.unlink()
            
            # Update migration status
            await db.migration_status.update_one(
                {"migration_id": "2026_04_10_sanitize_defense_data"},
                {
                    "$set": {
                        "archive_deleted": True,
                        "archive_deleted_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            return {
                "success": True,
                "message": f"Archive file {archive_filename} deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Archive file not found on server"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting archive: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= INCLUDE ROUTER (MUST BE AFTER ALL ROUTES) =============
app.include_router(api_router)
