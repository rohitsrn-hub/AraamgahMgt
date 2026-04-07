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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="E-ARMS API", description="ECSAG Automated Room Management System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    days_before: int  # Days before check-in
    charge_percent: float  # Percentage of advance to deduct

DEFAULT_RANKS = [
    "Sep/Dfr/Swr", "Nk", "Hav", "Sgt", "PO", "Nb Sub", "JWO", "CPO",
    "Sub", "WO", "CA", "SM", "MCPO", "Hony Lt or Eqvt", "Hony Capt or Eqvt", "Def Civ"
]

COMMAND_ORDER = [
    "E Command", "N Command", "W Command", "S Command", "SW Command",
    "C Command", "ARTRAC", "Army HQ", "SFC", "Navy", "Air Force", "Def Civ", "Others"
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
    ranks: List[str] = Field(default_factory=lambda: DEFAULT_RANKS.copy())
    cancellation_policy: List[dict] = Field(default_factory=lambda: [
        {"days_before": 7, "charge_percent": 0},
        {"days_before": 3, "charge_percent": 25},
        {"days_before": 1, "charge_percent": 50},
        {"days_before": 0, "charge_percent": 100}
    ])
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    ranks: Optional[List[str]] = None
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
    ranks: Optional[List[str]] = None
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
    rank: Optional[str] = None
    unit: Optional[str] = None
    contact_number: Optional[str] = None
    id_proof_type: Optional[str] = None
    id_proof_number: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GuestCreate(BaseModel):
    name: str
    rank: Optional[str] = None
    unit: Optional[str] = None
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
    guest_rank: Optional[str] = None
    guest_unit: Optional[str] = None
    guest_service_status: Optional[str] = None  # "Serving" or "Retired"
    room_ids: List[str] = []
    room_numbers: List[str] = []
    room_categories: List[str] = []
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
    service_type: Optional[str] = None
    command_hq: Optional[str] = None
    army_number: Optional[str] = None
    guest_age: Optional[int] = None
    guest_sex: Optional[str] = None
    guest_address: Optional[str] = None
    aadhaar_number: Optional[str] = None
    identity_card_number: Optional[str] = None
    wife_count: int = 0
    children_count: int = 0
    family_members: List[dict] = Field(default_factory=list)
    room_guest_mapping: List[dict] = Field(default_factory=list)  # NEW: Room-wise guest assignments
    room_rent_total: float = 0.0
    license_fee_total: float = 0.0
    notes: Optional[str] = None
    checked_in_by: Optional[str] = None
    checked_out_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BookingCreate(BaseModel):
    guest_name: str
    guest_contact: Optional[str] = None
    guest_rank: Optional[str] = None
    guest_unit: Optional[str] = None
    guest_service_status: Optional[str] = None
    room_ids: List[str]
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
    service_type: Optional[str] = None
    command_hq: Optional[str] = None
    army_number: Optional[str] = None
    guest_age: Optional[int] = None
    guest_sex: Optional[str] = None
    guest_address: Optional[str] = None
    aadhaar_number: Optional[str] = None
    identity_card_number: Optional[str] = None
    wife_count: int = 0
    children_count: int = 0
    family_members: List[dict] = Field(default_factory=list)
    notes: Optional[str] = None

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
    identity_card_number: Optional[str] = None
    guest_service_status: Optional[str] = None
    service_type: Optional[str] = None
    command_hq: Optional[str] = None
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

class CancelBookingRequest(BaseModel):
    booking_id: str
    reason: Optional[str] = None
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

async def get_room_rate(category: RoomCategory, guest_rank: Optional[str] = None) -> float:
    """Get room rate from settings, applying Def Civ rate if applicable"""
    settings = await db.app_settings.find_one({}, {"_id": 0})
    is_def_civ = guest_rank and guest_rank.strip().lower() == "def civ"
    if settings:
        if category == RoomCategory.CAT_I:
            if is_def_civ:
                return settings.get("def_civ_cat_i_rate", settings.get("cat_i_rate", 600.0))
            return settings.get("cat_i_rate", 500.0)
        else:
            if is_def_civ:
                return settings.get("def_civ_cat_ii_rate", settings.get("cat_ii_rate", 400.0))
            return settings.get("cat_ii_rate", 300.0)
    if is_def_civ:
        return 600.0 if category == RoomCategory.CAT_I else 400.0
    return 500.0 if category == RoomCategory.CAT_I else 300.0

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
    return {"message": "E-ARMS API is running", "version": "1.0.0"}

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
    
    default_cancellation_policy = [
        {"days_before": 7, "charge_percent": 0},
        {"days_before": 3, "charge_percent": 25},
        {"days_before": 1, "charge_percent": 50},
        {"days_before": 0, "charge_percent": 100}
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
        ranks=request.ranks or DEFAULT_RANKS.copy(),
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

@api_router.post("/bookings")
async def create_booking(booking: BookingCreate):
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

        rate = await get_room_rate(RoomCategory(room["category"]), booking.guest_rank)
        total_amount += rate * nights
        room_numbers.append(room["room_number"])
        room_categories.append(room["category"])

    # Create or find guest
    guest = None
    if booking.guest_contact:
        guest = await db.guests.find_one({"contact_number": booking.guest_contact}, {"_id": 0})
    if not guest:
        guest_obj = Guest(
            name=booking.guest_name,
            rank=booking.guest_rank,
            unit=booking.guest_unit,
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
        guest_rank=booking.guest_rank,
        guest_unit=booking.guest_unit,
        guest_service_status=booking.guest_service_status,
        room_ids=booking.room_ids,
        room_numbers=room_numbers,
        room_categories=room_categories,
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
        service_type=booking.service_type,
        command_hq=booking.command_hq,
        army_number=booking.army_number,
        guest_age=booking.guest_age,
        guest_sex=booking.guest_sex,
        guest_address=booking.guest_address,
        aadhaar_number=booking.aadhaar_number,
        identity_card_number=booking.identity_card_number,
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
        "identity_card_number": request.identity_card_number,
        "guest_service_status": request.guest_service_status,
        "service_type": request.service_type,
        "command_hq": request.command_hq,
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
    """Calculate refund amount based on cancellation policy"""
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    settings = await db.app_settings.find_one({}, {"_id": 0})
    cancellation_policy = settings.get("cancellation_policy", [
        {"days_before": 7, "charge_percent": 0},
        {"days_before": 3, "charge_percent": 25},
        {"days_before": 1, "charge_percent": 50},
        {"days_before": 0, "charge_percent": 100}
    ])
    
    # Calculate days until check-in
    check_in_date = datetime.fromisoformat(booking["check_in_date"].replace('Z', '+00:00'))
    if isinstance(check_in_date, datetime) and check_in_date.tzinfo is None:
        check_in_date = check_in_date.replace(tzinfo=timezone.utc)
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    check_in_date = check_in_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    days_until_checkin = (check_in_date - today).days
    
    # Find applicable charge percent
    charge_percent = 100  # Default: no refund
    for slab in sorted(cancellation_policy, key=lambda x: x["days_before"], reverse=True):
        if days_until_checkin >= slab["days_before"]:
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
        "days_until_checkin": days_until_checkin,
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

# ============= GUEST HISTORY =============

@api_router.get("/bookings/guest-history")
async def get_guest_history(
    phone_number: Optional[str] = Query(None, description="Guest phone number"),
    army_number: Optional[str] = Query(None, description="Army/Service number")
):
    """
    Get booking history for a guest by phone number or army number.
    Returns all bookings, statistics, and guest information.
    """
    if not phone_number and not army_number:
        raise HTTPException(
            status_code=400, 
            detail="Please provide either phone_number or army_number"
        )
    
    # Build query
    query = {}
    if phone_number:
        # Remove spaces and format for search (support multiple formats)
        phone_clean = phone_number.replace(" ", "").replace("+91", "").replace("-", "")
        query["$or"] = [
            {"guest_contact": {"$regex": phone_clean, "$options": "i"}},
            {"guest_contact": {"$regex": f"\\+91.*{phone_clean}", "$options": "i"}}
        ]
    elif army_number:
        query["army_number"] = {"$regex": army_number, "$options": "i"}
    
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
        "army_number": first_booking.get("army_number"),
        "guest_rank": first_booking.get("guest_rank"),
        "guest_unit": first_booking.get("guest_unit"),
        "guest_service_status": first_booking.get("guest_service_status")
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
    """Get calendar/planner data for a given month showing room bookings per day"""
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
    room_bookings = {}
    for b in bookings:
        # Get room IDs (handle both old and new format)
        rids = b.get("room_ids", [])
        if not rids and b.get("room_id"):
            rids = [b["room_id"]]
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
                if bk["check_in_date"] <= date_str and bk["check_out_date"] > date_str:
                    day_status = bk["status"]
                    day_info = {
                        "booking_id": bk["booking_id"],
                        "booking_number": bk["booking_number"],
                        "guest_name": bk["guest_name"]
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
        "guest_rank": booking.get("guest_rank"),
        "guest_unit": booking.get("guest_unit"),
        "guest_contact": booking.get("guest_contact"),
        "service_status": booking.get("guest_service_status"),
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
    
    command_map = {
        "Northern Command": "N Command", "Eastern Command": "E Command",
        "Western Command": "W Command", "Southern Command": "S Command",
        "South Western Command": "SW Command", "Central Command": "C Command",
        "ARTRAC": "ARTRAC", "SFC": "SFC", "Army HQ": "Army HQ"
    }
    
    commands = {cmd: {"guests": 0, "days": 0} for cmd in COMMAND_ORDER}
    jco_days = 0; or_days = 0; def_civ_days = 0
    extra_beds_total = 0
    
    for bk in bookings:
        checkin = date_type.fromisoformat(bk.get("check_in_date", month_start_str))
        checkout = date_type.fromisoformat(bk.get("check_out_date", month_end_str))
        eff_in = max(checkin, month_start)
        eff_out = min(checkout, month_end + timedelta(days=1))
        nights = max(0, (eff_out - eff_in).days)
        if nights == 0:
            continue
        
        rank = (bk.get("guest_rank") or "").strip().lower()
        is_def_civ = rank == "def civ"
        svc = bk.get("service_type", "")
        
        if is_def_civ:
            cmd_key = "Def Civ"
        elif svc == "Air Force":
            cmd_key = "Air Force"
        elif svc == "Navy":
            cmd_key = "Navy"
        elif svc == "SFC":
            cmd_key = "SFC"
        elif svc == "Army":
            cmd_key = command_map.get(bk.get("command_hq", ""), "Army HQ")
        else:
            cmd_key = "Others"
        
        if cmd_key in commands:
            commands[cmd_key]["guests"] += 1
            commands[cmd_key]["days"] += nights
        
        cats = bk.get("room_categories", [])
        if is_def_civ:
            def_civ_days += nights * max(1, len(cats))
        else:
            for cat in (cats or ["Cat II"]):
                if cat == "Cat I":
                    jco_days += nights
                else:
                    or_days += nights
        
        extra_beds_total += bk.get("extra_beds", 0) * nights
    
    s = settings
    cat_i_lf = s.get("cat_i_license_fee", 30)
    cat_ii_lf = s.get("cat_ii_license_fee", 15)
    def_civ_lf = s.get("def_civ_license_fee", 30)
    cat_i_rr = s.get("cat_i_room_rent", 470)
    cat_ii_rr = s.get("cat_ii_room_rent", 385)
    def_civ_rr = s.get("def_civ_room_rent", 570)
    
    room_rent_total = round(jco_days * cat_i_rr + or_days * cat_ii_rr + def_civ_days * def_civ_rr, 2)
    lf_jco = round(jco_days * cat_i_lf, 2)
    lf_or = round(or_days * cat_ii_lf, 2)
    lf_def_civ = round(def_civ_days * def_civ_lf, 2)
    total_license_fee = round(lf_jco + lf_or + lf_def_civ, 2)
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
    total_booked_days = sum(v["days"] for v in commands.values())
    avg_occ = round(total_booked_days / (total_rooms * days_in_month) * 100, 2) if total_rooms * days_in_month > 0 else 0
    
    no_shows = await db.bookings.count_documents({
        "status": "cancelled", "advance_paid": {"$gt": 0},
        "check_in_date": {"$gte": month_start_str, "$lte": month_end_str}
    })
    
    return {
        "month": month, "year": year,
        "month_name": cal_mod.month_name[month],
        "days_in_month": days_in_month, "total_rooms": total_rooms,
        "command_breakdown": [
            {"command": c, "guests": commands[c]["guests"], "days": commands[c]["days"]}
            for c in COMMAND_ORDER if commands[c]["guests"] > 0 or commands[c]["days"] > 0
        ],
        "total_guests": sum(v["guests"] for v in commands.values()),
        "total_days": total_booked_days,
        "jco_days": jco_days, "or_days": or_days, "def_civ_days": def_civ_days,
        "extra_beds_total": extra_beds_total,
        "license_fees": {
            "jco": {"days": jco_days, "rate": cat_i_lf, "total": lf_jco},
            "or": {"days": or_days, "rate": cat_ii_lf, "total": lf_or},
            "def_civ": {"days": def_civ_days, "rate": def_civ_lf, "total": lf_def_civ}
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
            "cat_i_rate": s.get("cat_i_rate", 500), "cat_ii_rate": s.get("cat_ii_rate", 400),
            "def_civ_rate": s.get("def_civ_cat_i_rate", 600),
            "cat_i_room_rent": cat_i_rr, "cat_ii_room_rent": cat_ii_rr, "def_civ_room_rent": def_civ_rr,
            "cat_i_license_fee": cat_i_lf, "cat_ii_license_fee": cat_ii_lf, "def_civ_license_fee": def_civ_lf
        }
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
            "service": "E-ARMS Backend",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
