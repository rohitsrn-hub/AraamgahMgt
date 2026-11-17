from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, Security, Request
from fastapi.responses import FileResponse, StreamingResponse, Response
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import re
import json
import uuid
import calendar
from datetime import datetime, timezone, timedelta, date as date_type
from enum import Enum

# Import backup services
from services import backup_service, restore_service, scheduler_service, corrections_service
from services.migration_service import run_startup_migrations

# Import utils
from utils import (
    validate_ifsc,
    validate_indian_mobile,
    normalize_uppercase_fields,
    generate_booking_number,
    serialize_datetime,
    serialize_doc,
    serialize_response,
    calculate_nights,
)
from utils.report_calc import (
    report_booking_query,
    effective_stay,
    build_room_maps,
    booking_financials,
    rate_components,
    effective_rate_settings,
    stay_charges,
    cancellation_refund,
    EXTRA_BED_RATE,
    RATE_FIELDS,
)
from utils.manual_occupancy_excel import build_manual_occupancy_workbook

# The guesthouse operates in IST; the backend may run in UTC (e.g. on Render).
# A calendar date meaningful to staff ("today", the default checkout date) must
# be computed in IST — a UTC date is a day behind between 00:00 and 05:30 IST.
IST = timezone(timedelta(hours=5, minutes=30))

def ist_today_str() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d")

def checkin_moment(check_in_str: str) -> datetime:
    """The actual check-in instant for a booking: 13:00 IST on the check-in
    date (standard guesthouse check-in time). Used for cancellation-slab timing
    so the hours-before-check-in count matches reality — parsing the date as
    00:00 UTC put it 7.5h early and could drop guests into a worse refund tier."""
    d = date_type.fromisoformat(str(check_in_str).split("T")[0])
    return datetime(d.year, d.month, d.day, 13, 0, tzinfo=IST)

# Import auth utilities
from utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_user_response
)

# Security scheme for JWT
security = HTTPBearer()

# Import user models
from models.user import (
    User,
    UserCreate,
    UserLogin,
    UserResponse,
    LoginResponse,
    UserRole as UserRoleModel
)

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

# ============= HELPER FUNCTIONS =============
# Note: Helper functions moved to utils/ for better organization

# Create dependency that injects db into get_current_user
async def get_current_user_with_db(credentials = Security(security)):
    """Wrapper to inject db into get_current_user"""
    from utils.auth import decode_access_token
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="User account is disabled")

    # Someone is using the app, so the server is awake: if the last full
    # backup is old, take one in the background (see scheduler_service).
    scheduler_service.maybe_trigger_backup(db)

    return user


async def require_admin_role(current_user: dict = Depends(get_current_user_with_db)) -> dict:
    """Require admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def require_staff_or_admin_role(current_user: dict = Depends(get_current_user_with_db)) -> dict:
    """Require staff or admin role"""
    role = current_user.get("role")
    if role not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="Staff or Admin access required")
    return current_user

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
    non_org_room_rent: float = 570.0
    non_org_license_fee: float = 30.0
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
    non_org_room_rent: Optional[float] = None
    non_org_license_fee: Optional[float] = None
    cat_i_rooms_count: Optional[int] = None
    cat_ii_rooms_count: Optional[int] = None
    default_advance_amount: Optional[float] = None
    colors: Optional[List[str]] = None
    cancellation_policy: Optional[List[dict]] = None

class RateScheduleEntry(BaseModel):
    effective_date: str  # YYYY-MM-DD — the check-in date from which this rate applies
    cat_i_room_rent: Optional[float] = None
    cat_i_license_fee: Optional[float] = None
    cat_ii_room_rent: Optional[float] = None
    cat_ii_license_fee: Optional[float] = None
    non_org_room_rent: Optional[float] = None
    non_org_license_fee: Optional[float] = None
    note: Optional[str] = None

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
    non_org_room_rent: float = 570.0
    non_org_license_fee: float = 30.0
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
    refund_due: Optional[float] = 0.0  # NEW: Refund amount due (from amendment or overpayment)
    refund_reason: Optional[str] = None  # NEW: Reason for refund
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
    is_amended: bool = False  # True when booking was modified by a stay extension
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
    # Early checkout notification (if guest informs at check-in)
    planned_early_checkout_date: Optional[str] = None  # YYYY-MM-DD format
    # Alternate contacts (optional, captured at check-in)
    alt_contacts: List[dict] = Field(default_factory=list)
    # The guest has arrived BEFORE the booked check-in date and staff have
    # confirmed that check-in moves to today (the extra nights are billed).
    allow_early_arrival: bool = False

class CheckOutRequest(BaseModel):
    booking_id: str
    staff_id: str
    final_payment: float = 0.0
    payment_mode: Optional[str] = None
    payment_id: Optional[str] = None
    notes: Optional[str] = None
    # Organization color (to be filled at checkout if Org guest)
    org_color: Optional[str] = None
    # Payment details
    card_last4: Optional[str] = None
    card_type: Optional[str] = None
    upi_id: Optional[str] = None
    upi_phone: Optional[str] = None
    bank_name: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_account: Optional[str] = None
    # Extra bed fields for actual usage at checkout
    extra_beds_checkout: Optional[int] = 0
    extra_bed_days: Optional[int] = 0
    # Actual checkout date (for early checkout calculation)
    actual_checkout_date: Optional[str] = None  # YYYY-MM-DD format

class CancelBookingRequest(BaseModel):
    booking_id: str
    reason: Optional[str] = None
    # None (omitted) = "apply the cancellation policy" — the server works the
    # refund out itself. This used to default to 0, so a client that failed
    # to load the refund preview cancelled the booking with NO refund queued
    # for a guest who was owed one, and nothing on screen said so.
    refund_amount: Optional[float] = None

class CloseStaleBookingRequest(BaseModel):
    staff_id: str
    actual_checkout_date: Optional[str] = None  # YYYY-MM-DD; defaults to the booking's own planned check-out

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

class ConfirmExtensionRequest(BaseModel):
    new_check_out_date: str
    amendments: List[dict]  # proposed_amendments list returned by plan-extension

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
# Note: Helper functions moved to utils/ for better organization

# ============= API ROUTES =============

# Health check
@api_router.get("/")
async def root():
    return {"message": "SARAI API is running", "version": "1.0.0"}

# ============= APP SETTINGS =============

@api_router.get("/settings")
async def get_settings(current_user: dict = Depends(get_current_user_with_db)):
    settings = await db.app_settings.find_one({}, {"_id": 0})
    if not settings:
        # Return default settings
        default = AppSettings()
        return default.model_dump()

    # Merge in whichever rate is effective TODAY, so the Settings page's
    # display/edit fields (Room Rates Summary, License Fee Breakdown) show
    # the current real rate once a scheduled change's date arrives, instead
    # of staying frozen on the old base values forever. rate_history itself
    # stays in the response untouched — booking previews resolve per their
    # own check-in date, not "today" (see frontend/src/utils/rateUtils.js).
    return {**settings, **effective_rate_settings(settings, ist_today_str())}

@api_router.post("/settings/setup")
async def complete_setup(request: SetupRequest, current_user: dict = Depends(require_admin_role)):
    """Complete first-time setup"""
    existing = await db.app_settings.find_one({})

    # Guard against a destructive re-run. Setup recreates all rooms with new
    # internal IDs (delete_many below); if bookings already reference the old
    # room IDs, wiping rooms orphans them — availability checks match by room
    # ID, so every existing booking silently stops blocking its room and the
    # same nights can be double-booked. Once setup is complete and any booking
    # exists, refuse rather than corrupt live data. Use the Settings screen to
    # change rates; room structure changes on a live DB need a deliberate
    # migration with the owner's sign-off.
    if existing and existing.get("is_setup_complete"):
        booking_count = await db.bookings.count_documents({})
        if booking_count > 0:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Setup already completed and bookings exist. Re-running setup "
                    "would recreate rooms and orphan existing bookings. Change rates "
                    "via Settings; room-structure changes need a data migration."
                ),
            )

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
        # These two were never passed through, so whatever Non-Org rate the
        # setup wizard collected was silently replaced by the 570/30 default.
        non_org_room_rent=request.non_org_room_rent,
        non_org_license_fee=request.non_org_license_fee,
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
async def update_settings(request: AppSettingsUpdate, current_user: dict = Depends(require_admin_role)):
    """Update app settings"""
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # The Settings page displays the rate in force TODAY (GET /settings merges
    # it over the base fields) and sends all six rate fields back on every
    # Save. Writing an unchanged echo into the BASE fields once a scheduled
    # rate change has taken effect re-priced every booking dated before that
    # change in every report — an admin changing only the default advance
    # turned a Rs 1,000 July stay into Rs 1,200. A rate that equals what is
    # already in force today is not an edit; leave the base untouched.
    existing = await db.app_settings.find_one({}, {"_id": 0}) or {}
    in_force_today = effective_rate_settings(existing, ist_today_str())
    for field in RATE_FIELDS:
        if field in update_data and field in in_force_today and update_data[field] == in_force_today[field]:
            del update_data[field]

    result = await db.app_settings.update_one({}, {"$set": update_data})
    # matched_count, not modified_count: Mongo reports modified_count == 0 when
    # the new values equal the old ones, so re-saving an unchanged settings form
    # used to raise a spurious "Settings not found".
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Settings not found")

    return await get_settings()

@api_router.post("/settings/reset-setup")
async def reset_setup(current_user: dict = Depends(require_admin_role)):
    """P3: Reset is_setup_complete flag to show setup wizard again"""
    result = await db.app_settings.update_one({}, {"$set": {"is_setup_complete": False}})
    if result.matched_count == 0:  # matched, not modified — see update_settings
        raise HTTPException(status_code=404, detail="Settings not found")

    return {"message": "Setup reset successfully. Please reload the page."}

@api_router.put("/settings/categories")
async def update_room_categories(categories: List[dict], current_user: dict = Depends(require_admin_role)):
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
    
    if result.matched_count == 0:  # matched, not modified — see update_settings
        raise HTTPException(status_code=404, detail="Settings not found")

    return {"message": "Room categories updated successfully", "categories": categories}

# ============= RATE SCHEDULE (date-versioned rate changes) =============
# A booking bills entirely at whichever rate was in effect on its own
# check-in date (see utils/report_calc.effective_rate_settings) — so a
# future rate change can be entered here today without touching any
# existing or currently-active booking's price. Only rooms/utils/
# report_calc.rate_components() may read these fields for money; nothing
# here computes a rupee amount itself.

@api_router.get("/settings/rate-schedule")
async def get_rate_schedule(current_user: dict = Depends(require_admin_role)):
    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}
    history = sorted(settings.get("rate_history") or [], key=lambda h: h.get("effective_date", ""))
    base_rates = {k: settings.get(k) for k in RATE_FIELDS}
    return {
        "current_base_rates": base_rates,
        "today_effective_rates": effective_rate_settings(settings, ist_today_str()),
        "scheduled_changes": history,
    }

@api_router.post("/settings/rate-schedule")
async def add_rate_schedule_entry(entry: RateScheduleEntry, current_user: dict = Depends(require_admin_role)):
    try:
        effective = date_type.fromisoformat(entry.effective_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="effective_date must be YYYY-MM-DD")

    # No backdating: every report and every booking's price is recomputed
    # live from this history on each request, not stored as a snapshot — a
    # past-dated entry would silently change already-quoted bookings and
    # historical report totals the instant it's saved.
    today = date_type.fromisoformat(ist_today_str())
    if effective < today:
        raise HTTPException(status_code=400, detail="effective_date cannot be in the past")

    provided_rates = {k: getattr(entry, k) for k in RATE_FIELDS if getattr(entry, k) is not None}
    if not provided_rates:
        raise HTTPException(status_code=400, detail="At least one rate field must be provided")
    for k, v in provided_rates.items():
        if v < 0:
            raise HTTPException(status_code=400, detail=f"{k} cannot be negative")

    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}
    existing_dates = {h.get("effective_date") for h in (settings.get("rate_history") or [])}
    if entry.effective_date in existing_dates:
        raise HTTPException(
            status_code=409,
            detail=f"A rate change is already scheduled for {entry.effective_date}. Delete it first to replace it."
        )

    doc = {
        "id": str(uuid.uuid4()),
        "effective_date": entry.effective_date,
        **provided_rates,
        "note": entry.note,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("username") or current_user.get("id"),
    }

    result = await db.app_settings.update_one({}, {"$push": {"rate_history": doc}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Settings not found")

    return {"message": "Rate change scheduled", "entry": doc}

@api_router.delete("/settings/rate-schedule/{entry_id}")
async def delete_rate_schedule_entry(entry_id: str, current_user: dict = Depends(require_admin_role)):
    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}
    entry = next((h for h in (settings.get("rate_history") or []) if h.get("id") == entry_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Scheduled rate change not found")

    # Same protection as the backdating check above: deleting an entry whose
    # date has already passed would retroactively drop every booking dated
    # on/after it back to the older rate on next calculation.
    today = date_type.fromisoformat(ist_today_str())
    effective = date_type.fromisoformat(entry["effective_date"])
    if effective <= today:
        raise HTTPException(
            status_code=409,
            detail="This rate change has already taken effect and can no longer be removed."
        )

    await db.app_settings.update_one({}, {"$pull": {"rate_history": {"id": entry_id}}})
    return {"message": "Scheduled rate change removed"}

# ============= AUTHENTICATION =============



LOGIN_WINDOW_MINUTES = 15
LOGIN_MAX_FAILURES_PER_USER = 5      # wrong passwords for one username from one address
LOGIN_MAX_FAILURES_PER_ADDRESS = 30  # wrong passwords for any usernames from one address


def _client_address(request: Request) -> str:
    """The caller's address. Behind Render's proxy request.client is the proxy
    itself, so use the LAST X-Forwarded-For entry (the one the proxy added; the
    earlier ones are supplied by the caller and can be faked)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


async def _login_retry_minutes(username: str, address: str) -> int:
    """0 if this login attempt may proceed, else minutes until it may."""
    since = (datetime.now(timezone.utc) - timedelta(minutes=LOGIN_WINDOW_MINUTES)).isoformat()
    now = datetime.now(timezone.utc)
    for query, limit in (
        ({"username": username, "address": address, "at": {"$gte": since}}, LOGIN_MAX_FAILURES_PER_USER),
        ({"address": address, "at": {"$gte": since}}, LOGIN_MAX_FAILURES_PER_ADDRESS),
    ):
        recent = await db.login_failures.find(query, {"_id": 0, "at": 1}).to_list(1000)
        if len(recent) >= limit:
            stamps = sorted((datetime.fromisoformat(r["at"]) for r in recent), reverse=True)
            unlock_at = stamps[limit - 1] + timedelta(minutes=LOGIN_WINDOW_MINUTES)
            return max(1, int((unlock_at - now).total_seconds() // 60) + 1)
    return 0


@api_router.post("/auth/login", response_model=LoginResponse)
async def login(credentials: UserLogin, request: Request):
    """
    User login endpoint

    Returns JWT access token on successful authentication.
    After 5 wrong passwords for one username (or 30 for any usernames) from one
    address within 15 minutes, further attempts from that address are refused
    for the rest of the window — slows password guessing without locking the
    real user out from anywhere else.
    """
    username = credentials.email.lower()
    address = _client_address(request)

    wait = await _login_retry_minutes(username, address)
    if wait:
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed login attempts. Please wait {wait} minute(s) and try again."
        )

    async def failed(status_code: int, detail: str):
        await db.login_failures.insert_one({"username": username, "address": address,
                                            "at": datetime.now(timezone.utc).isoformat()})
        # keep the collection small: forget anything older than a day
        await db.login_failures.delete_many(
            {"at": {"$lt": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()}})
        raise HTTPException(status_code=status_code, detail=detail)

    # Find user by username OR email (case-insensitive)
    user = await db.users.find_one(
        {
            "$or": [
                {"username": credentials.email.lower()},
                {"email": credentials.email.lower()}
            ]
        }, 
        {"_id": 0}
    )
    
    if not user:
        await failed(401, "Invalid username or password")
    
    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        await failed(401, "Invalid username or password")
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=403,
            detail="Account is disabled. Contact administrator."
        )

    # A correct login clears this username's failures from this address
    await db.login_failures.delete_many({"username": username, "address": address})
    
    # Update last login
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Create JWT token
    access_token = create_access_token(
        data={
            "user_id": user["id"],
            "email": user["email"],
            "role": user["role"]
        }
    )
    
    # Return token and user info
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            role=user["role"],
            is_active=user["is_active"],
            created_at=user["created_at"],
            last_login=user.get("last_login")
        )
    )


@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user_with_db)):
    """
    Get current logged-in user information
    
    Requires: Valid JWT token in Authorization header
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        role=current_user["role"],
        is_active=current_user["is_active"],
        created_at=current_user["created_at"],
        last_login=current_user.get("last_login")
    )


@api_router.post("/auth/logout")
async def logout():
    """
    Logout endpoint (stateless - client should delete token)
    
    Returns success message
    """
    return {"message": "Logged out successfully. Please delete your token."}


# ============= USER MANAGEMENT (ADMIN ONLY) =============

@api_router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_admin_role)
):
    """
    Create a new user (Admin only)
    
    Requires: Admin role
    """
    # Validate role
    user_data.validate_role()

    # Normalize the username to lowercase. Login always looks up by the
    # lowercased value, so storing any capital letter (e.g. "Rakesh") made the
    # account permanently unreachable. Store and dedupe case-insensitively.
    username = user_data.email.strip().lower()

    # Check if username already exists (case-insensitive)
    existing = await db.users.find_one({"email": username}, {"_id": 0})
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # Create user
    new_user = User(
        id=str(uuid.uuid4()),
        email=username,  # Username (normalized lowercase)
        password_hash=hash_password(user_data.password),
        name=user_data.name,
        role=user_data.role,
        is_active=True,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    
    # Insert into database
    await db.users.insert_one(new_user.model_dump())
    
    # Return user (without password_hash)
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        role=new_user.role,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        last_login=None
    )


@api_router.get("/users", response_model=List[UserResponse])
async def list_users(current_user: dict = Depends(require_admin_role)):
    """
    List all users (Admin only)
    
    Requires: Admin role
    """
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(100)
    
    return [
        UserResponse(
            id=u["id"],
            email=u["email"],
            name=u["name"],
            role=u["role"],
            is_active=u.get("is_active", True),
            created_at=u["created_at"],
            last_login=u.get("last_login")
        )
        for u in users
    ]


@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update_data: dict,
    current_user: dict = Depends(require_admin_role)
):
    """
    Update a user (Admin only)
    
    Requires: Admin role
    """
    # Prevent admin from disabling themselves
    if user_id == current_user["id"] and not update_data.get("is_active", True):
        raise HTTPException(
            status_code=400,
            detail="Cannot disable your own account"
        )
    
    update_fields = {}
    
    if "name" in update_data:
        update_fields["name"] = update_data["name"]
    
    if "role" in update_data:
        if update_data["role"] not in ["admin", "staff", "viewer"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        update_fields["role"] = update_data["role"]
    
    if "is_active" in update_data:
        update_fields["is_active"] = update_data["is_active"]
    
    if "password" in update_data:
        # The reset-password screen and user creation both require 8+ characters;
        # this path accepted anything, down to a single character.
        if not isinstance(update_data["password"], str) or len(update_data["password"]) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        update_fields["password_hash"] = hash_password(update_data["password"])
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Update user
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get updated user
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    
    return UserResponse(**user)


@api_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin_role)
):
    """
    Delete a user (Admin only)
    
    Requires: Admin role
    """
    # Prevent admin from deleting themselves
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )
    
    result = await db.users.delete_one({"id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}


@api_router.put("/users/{user_id}/password")
async def reset_user_password(
    user_id: str,
    password_data: dict,
    current_user: dict = Depends(require_admin_role)
):
    """
    Reset a user's password (Admin only)
    
    Requires: Admin role
    Body: {"new_password": "new_password_here"}
    """
    new_password = password_data.get("new_password")
    
    if not new_password:
        raise HTTPException(status_code=400, detail="new_password is required")
    
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Hash the new password
    password_hash = hash_password(new_password)
    
    # Update user's password
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"password_hash": password_hash}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Password reset successfully"}

# ============= ROOMS =============

@api_router.get("/rooms", response_model=List[dict])
async def get_rooms(category: Optional[RoomCategory] = None, status: Optional[RoomStatus] = None, current_user: dict = Depends(get_current_user_with_db)):
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
    exclude_booking_id: Optional[str] = Query(None, description="Booking ID to exclude from conflict check"),
    current_user: dict = Depends(get_current_user_with_db)
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
async def get_room(room_id: str, current_user: dict = Depends(get_current_user_with_db)):
    room = await db.rooms.find_one({"id": room_id}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@api_router.post("/rooms")
async def create_room(room: RoomCreate, current_user: dict = Depends(require_admin_role)):
    existing = await db.rooms.find_one({"room_number": room.room_number}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail=f"Room {room.room_number} already exists")

    room_obj = Room(**room.model_dump())
    doc = serialize_doc(room_obj.model_dump())
    await db.rooms.insert_one(doc)
    # Return the created room by fetching it back without _id
    created_room = await db.rooms.find_one({"id": doc["id"]}, {"_id": 0})
    return created_room

@api_router.put("/rooms/{room_id}")
async def update_room(room_id: str, update: RoomUpdate, current_user: dict = Depends(require_staff_or_admin_role)):
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    # Staff may change a room's status (available / maintenance) — a daily task.
    # Renaming a room or changing its category rewrites how every earlier
    # booking of it is listed and priced in reports (a renamed room's old
    # revenue drops out of Room Occupancy), so that is administrator-only.
    if current_user.get("role") != "admin" and ({"room_number", "category", "floor"} & set(update_data)):
        raise HTTPException(status_code=403, detail="Only an administrator can rename a room or change its category or floor")

    if "room_number" in update_data:
        collision = await db.rooms.find_one(
            {"room_number": update_data["room_number"], "id": {"$ne": room_id}}, {"_id": 0}
        )
        if collision:
            raise HTTPException(status_code=400, detail=f"Room {update_data['room_number']} already exists")

    result = await db.rooms.update_one({"id": room_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Room not found")

    return await get_room(room_id)

@api_router.delete("/rooms/{room_id}")
async def delete_room(room_id: str, current_user: dict = Depends(require_admin_role)):
    # Refuse to delete a room a currently-active booking still holds — those
    # bookings' availability checks resolve the room live from this
    # collection, so deleting it out from under a confirmed/checked-in guest
    # would silently break their booking. Past bookings (checked_out/
    # cancelled) already store their own room_numbers/room_categories on the
    # booking document itself, so they don't depend on the room still
    # existing here — otherwise no room actually used by this guesthouse
    # could ever be deleted.
    referencing = await db.bookings.find_one({
        "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
        "$or": [{"room_ids": room_id}, {"room_id": room_id}],
    }, {"_id": 0})
    if referencing:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete this room — active booking {referencing.get('booking_number', referencing.get('id'))} references it."
        )

    result = await db.rooms.delete_one({"id": room_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"message": "Room deleted successfully"}

@api_router.post("/rooms/find-optimal-combination")
async def find_optimal_room_combination(
    check_in: str = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: str = Query(..., description="Check-out date (YYYY-MM-DD)"),
    num_rooms: int = Query(..., ge=1, description="Number of rooms needed per night"),
    exclude_booking_id: Optional[str] = Query(None, description="Booking ID to exclude from conflict check"),
    current_user: dict = Depends(require_staff_or_admin_role)
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


# ============= STAY EXTENSION =============

def _last_night_rooms(b: dict, room_maps: dict) -> list:
    """[{id, room_number, category}] for the rooms the guest occupies on the
    LAST booked night — the rooms an extension continues in. For a plain
    booking that is simply all of its rooms; for a mix & match booking it is
    the final segment's rooms, not every room used at any point in the stay
    (extending a guest who moved from A to B must extend B only)."""
    segments = sorted((b.get("room_segments") or []), key=lambda seg: seg.get("night_date") or "")
    if segments and segments[-1].get("rooms"):
        return [
            {"id": r.get("id"), "room_number": r.get("room_number"), "category": r.get("category")}
            for r in segments[-1]["rooms"]
        ]
    ids = b.get("room_ids") or ([b["room_id"]] if b.get("room_id") else [])
    numbers = b.get("room_numbers") or []
    categories = b.get("room_categories") or []
    rooms = []
    for i, rid in enumerate(ids):
        number = numbers[i] if i < len(numbers) else room_maps["id_to_number"].get(rid)
        category = categories[i] if i < len(categories) else room_maps["id_to_category"].get(rid)
        rooms.append({"id": rid, "room_number": number, "category": category})
    return rooms


def _booking_with_extension(b: dict, new_check_out: str, room_maps: dict, extension_rooms: Optional[list] = None) -> dict:
    """A copy of booking `b` exactly as it will be stored once extended to
    new_check_out — in the same rooms (extension_rooms=None) or in different
    ones. plan-extension prices this copy and confirm-extension saves it, so
    the quoted price, the saved booking and every later report all come from
    one description of the stay."""
    old_out = date_type.fromisoformat(b["check_out_date"])
    new_out = date_type.fromisoformat(new_check_out)
    extension_nights = [(old_out + timedelta(days=i)).isoformat() for i in range(max(0, (new_out - old_out).days))]

    after = dict(b)
    after["check_out_date"] = new_check_out
    segments = list(b.get("room_segments") or [])
    current_rooms = _last_night_rooms(b, room_maps)

    if extension_rooms is None:
        # A mix & match booking's reports are driven by its nightly
        # segments, so the new nights need segments too — without them the
        # extension was charged to the guest but never reached any report.
        if segments:
            after["room_segments"] = segments + [{"night_date": n, "rooms": current_rooms} for n in extension_nights]
        return after

    if not segments:
        check_in = date_type.fromisoformat(b["check_in_date"])
        segments = [
            {"night_date": (check_in + timedelta(days=i)).isoformat(), "rooms": current_rooms}
            for i in range((old_out - check_in).days)
        ]
    after["room_segments"] = segments + [{"night_date": n, "rooms": extension_rooms} for n in extension_nights]
    after["has_room_changes"] = True

    # room_ids / room_numbers / room_categories are parallel lists read by
    # position everywhere else. Keep them aligned, in order of first use.
    # (These were built from three separate set()s, which both scrambled the
    # order and collapsed two rooms of the same category into one entry.)
    ordered = {}
    existing_ids = b.get("room_ids") or []
    existing_numbers = b.get("room_numbers") or []
    existing_categories = b.get("room_categories") or []
    for i, rid in enumerate(existing_ids):
        ordered.setdefault(rid, {
            "id": rid,
            "room_number": existing_numbers[i] if i < len(existing_numbers) else room_maps["id_to_number"].get(rid),
            "category": existing_categories[i] if i < len(existing_categories) else room_maps["id_to_category"].get(rid),
        })
    for r in extension_rooms:
        ordered.setdefault(r["id"], r)
    after["room_ids"] = list(ordered.keys())
    after["room_numbers"] = [r["room_number"] for r in ordered.values()]
    after["room_categories"] = [r["category"] for r in ordered.values()]
    return after


def _extension_charge(settings: dict, room_maps: dict, before: dict, after: dict) -> float:
    """Price of an extension = room charges of the extended stay minus room
    charges of the stay as it stands, both from report_calc.stay_charges() —
    so the extra nights are priced per room exactly as check-in, check-out
    and the reports price them: the rate locked in at the ORIGINAL check-in
    date (an Extend never re-prices), the per-room Non-Org override, and the
    nightly room plan of a mix & match stay. plan_extension and
    confirm_extension both call this so the price shown for approval and the
    price actually charged can't differ."""
    return round(
        stay_charges(after, settings, room_maps)["total"] - stay_charges(before, settings, room_maps)["total"], 2
    )


def _booking_in_rooms(b: dict, rooms: list) -> dict:
    """A copy of booking `b` moved into `rooms` for its whole stay."""
    moved = dict(b)
    moved["room_ids"] = [r["id"] for r in rooms]
    moved["room_numbers"] = [r["room_number"] for r in rooms]
    moved["room_categories"] = [r["category"] for r in rooms]
    moved["room_segments"] = None
    moved["has_room_changes"] = False
    # Carry any per-room billing override across to the replacement room in
    # the same position, so a room billed Non-Org stays billed Non-Org.
    mapping = [dict(m) for m in (b.get("room_guest_mapping") or [])]
    if mapping and len(mapping) == len(rooms):
        for m, r in zip(mapping, rooms):
            m["room_id"], m["room_number"], m["room_category"] = r["id"], r["room_number"], r["category"]
        moved["room_guest_mapping"] = mapping
    return moved


def _booking_with_early_arrival(b: dict, new_check_in: str) -> dict:
    """A copy of booking `b` as it will be stored once its check-in date moves
    EARLIER to new_check_in (guest arrived before the booked date). For a mix &
    match booking, the extra nights go in the rooms of its first night — the
    nightly plan is what the reports read."""
    old_in = date_type.fromisoformat(str(b["check_in_date"]).split("T")[0])
    new_in = date_type.fromisoformat(new_check_in)
    after = dict(b)
    after["check_in_date"] = new_check_in
    segments = sorted(b.get("room_segments") or [], key=lambda seg: seg.get("night_date") or "")
    if segments:
        first_rooms = segments[0].get("rooms") or []
        early = [{"night_date": (new_in + timedelta(days=i)).isoformat(), "rooms": first_rooms}
                 for i in range(max(0, (old_in - new_in).days))]
        after["room_segments"] = early + segments
    return after


@api_router.post("/bookings/{booking_id}/plan-extension")
async def plan_extension(booking_id: str, new_check_out_date: str = Query(..., description="New checkout date YYYY-MM-DD"), current_user: dict = Depends(require_staff_or_admin_role)):
    from datetime import date as date_type, timedelta

    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["status"] != BookingStatus.CHECKED_IN.value:
        raise HTTPException(status_code=400, detail="Can only extend checked-in bookings")

    extension_start = booking["check_out_date"]
    extension_end = new_check_out_date

    try:
        date_type.fromisoformat(extension_end)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="New checkout date must be a valid YYYY-MM-DD date")
    if extension_end <= extension_start:
        raise HTTPException(status_code=400, detail="New checkout date must be after current checkout date")

    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}
    room_maps = build_room_maps(await db.rooms.find({}, {"_id": 0}).to_list(500))

    # The rooms the guest is in on their last booked night — the ones the
    # extension continues in (for a mix & match stay, NOT every room used).
    current_rooms = _last_night_rooms(booking, room_maps)
    current_room_ids = [r["id"] for r in current_rooms]
    current_room_numbers = [r["room_number"] for r in current_rooms]
    current_room_categories = [r["category"] for r in current_rooms]
    num_rooms = len(current_rooms) or booking.get("num_rooms", 1)

    old_total = booking.get("total_amount", 0.0)
    ext_cost = _extension_charge(
        settings, room_maps, booking, _booking_with_extension(booking, extension_end, room_maps)
    )
    new_total_main = round(old_total + ext_cost, 2)

    main_amendment = {
        "booking_id": booking_id,
        "booking_number": booking["booking_number"],
        "guest_name": booking["guest_name"],
        "change_type": "extension",
        "old_check_out": extension_start,
        "new_check_out": extension_end,
        "old_total": old_total,
        "new_total": new_total_main,
        "room_ids": current_room_ids,
        "room_numbers": current_room_numbers,
        "room_categories": current_room_categories,
    }

    # PHASE 1 — current rooms free during extension?
    # Match both room_ids (current) and the legacy singular room_id, or a legacy
    # booking holding one of these rooms would be missed and the extension would
    # wrongly believe the room is free.
    conflicts = await db.bookings.find({
        "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
        "$or": [
            {"room_ids": {"$in": current_room_ids}},
            {"room_id": {"$in": current_room_ids}},
        ],
        "check_in_date": {"$lt": extension_end},
        "check_out_date": {"$gt": extension_start},
        "id": {"$ne": booking_id},
    }, {"_id": 0}).to_list(200)

    if not conflicts:
        return {
            "status": "same_room",
            "message": f"Room(s) {', '.join(current_room_numbers)} free — extension available",
            "proposed_amendments": [main_amendment],
        }

    # PHASE 2 / 2.5 — backtracking CSP to find valid room reassignments for ALL conflicting bookings
    # Pre-compute: for each conflicting booking, rooms that are free from non-conflicting bookings
    conflicting_ids = [c["id"] for c in conflicts]
    all_rooms_p2 = await db.rooms.find({"status": {"$ne": RoomStatus.MAINTENANCE.value}}, {"_id": 0}).to_list(200)
    target_room_id_set = set(current_room_ids)

    candidates_per_booking: dict = {}  # cb_id -> list of room objects
    for cb in conflicts:
        blocking_query = {
            "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
            "check_in_date": {"$lt": cb["check_out_date"]},
            "check_out_date": {"$gt": cb["check_in_date"]},
            "id": {"$nin": conflicting_ids + [booking_id]},
        }
        blocking = await db.bookings.find(blocking_query, {"_id": 0}).to_list(200)
        blocked_by_others: set = set()
        for bb in blocking:
            rids = bb.get("room_ids") or ([bb["room_id"]] if bb.get("room_id") else [])
            blocked_by_others.update(rids)

        candidates_per_booking[cb["id"]] = [
            r for r in all_rooms_p2
            if r["id"] not in blocked_by_others and r["id"] not in target_room_id_set
        ]

    # MRV ordering: try bookings with fewest candidates first → prune early
    sorted_conflicts = sorted(conflicts, key=lambda cb: len(candidates_per_booking[cb["id"]]))

    def dates_overlap(cb1: dict, cb2: dict) -> bool:
        return cb1["check_in_date"] < cb2["check_out_date"] and cb1["check_out_date"] > cb2["check_in_date"]

    csp_assignment: dict = {}  # cb_id -> [room objects]

    from itertools import combinations as _combinations

    def try_assign(idx: int) -> bool:
        if idx == len(sorted_conflicts):
            return True
        cb = sorted_conflicts[idx]
        cb_id = cb["id"]
        n = cb.get("num_rooms", len(cb.get("room_ids", []))) or 1
        candidates = candidates_per_booking[cb_id]

        # Rooms already committed to overlapping bookings in current assignment
        taken: set = set()
        for prev_id, prev_rooms in csp_assignment.items():
            prev_cb = next(c for c in sorted_conflicts if c["id"] == prev_id)
            if dates_overlap(cb, prev_cb):
                taken.update(r["id"] for r in prev_rooms)

        free = [r for r in candidates if r["id"] not in taken]
        if len(free) < n:
            return False

        # Prefer category-matching rooms (reduces cost changes for reassigned guest)
        orig_cats = set(cb.get("room_categories", []))
        free.sort(key=lambda r: (0 if r["category"] in orig_cats else 1, r["room_number"]))

        for combo in _combinations(free, n):
            csp_assignment[cb_id] = list(combo)
            if try_assign(idx + 1):
                return True
            del csp_assignment[cb_id]

        return False

    if try_assign(0):
        proposed_shifts = []
        for cb in conflicts:
            chosen = csp_assignment[cb["id"]]
            chosen_ids = [r["id"] for r in chosen]
            chosen_nums = [r["room_number"] for r in chosen]
            chosen_cats = [r["category"] for r in chosen]
            new_cost_cb = stay_charges(_booking_in_rooms(cb, chosen), settings, room_maps)["total"]
            proposed_shifts.append({
                "booking_id": cb["id"],
                "booking_number": cb["booking_number"],
                "guest_name": cb["guest_name"],
                "change_type": "room_reassignment",
                "check_in_date": cb["check_in_date"],
                "check_out_date": cb["check_out_date"],
                "old_room_ids": cb.get("room_ids", []),
                "new_room_ids": chosen_ids,
                "old_room_numbers": cb.get("room_numbers", []),
                "new_room_numbers": chosen_nums,
                "old_room_categories": cb.get("room_categories", []),
                "new_room_categories": chosen_cats,
                "old_total": cb.get("total_amount", 0.0),
                "new_total": new_cost_cb,
            })
        return {
            "status": "shifted",
            "message": f"Extension possible — {len(proposed_shifts)} conflicting booking(s) will be reassigned to free up the room",
            "proposed_amendments": [main_amendment] + proposed_shifts,
        }

    # PHASE 3 — guest moves to a different room for extension (room segments)
    blocking_ext = await db.bookings.find({
        "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
        "check_in_date": {"$lt": extension_end},
        "check_out_date": {"$gt": extension_start},
        "id": {"$ne": booking_id},
    }, {"_id": 0}).to_list(200)

    blocked_ext_ids = set()
    for bb in blocking_ext:
        blocked_ext_ids.update(bb.get("room_ids", []))

    all_rooms_p3 = await db.rooms.find({"status": {"$ne": RoomStatus.MAINTENANCE.value}}, {"_id": 0}).to_list(200)
    alt_candidates = [
        r for r in all_rooms_p3
        if r["id"] not in blocked_ext_ids and r["id"] not in set(current_room_ids)
    ]

    if len(alt_candidates) >= num_rooms:
        orig_cats_set = set(current_room_categories)
        alt_candidates.sort(key=lambda r: (0 if r["category"] in orig_cats_set else 1))
        alt_rooms = alt_candidates[:num_rooms]
        alt_room_ids = [r["id"] for r in alt_rooms]
        alt_room_numbers = [r["room_number"] for r in alt_rooms]
        alt_room_cats = [r["category"] for r in alt_rooms]

        alt_rooms_seg = [{"id": r["id"], "room_number": r["room_number"], "category": r["category"]} for r in alt_rooms]
        ext_cost_alt = _extension_charge(
            settings, room_maps, booking,
            _booking_with_extension(booking, extension_end, room_maps, alt_rooms_seg),
        )
        new_total_alt = round(old_total + ext_cost_alt, 2)

        p3_amendment = {
            **main_amendment,
            "change_type": "extension_room_change",
            "new_total": new_total_alt,
            "extension_room_ids": alt_room_ids,
            "extension_room_numbers": alt_room_numbers,
            "extension_room_categories": alt_room_cats,
        }
        return {
            "status": "other_room",
            "message": f"Same-room extension not possible. Extension available by moving to room(s): {', '.join(alt_room_numbers)}",
            "proposed_amendments": [p3_amendment],
        }

    # PHASE 4 — impossible
    return {
        "status": "impossible",
        "message": "Extension not possible — no rooms available for the requested period",
        "proposed_amendments": [],
    }


@api_router.post("/bookings/{booking_id}/confirm-extension")
async def confirm_extension(booking_id: str, request: ConfirmExtensionRequest, current_user: dict = Depends(require_staff_or_admin_role)):
    from datetime import datetime, timezone, timedelta, date as date_type

    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["status"] != BookingStatus.CHECKED_IN.value:
        raise HTTPException(status_code=400, detail="Can only confirm extension for checked-in bookings")

    now = datetime.now(timezone.utc)
    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}
    room_maps = build_room_maps(await db.rooms.find({}, {"_id": 0}).to_list(500))

    def _validated_new_check_out(amendment: dict, old_check_out: str) -> str:
        new_check_out = amendment.get("new_check_out")
        try:
            date_type.fromisoformat(new_check_out)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Extension has an invalid new checkout date")
        if new_check_out <= old_check_out:
            raise HTTPException(status_code=400, detail="New checkout date must be after current checkout date")
        return new_check_out

    def _money_update(before: dict, after: dict) -> tuple:
        """(extension charge, fields to store) for a booking going from
        `before` to `after`. The stored room/licence totals are refreshed too
        so nothing downstream ever sees a pre-extension figure."""
        ext_cost = _extension_charge(settings, room_maps, before, after)
        after_charges = stay_charges(after, settings, room_maps)
        new_total = round((before.get("total_amount", 0.0) or 0.0) + ext_cost, 2)
        return ext_cost, {
            "total_amount": new_total,
            # Add the extension to the existing balance instead of rebuilding
            # it as total - advance: the balance also carries the check-in
            # extra-bed charge, which the rebuild silently dropped.
            "balance_amount": round((before.get("balance_amount", 0.0) or 0.0) + ext_cost, 2),
            "room_rent_total": after_charges["room_rent"],
            "license_fee_total": after_charges["license_fee"],
        }

    # The amendments were computed by plan-extension against room availability
    # at that moment; a booking made by someone else in the gap between plan and
    # confirm could now conflict. Re-validate here — but exclude every booking in
    # THIS amendment set from the conflict check, since they are being moved
    # together as one coordinated shuffle (the solver may reassign B to free a
    # room for A). Only an outside booking should block the confirm.
    amended_ids = {a.get("booking_id") for a in request.amendments if a.get("booking_id")}
    amended_ids.add(booking_id)

    async def _extension_conflict(room_ids_to_check, window_start, window_end):
        for rid in room_ids_to_check:
            conflicting = await db.bookings.find_one({
                "id": {"$nin": list(amended_ids)},
                "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
                "$or": [{"room_ids": rid}, {"room_id": rid}],
                "check_in_date": {"$lt": window_end},
                "check_out_date": {"$gt": window_start},
            })
            if conflicting:
                room = await db.rooms.find_one({"id": rid}, {"_id": 0})
                name = room.get("room_number") if room else rid
                raise HTTPException(
                    status_code=409,
                    detail=f"Room {name} was booked by another guest since planning; extension cannot be confirmed. Re-plan the extension."
                )

    async def _rooms_by_id(room_ids):
        """Fetch room_number/category fresh from the rooms collection, keyed
        by id. Money and room labels are derived from this, never from the
        client-supplied amendment — an amendment is a proposal the client
        echoes back, not a source of truth for what a room actually is."""
        out = {}
        for rid in room_ids:
            room = await db.rooms.find_one({"id": rid}, {"_id": 0})
            out[rid] = room or {"id": rid, "room_number": rid, "category": "Cat I"}
        return out

    async def _release_room_if_unclaimed(room_id, exclude_booking_id):
        other = await db.bookings.find_one({
            "id": {"$ne": exclude_booking_id},
            "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
            "$or": [{"room_ids": room_id}, {"room_id": room_id}],
        })
        if not other:
            await db.rooms.update_one({"id": room_id}, {"$set": {"status": RoomStatus.AVAILABLE.value}})

    for amendment in request.amendments:
        bid = amendment.get("booking_id")
        if not bid:
            continue
        b = await db.bookings.find_one({"id": bid}, {"_id": 0})
        if not b:
            continue

        change_type = amendment.get("change_type", "")
        # updated_at must be an ISO string like every other timestamp in this
        # app — a raw datetime object here is exactly what made a full backup
        # crash with "Object of type datetime is not JSON serializable" the
        # first time it reached one of these documents.
        update: dict = {"updated_at": now.isoformat(), "is_amended": True}
        changes = []

        if change_type == "extension":
            # New nights added in the rooms the guest is already in. Old
            # checkout and rooms come from the booking itself (b), not the
            # amendment, so the charge can't be manipulated by a tampered
            # request.
            old_check_out = b["check_out_date"]
            new_check_out = _validated_new_check_out(amendment, old_check_out)
            await _extension_conflict(
                [r["id"] for r in _last_night_rooms(b, room_maps)],
                old_check_out, new_check_out,
            )
            after = _booking_with_extension(b, new_check_out, room_maps)
            old_total = b.get("total_amount", 0.0)
            ext_cost, money = _money_update(b, after)

            update["check_out_date"] = new_check_out
            update.update(money)
            if after.get("room_segments"):
                update["room_segments"] = after["room_segments"]
            changes = [
                f"Stay extended: checkout {old_check_out} → {new_check_out}",
                f"Amount: ₹{old_total:.0f} → ₹{money['total_amount']:.0f}",
            ]

        elif change_type == "room_reassignment":
            # Guest moved to new rooms for the whole stay → those rooms must be
            # free for the booking's full window (excluding the co-moved set).
            new_room_ids = amendment["new_room_ids"]
            await _extension_conflict(new_room_ids, b["check_in_date"], b["check_out_date"])

            old_room_ids = b.get("room_ids", []) or ([b["room_id"]] if b.get("room_id") else [])
            new_rooms_by_id = await _rooms_by_id(new_room_ids)
            moved = _booking_in_rooms(b, [
                {"id": rid, "room_number": new_rooms_by_id[rid]["room_number"], "category": new_rooms_by_id[rid]["category"]}
                for rid in new_room_ids
            ])
            new_room_numbers = moved["room_numbers"]

            old_total = b.get("total_amount", 0.0)
            moved_charges = stay_charges(moved, settings, room_maps)
            new_total = moved_charges["total"]

            update["room_ids"] = moved["room_ids"]
            update["room_numbers"] = moved["room_numbers"]
            update["room_categories"] = moved["room_categories"]
            update["room_segments"] = None
            update["has_room_changes"] = False
            if moved.get("room_guest_mapping"):
                update["room_guest_mapping"] = moved["room_guest_mapping"]
            update["total_amount"] = new_total
            update["balance_amount"] = round((b.get("balance_amount", 0.0) or 0.0) + (new_total - old_total), 2)
            update["room_rent_total"] = moved_charges["room_rent"]
            update["license_fee_total"] = moved_charges["license_fee"]
            changes = [
                f"Room reassigned: {', '.join(b.get('room_numbers', []))} → {', '.join(new_room_numbers)}",
                f"Amount: ₹{old_total:.0f} → ₹{new_total:.0f}",
            ]

            # Only touch the rooms' live "occupied" flag if THIS guest is
            # actually in the building. The booking being moved here is the
            # one that was in the extending guest's way — almost always a
            # future, not-yet-arrived (confirmed) booking — and this used to
            # mark its new rooms "occupied" on the spot regardless, so an
            # empty room showed as occupied until someone noticed.
            if b.get("status") == BookingStatus.CHECKED_IN.value:
                for rid in old_room_ids:
                    await _release_room_if_unclaimed(rid, bid)
                for rid in new_room_ids:
                    await db.rooms.update_one({"id": rid}, {"$set": {"status": RoomStatus.OCCUPIED.value}})

        elif change_type == "extension_room_change":
            # Extension nights are served by DIFFERENT rooms → those extension
            # rooms must be free for the extension window (excluding co-moved set).
            extension_room_ids = amendment["extension_room_ids"]
            old_check_out = b["check_out_date"]
            new_check_out = _validated_new_check_out(amendment, old_check_out)
            await _extension_conflict(extension_room_ids, old_check_out, new_check_out)

            ext_rooms_by_id = await _rooms_by_id(extension_room_ids)
            ext_rooms_seg = [
                {"id": rid, "room_number": ext_rooms_by_id[rid]["room_number"], "category": ext_rooms_by_id[rid]["category"]}
                for rid in extension_room_ids
            ]

            # Original period stays in the current rooms, extension nights
            # go in the new rooms — recorded as nightly room_segments.
            after = _booking_with_extension(b, new_check_out, room_maps, ext_rooms_seg)
            old_total = b.get("total_amount", 0.0)
            ext_cost, money = _money_update(b, after)

            update["check_out_date"] = new_check_out
            update["room_segments"] = after["room_segments"]
            update["has_room_changes"] = True
            update["room_ids"] = after["room_ids"]
            update["room_numbers"] = after["room_numbers"]
            update["room_categories"] = after["room_categories"]
            update.update(money)
            changes = [
                f"Stay extended: checkout {old_check_out} → {new_check_out}",
                f"Extension rooms: {', '.join(r['room_number'] for r in ext_rooms_seg)} (different from original {', '.join(b.get('room_numbers', []))})",
                f"Amount: ₹{old_total:.0f} → ₹{money['total_amount']:.0f}",
            ]
            # Note: the extension rooms only take over from the old checkout
            # date (a future date relative to "now" in the common case), and
            # room.status has no time dimension — it's a single current-state
            # flag. Flipping extension_room_ids to "occupied" immediately
            # would incorrectly mark them occupied before the guest has
            # actually moved in. Room status for segmented stays is
            # intentionally left to check-in/check-out to manage;
            # room_segments already tracks the true night-by-night assignment
            # for reports and billing.
        else:
            continue

        amendment_log = b.get("amendment_log", [])
        amendment_log.append({
            "amended_at": now.isoformat(),
            "changes": changes,
            "reason": f"Stay extension to {request.new_check_out_date}",
            "source": "extension",
        })
        update["amendment_log"] = amendment_log

        await db.bookings.update_one({"id": bid}, {"$set": update})

    return {"success": True, "message": f"Extension confirmed — all bookings updated"}


# ============= BOOKINGS =============

@api_router.get("/bookings", response_model=List[dict])
async def get_bookings(
    status: Optional[BookingStatus] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user_with_db)
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

# Must be registered BEFORE /bookings/{booking_id} below — FastAPI/Starlette
# matches routes in registration order, and {booking_id} matches ANY single
# path segment including the literal word "stale-confirmed". Registered
# after it, every call here was being swallowed by get_booking() instead,
# which looked up a booking literally named "stale-confirmed", found none,
# and returned 404 "Booking not found" — silently breaking both the
# Bookings page's "needs attention" banner and anything that called this
# endpoint, every single time, since the day it was added.
@api_router.get("/bookings/stale-confirmed")
async def list_stale_confirmed_bookings(current_user: dict = Depends(require_staff_or_admin_role)):
    """Confirmed bookings whose planned checkout has already passed and that
    were never actually checked in — the entry was made (often via Migration
    Mode, for a stay already over) but no one ran it through the real
    check-in/checkout flow. Left alone, these sit at "confirmed" forever and
    still count as occupying their room for their full original window in
    every report, which can overlap a different, real guest later placed in
    that same room and inflate that room's occupancy numbers.

    Powers the "needs attention" banner on the Bookings page so staff see
    this on every visit instead of it only surfacing during an audit.
    """
    today = ist_today_str()
    candidates = await db.bookings.find({
        "status": "confirmed",
        "actual_check_in": None,
        "check_out_date": {"$lt": today},
    }, {"_id": 0}).sort("check_out_date", 1).to_list(200)

    result = []
    for bk in candidates:
        checkout_date = date_type.fromisoformat(bk["check_out_date"])
        result.append({
            "id": bk.get("id"),
            "booking_number": bk.get("booking_number"),
            "guest_name": bk.get("guest_name"),
            "rooms": bk.get("room_numbers") or ([bk["room_number"]] if bk.get("room_number") else []),
            "check_in_date": bk.get("check_in_date"),
            "check_out_date": bk.get("check_out_date"),
            "days_since_planned_checkout": (date_type.fromisoformat(today) - checkout_date).days,
        })
    return {"as_of": today, "count": len(result), "bookings": result}

@api_router.get("/bookings/{booking_id}")
async def get_booking(booking_id: str, current_user: dict = Depends(get_current_user_with_db)):
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

    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}

    # Extract all unique room IDs from segments
    all_room_ids = set()
    for segment in room_segments:
        for room in segment.get("rooms", []):
            all_room_ids.add(room["id"])
    
    room_ids = list(all_room_ids)
    room_numbers = []
    room_categories = []
    
    # Validate that all rooms exist
    room_number_by_id = {}
    for rid in room_ids:
        room = await db.rooms.find_one({"id": rid}, {"_id": 0})
        if not room:
            raise HTTPException(status_code=404, detail=f"Room {rid} not found")
        if room["status"] == RoomStatus.MAINTENANCE.value:
            raise HTTPException(status_code=400, detail=f"Room {room['room_number']} is under maintenance")
        room_numbers.append(room["room_number"])
        room_categories.append(room["category"])
        room_number_by_id[rid] = room["room_number"]

    # Availability check: a segmented booking spans check_in..check_out, so any
    # existing confirmed/checked-in booking overlapping that window and holding
    # one of these rooms is a conflict. Without this, mix & match bookings had
    # no availability check at all and could double-book an occupied room.
    for rid in room_ids:
        conflicting = await db.bookings.find_one({
            "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
            "$or": [{"room_ids": rid}, {"room_id": rid}],
            "check_in_date": {"$lt": check_out_date},
            "check_out_date": {"$gt": check_in_date},
        })
        if conflicting:
            raise HTTPException(
                status_code=400,
                detail=f"Room {room_number_by_id.get(rid, rid)} is not available for the selected dates"
            )

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
            rate, license_fee = rate_components(settings, is_org, room_category, check_in_date)
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
async def create_booking(booking: BookingCreate, current_user: dict = Depends(require_staff_or_admin_role)):
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

    # Validate dates. Without this a reversed range (checkout before checkin)
    # was accepted, charged one night, and — because its date window is empty —
    # never blocked its room again and never conflicted with anything.
    try:
        _ci = date_type.fromisoformat(booking.check_in_date)
        _co = date_type.fromisoformat(booking.check_out_date)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Dates must be valid YYYY-MM-DD")
    if _co <= _ci:
        raise HTTPException(status_code=400, detail="Check-out date must be after check-in date")

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
        settings = await db.app_settings.find_one({}, {"_id": 0}) or {}

        for rid in booking.room_ids:
            room = await db.rooms.find_one({"id": rid}, {"_id": 0})
            if not room:
                raise HTTPException(status_code=404, detail=f"Room {rid} not found")
            if room["status"] == RoomStatus.MAINTENANCE.value:
                raise HTTPException(status_code=400, detail=f"Room {room['room_number']} is under maintenance")

            # Check for overlapping bookings
            # Use $lt and $gt (not $lte/$gte) to allow same-day bookings
            # If existing checkout = new checkin → NO conflict (guest leaves 08:00, new arrives 13:00)
            overlapping = await db.bookings.find_one({
                "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
                "$or": [
                    {"room_ids": rid},
                    {"room_id": rid}  # backward compat with old records
                ],
                "check_in_date": {"$lt": booking.check_out_date},
                "check_out_date": {"$gt": booking.check_in_date}
            })
            if overlapping:
                raise HTTPException(status_code=400, detail=f"Room {room['room_number']} is already booked for these dates")

            rate, license_fee = rate_components(settings, booking.is_org, room["category"], booking.check_in_date)
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
    booking_number = await generate_booking_number(db)

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
async def check_in(request: CheckInRequest, current_user: dict = Depends(require_staff_or_admin_role)):
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

    # Validate alternate contact mobiles
    if request.alt_contacts:
        for i, contact in enumerate(request.alt_contacts):
            if not contact.get("name", "").strip():
                raise HTTPException(status_code=400, detail=f"Name is required for alternate contact {i + 1}")
            if not contact.get("mobile"):
                raise HTTPException(status_code=400, detail=f"Mobile number is required for alternate contact {i + 1}")
            if not validate_indian_mobile(contact["mobile"]):
                raise HTTPException(status_code=400, detail=f"Invalid mobile number for alternate contact {contact.get('name', i + 1)}")
    
    booking = await db.bookings.find_one({"id": request.booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking["status"] != BookingStatus.CONFIRMED.value:
        raise HTTPException(status_code=400, detail="Booking cannot be checked in")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Get settings for rate calculation
    settings = await db.app_settings.find_one({}, {"_id": 0})
    
    # Recalculate room charges through report_calc.stay_charges() — the same
    # calculation every report uses — so the stored total_amount can never
    # drift from what the reports compute. (History: this first read legacy
    # cat_i_rate fields and double-counted the licence fee; then it carried
    # its own copy of the per-room arithmetic, which billed a mix & match
    # booking for EVERY room it ever uses on EVERY night of the stay instead
    # of the night-by-night plan it was quoted at.)
    room_guest_mapping = [dict(r) for r in (request.room_guest_mapping or [])]
    if not booking.get("is_org", False):
        # A Non-Org booking pays the Non-Org rate for every room. The
        # check-in screen only recalculated a room's charge category once a
        # guest was assigned to it, so a room left unassigned in a multi-room
        # Non-Org booking arrived here still labelled "Cat I"/"Cat II" and
        # was billed at the cheaper Org rate.
        for room in room_guest_mapping:
            room["charge_category"] = "Non-Org"

    all_rooms = await db.rooms.find({}, {"_id": 0}).to_list(500)
    room_maps = build_room_maps(all_rooms)

    # EARLY ARRIVAL (owner ruling: staff may check a guest in before the booked
    # date, no restriction). Check-in moves to today, the room must be free for
    # the extra night(s), and they are billed — the rate stays the one in force
    # on the (new) check-in date, like any booking.
    today = ist_today_str()
    booked_check_in = str(booking["check_in_date"]).split("T")[0]
    early_nights = 0
    moved_booking = booking
    if today < booked_check_in:
        early_nights = (date_type.fromisoformat(booked_check_in) - date_type.fromisoformat(today)).days
        if not request.allow_early_arrival:
            raise HTTPException(
                status_code=409,
                detail=(f"This guest is arriving {early_nights} day(s) before the booked check-in date ({booked_check_in}). "
                        "Confirm the early arrival to move check-in to today and bill the extra night(s).")
            )
        booking_rooms = booking.get("room_ids") or ([booking["room_id"]] if booking.get("room_id") else [])
        for rid in booking_rooms:
            clash = await db.bookings.find_one({
                "id": {"$ne": booking["id"]},
                "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
                "$or": [{"room_ids": rid}, {"room_id": rid}],
                "check_in_date": {"$lt": booked_check_in},
                "check_out_date": {"$gt": today},
            })
            if clash:
                room = next((r for r in all_rooms if r["id"] == rid), {})
                raise HTTPException(
                    status_code=409,
                    detail=(f"Room {room.get('room_number', rid)} is not free for the early nights "
                            f"({today} to {booked_check_in}): it is booked by {clash.get('booking_number')} "
                            f"({clash.get('check_in_date')} to {clash.get('check_out_date')}). "
                            "Change this guest's room first, or check in on the booked date.")
                )
        moved_booking = _booking_with_early_arrival(booking, today)

    priced_booking = {**moved_booking, "room_guest_mapping": room_guest_mapping or booking.get("room_guest_mapping") or []}
    charges = stay_charges(priced_booking, settings or {}, room_maps)
    if not charges["rooms"]:
        # Never silently store a Rs 0 bill (this has happened before).
        raise HTTPException(
            status_code=409,
            detail="Cannot work out this booking's room charges — its rooms could not be found. Re-assign the rooms and try again."
        )
    new_room_rent_total = charges["room_rent"]
    new_license_fee_total = charges["license_fee"]

    # Extra beds are charged at CHECK-OUT, for the beds and days actually
    # used (owner ruling, Nov 2026) — a guest often asks for one only partway
    # through the stay. The number noted here is for information; it adds
    # nothing to the bill or the balance.
    extra_bed_charge = 0.0

    # Recalculate total and balance
    new_total_amount = new_room_rent_total + new_license_fee_total
    new_balance = new_total_amount - booking.get("advance_paid", 0.0)

    # Build update fields — only overwrite non-None values
    update_fields = {
        "status": BookingStatus.CHECKED_IN.value,
        "actual_check_in": now,
        "checked_in_by": request.staff_id,
        "extra_beds": request.extra_beds,
        "extra_bed_charge": extra_bed_charge,
        "room_rent_total": new_room_rent_total,   # rent only (licence tracked separately)
        "license_fee_total": new_license_fee_total,
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
        "planned_early_checkout_date": request.planned_early_checkout_date,  # Track if guest informed about early checkout
    }
    for k, v in optional_fields.items():
        if v is not None:
            update_fields[k] = v
    if request.family_members:
        update_fields["family_members"] = request.family_members
    if request.alt_contacts:
        update_fields["alt_contacts"] = request.alt_contacts
    if early_nights:
        update_fields["check_in_date"] = today
        update_fields["original_check_in_date"] = booked_check_in
        update_fields["early_arrival_nights"] = early_nights
        if moved_booking.get("room_segments"):
            update_fields["room_segments"] = moved_booking["room_segments"]
        update_fields["amendment_log"] = (booking.get("amendment_log") or []) + [{
            "amended_at": now,
            "changes": [f"Check-in: {booked_check_in} → {today} (guest arrived {early_nights} day(s) early)"],
            "reason": "Early arrival", "source": "early_arrival",
        }]
    if room_guest_mapping:
        update_fields["room_guest_mapping"] = room_guest_mapping  # Store the (normalised) mapping
    if request.notes:
        update_fields["notes"] = request.notes

    # Atomically claim the check-in: only flip if still confirmed, so two
    # simultaneous check-in submissions can't both apply side effects.
    claim = await db.bookings.update_one(
        {"id": request.booking_id, "status": BookingStatus.CONFIRMED.value},
        {"$set": update_fields}
    )
    if claim.modified_count == 0:
        raise HTTPException(status_code=409, detail="Booking is already being checked in or has been checked in")

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
async def update_booking_rooms(booking_id: str, request: dict, current_user: dict = Depends(require_staff_or_admin_role)):
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
        if room.get("status") == RoomStatus.MAINTENANCE.value:
            raise HTTPException(status_code=400, detail=f"Room {room['room_number']} is under maintenance")
        new_rooms.append(room)

    # The new rooms must actually be free for this booking's dates — this
    # endpoint previously swapped rooms with only an existence check, so a
    # pre-check-in swap could land on a room already booked for those nights.
    for room_id in new_room_ids:
        conflicting = await db.bookings.find_one({
            "id": {"$ne": booking_id},
            "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
            "$or": [{"room_ids": room_id}, {"room_id": room_id}],
            "check_in_date": {"$lt": booking["check_out_date"]},
            "check_out_date": {"$gt": booking["check_in_date"]},
        })
        if conflicting:
            room = next((r for r in new_rooms if r["id"] == room_id), None)
            raise HTTPException(
                status_code=400,
                detail=f"Room {room['room_number'] if room else room_id} is not available for this booking's dates"
            )
    
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

async def _checkout_bill(booking: dict, request_date: Optional[str], extra_beds: int, extra_bed_days: int) -> dict:
    """What a guest owes at check-out — the ONE calculation behind both the
    check-out screen's quote and the bill check_out() stores, so the amount
    staff collect, the stored total and every report can't differ.

    Owner rulings (Nov 2026):
      * Nights are billed for the nights actually stayed. A late check-out
        (actual date after the booked one) is billed to the actual date.
      * An early check-out is billed for the actual nights only if the guest
        said so at check-in; otherwise for the full booked term (accountant
        ruling, Sep 2026) — the room still shows vacant from the real
        departure.
      * Extra beds are charged here, at check-out, for the beds and the exact
        number of days actually used — never at check-in.
    """
    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}
    room_maps = build_room_maps(await db.rooms.find({}, {"_id": 0}).to_list(500))

    check_in_dt = date_type.fromisoformat(str(booking["check_in_date"]).split("T")[0])
    booked_out_dt = date_type.fromisoformat(str(booking["check_out_date"]).split("T")[0])
    actual_checkout_date = request_date or ist_today_str()
    try:
        actual_dt = date_type.fromisoformat(actual_checkout_date)
    except (ValueError, TypeError):
        # Was an unhandled 500 ("Check-out failed") with no usable message.
        raise HTTPException(status_code=400, detail="Checkout date must be a valid YYYY-MM-DD date")

    priced = booking
    if actual_dt < booked_out_dt:
        if booking.get("planned_early_checkout_date"):
            charged_nights, charge_reason = (actual_dt - check_in_dt).days, "early_checkout_informed"
        else:
            charged_nights, charge_reason = (booked_out_dt - check_in_dt).days, "early_checkout_not_informed"
    elif actual_dt > booked_out_dt:
        charged_nights, charge_reason = (actual_dt - check_in_dt).days, "late_checkout"
        # Price the extra nights in the rooms the guest was in on the last
        # booked night (for a mix & match stay this also adds the nights to
        # its night plan, which is what the reports read).
        priced = _booking_with_extension(booking, actual_checkout_date, room_maps)
    else:
        charged_nights, charge_reason = (booked_out_dt - check_in_dt).days, "normal"
    charged_nights = max(0, charged_nights)

    charges = stay_charges(priced, settings, room_maps, charged_nights)
    if charges["rooms"] or charged_nights == 0:
        room_rent_only, license_fee_only = charges["room_rent"], charges["license_fee"]
    else:
        # Rooms can't be resolved at all (e.g. deleted since): fall back to
        # what check-in stored rather than bill Rs 0.
        original_nights = (booked_out_dt - check_in_dt).days
        factor = (charged_nights / original_nights) if original_nights > 0 else 1
        room_rent_only = (booking.get("room_rent_total", 0) or 0) * factor
        license_fee_only = (booking.get("license_fee_total", 0) or 0) * factor

    extra_bed_charge = max(0, extra_beds or 0) * max(0, extra_bed_days or 0) * EXTRA_BED_RATE
    room_total = room_rent_only + license_fee_only
    total_due = room_total + extra_bed_charge
    advance_paid = booking.get("advance_paid", 0) or 0
    return {
        "actual_checkout_date": actual_checkout_date,
        "charged_nights": charged_nights,
        "charge_reason": charge_reason,
        "room_rent": room_rent_only,
        "license_fee": license_fee_only,
        "room_total": round(room_total, 2),
        "extra_bed_charge": round(extra_bed_charge, 2),
        "total_due": round(total_due, 2),
        "advance_paid": advance_paid,
        "amount_due_now": round(total_due - advance_paid, 2),  # negative = guest overpaid
        "priced_booking": priced,
    }


@api_router.get("/bookings/{booking_id}/checkout-quote")
async def checkout_quote(
    booking_id: str,
    actual_checkout_date: Optional[str] = None,
    extra_beds: int = 0,
    extra_bed_days: int = 0,
    current_user: dict = Depends(require_staff_or_admin_role),
):
    """The bill check-out would produce for these inputs, without changing
    anything. The check-out screen shows this number so it can never differ
    from what is stored."""
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["status"] != BookingStatus.CHECKED_IN.value:
        raise HTTPException(status_code=400, detail="Booking is not checked in")
    bill = await _checkout_bill(booking, actual_checkout_date, extra_beds, extra_bed_days)
    bill.pop("priced_booking")
    return bill


@api_router.post("/bookings/check-out")
async def check_out(request: CheckOutRequest, current_user: dict = Depends(require_staff_or_admin_role)):
    booking = await db.bookings.find_one({"id": request.booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking["status"] != BookingStatus.CHECKED_IN.value:
        raise HTTPException(status_code=400, detail="Booking is not checked in")
    
    now = datetime.now(timezone.utc).isoformat()

    bill = await _checkout_bill(booking, request.actual_checkout_date, request.extra_beds_checkout, request.extra_bed_days)
    actual_checkout_date = bill["actual_checkout_date"]
    charged_nights = bill["charged_nights"]
    charge_reason = bill["charge_reason"]
    room_rent_only = bill["room_rent"]
    license_fee_only = bill["license_fee"]
    extra_bed_charge_checkout = bill["extra_bed_charge"]
    total_amount_due = bill["total_due"]
    advance_paid = bill["advance_paid"]
    final_balance = total_amount_due - advance_paid
    
    # Build update fields
    update_fields = {
        "status": BookingStatus.CHECKED_OUT.value,
        "actual_check_out": now,
        "checked_out_by": request.staff_id,
        "actual_checkout_date": actual_checkout_date,
        "charged_nights": charged_nights,
        "charge_reason": charge_reason,
        "room_rent_total": room_rent_only,       # rent only, as at check-in
        "license_fee_total": license_fee_only,
        "extra_beds_checkout": request.extra_beds_checkout,
        "extra_bed_days": request.extra_bed_days,
        "extra_bed_charge_checkout": extra_bed_charge_checkout,
        "total_amount": total_amount_due,
        "balance_amount": final_balance - request.final_payment,
        "final_payment": request.final_payment,
        "updated_at": now
    }
    
    if charge_reason == "late_checkout" and bill["priced_booking"].get("room_segments"):
        update_fields["room_segments"] = bill["priced_booking"]["room_segments"]

    # Optional fields
    optional_fields = {
        "payment_mode": request.payment_mode,
        "payment_id": request.payment_id,
        "notes": request.notes,
        "org_color": request.org_color,
        "card_last4": request.card_last4,
        "card_type": request.card_type,
        "upi_id": request.upi_id,
        "upi_phone": request.upi_phone,
        "bank_name": request.bank_name,
        "bank_ifsc": request.bank_ifsc,
        "bank_account": request.bank_account
    }
    for k, v in optional_fields.items():
        if v is not None:
            update_fields[k] = v
    
    # Atomically claim the checkout: only flip if still checked_in. Two
    # simultaneous checkout submissions (double-click, retry) both passed the
    # find_one guard above; without this, both would insert a "final" payment
    # and double-count the collection. Only the update that actually changes the
    # status proceeds to touch rooms and record payment.
    claim = await db.bookings.update_one(
        {"id": request.booking_id, "status": BookingStatus.CHECKED_IN.value},
        {"$set": update_fields}
    )
    if claim.modified_count == 0:
        raise HTTPException(status_code=409, detail="Booking is already being checked out or has been checked out")

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
async def calculate_refund(booking_id: str, current_user: dict = Depends(get_current_user_with_db)):
    """Calculate refund amount based on cancellation policy
    
    Policy (flexible - supports both hours_before and days_before):
    - >96 hours (4 days) before check-in: 0% charge (100% refund)
    - 48-96 hours (2-4 days) before check-in: 50% charge (50% refund)
    - <48 hours (2 days) before check-in: 100% charge (0% refund)
    """
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}

    # Hours until check-in (13:00 IST on the check-in date)
    hours_until_checkin = (checkin_moment(booking["check_in_date"]) - datetime.now(IST)).total_seconds() / 3600

    advance_paid = booking.get("advance_paid", 0) or 0
    refund = cancellation_refund(advance_paid, hours_until_checkin, settings.get("cancellation_policy"))
    charge_percent = refund["charge_percent"]
    cancellation_charge = refund["cancellation_charge"]
    refund_amount = refund["refund_amount"]

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
async def cancel_booking(request: CancelBookingRequest, current_user: dict = Depends(require_staff_or_admin_role)):
    booking = await db.bookings.find_one({"id": request.booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking["status"] == BookingStatus.CHECKED_IN.value:
        # Cancelling removes a booking's nights from every report. A guest who
        # has checked in has stayed: close the stay with Check Out. A check-in
        # made by mistake is undone by an administrator deleting the booking.
        raise HTTPException(
            status_code=400,
            detail="A guest who has checked in cannot be cancelled — use Check Out. To undo a booking made by mistake, ask an administrator to delete it."
        )
    if booking["status"] != BookingStatus.CONFIRMED.value:
        raise HTTPException(status_code=400, detail="Booking cannot be cancelled")
    
    now = datetime.now(timezone.utc).isoformat()

    # Atomically claim the cancellation: only flip if the booking is still in
    # the status we just read. Two simultaneous submissions (double-click,
    # retry on a slow connection) both passed the check above and BOTH went
    # on to queue a refund for the same advance.
    claim = await db.bookings.update_one(
        {"id": request.booking_id, "status": booking["status"]},
        {"$set": {
            "status": BookingStatus.CANCELLED.value,
            "notes": f"{booking.get('notes', '') or ''} | Cancelled: {request.reason or 'No reason provided'}",
            "updated_at": now
        }}
    )
    if claim.modified_count == 0:
        raise HTTPException(status_code=409, detail="Booking is already being cancelled or has changed; refresh and try again")

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
    
    # Create refund record if advance was paid. Cap at what the guest actually
    # paid in advance — the client sends refund_amount and nothing else stops a
    # typo (or a forged request) from queueing a ₹99,999 refund on a ₹400 advance.
    advance_paid = booking.get("advance_paid", 0) or 0
    if request.refund_amount is None:
        # No amount supplied: apply the cancellation policy here, with the
        # same function the refund preview uses.
        settings = await db.app_settings.find_one({}, {"_id": 0}) or {}
        hours_until_checkin = (checkin_moment(booking["check_in_date"]) - datetime.now(IST)).total_seconds() / 3600
        requested_refund = cancellation_refund(
            advance_paid, hours_until_checkin, settings.get("cancellation_policy")
        )["refund_amount"]
    else:
        requested_refund = request.refund_amount
    refund_amount = min(max(requested_refund, 0), advance_paid)
    if refund_amount > 0:
        refund = Refund(
            booking_id=booking["id"],
            booking_number=booking["booking_number"],
            guest_name=booking["guest_name"],
            amount=refund_amount,
            bank_details=booking.get("bank_details"),
            upi_number=booking.get("upi_number"),
            bank_name=booking.get("bank_name"),
            bank_ifsc=booking.get("bank_ifsc"),
            bank_account=booking.get("bank_account"),
            upi_id=booking.get("upi_id"),
            upi_phone=booking.get("upi_phone"),
        )
        await db.refunds.insert_one(serialize_doc(refund.model_dump()))
    
    return {"message": "Booking cancelled successfully", "booking_id": request.booking_id, "refund_amount": refund_amount}

@api_router.post("/bookings/{booking_id}/close-stale")
async def close_stale_booking(
    booking_id: str, request: CloseStaleBookingRequest,
    current_user: dict = Depends(require_staff_or_admin_role)
):
    """Close out a stale confirmed booking (see list_stale_confirmed_bookings)
    as an actual, completed stay — for when the guest really did come and go,
    just never got clicked through Check In / Check Out at the time.

    Deliberately does NOT recompute total_amount/room_rent_total/
    license_fee_total/balance_amount: every report derives its own money from
    booking_financials() using status + actual_checkout_date (never from
    these stored totals), so fixing those two fields alone already corrects
    every report. The stored amount stays exactly what was originally quoted
    for this booking, since this action carries no new payment information —
    a real billing correction belongs in Amend, not here.
    """
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    today = ist_today_str()
    if (booking.get("status") != BookingStatus.CONFIRMED.value
            or booking.get("actual_check_in") is not None
            or booking.get("check_out_date", "9999-99-99") >= today):
        raise HTTPException(status_code=400, detail="This booking is not a stale confirmed booking")

    actual_checkout_date = request.actual_checkout_date or booking["check_out_date"]
    try:
        checkout_dt = date_type.fromisoformat(actual_checkout_date)
        checkin_dt = date_type.fromisoformat(booking["check_in_date"])
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")
    if checkout_dt <= checkin_dt:
        raise HTTPException(status_code=400, detail="Departure date must be after the check-in date")

    now = datetime.now(timezone.utc).isoformat()
    closing_note = f"Closed out as a stale confirmed booking on {today} by {request.staff_id} (never processed through check-in/checkout)."
    notes = f"{booking.get('notes', '') or ''} | {closing_note}".strip(" |")

    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {
            "status": BookingStatus.CHECKED_OUT.value,
            "actual_check_in": checkin_moment(booking["check_in_date"]).astimezone(timezone.utc).isoformat(),
            "actual_check_out": now,
            "actual_checkout_date": actual_checkout_date,
            "checked_in_by": request.staff_id,
            "checked_out_by": request.staff_id,
            "notes": notes,
            "updated_at": now,
        }}
    )

    updated_booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    return {"message": "Booking closed out", "booking": updated_booking}

@api_router.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: str, current_user: dict = Depends(require_admin_role)):
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
    
    # Free up rooms if booking is confirmed or checked_in — but only rooms no
    # other active booking still holds, so deleting one booking can't flip a
    # room that a different checked-in guest occupies to "available".
    if booking["status"] in [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]:
        room_ids = booking.get("room_ids", [])
        if not room_ids and booking.get("room_id"):
            room_ids = [booking["room_id"]]

        for rid in room_ids:
            other = await db.bookings.find_one({
                "id": {"$ne": booking_id},
                "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
                "$or": [{"room_ids": rid}, {"room_id": rid}],
            })
            if not other:
                await db.rooms.update_one(
                    {"id": rid},
                    {"$set": {"status": RoomStatus.AVAILABLE.value}}
                )

    # Delete the booking
    result = await db.bookings.delete_one({"id": booking_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found or already deleted")

    # Remove any still-pending refund for this booking — a permanently deleted
    # "wrong entry" must not leave a payable refund sitting in the queue.
    # Completed refunds/payments are left untouched (they record money that
    # actually moved and belong to the accounting history).
    await db.refunds.delete_many({
        "booking_id": booking_id,
        "status": {"$ne": RefundStatus.COMPLETED.value},
    })

    return {
        "message": "Booking permanently deleted",
        "booking_id": booking_id,
        "booking_number": booking.get("booking_number"),
        "guest_name": booking.get("guest_name")
    }

@api_router.post("/bookings/amend")
async def amend_booking(request: AmendBookingRequest, current_user: dict = Depends(require_staff_or_admin_role)):
    """
    Amend a confirmed booking
    
    Allows changes to: dates, rooms, party composition
    Restrictions: Only CONFIRMED bookings can be amended
    Payment: Collects additional advance if cost increases
    
    Amendment Policy:
    - Amendments made >24 hours before check-in: No cancellation charges
    - Amendments made <24 hours before check-in: Subject to cancellation policy if dates moved forward
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
    
    # Check amendment timing (for informational purposes)
    original_check_in = datetime.fromisoformat(booking["check_in_date"].replace('Z', '+00:00'))
    if isinstance(original_check_in, datetime) and original_check_in.tzinfo is None:
        original_check_in = original_check_in.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    hours_until_checkin = (original_check_in - now).total_seconds() / 3600
    
    # Prepare amendment data
    amendment_data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "amendment_hours_before_checkin": round(hours_until_checkin, 1)
    }
    
    # Track changes for amendment log
    changes = []
    
    # Amend dates
    dates_changed = False
    if request.check_in_date and request.check_in_date != booking["check_in_date"]:
        changes.append(f"Check-in: {booking['check_in_date']} → {request.check_in_date}")
        amendment_data["check_in_date"] = request.check_in_date
        dates_changed = True

    if request.check_out_date and request.check_out_date != booking["check_out_date"]:
        changes.append(f"Check-out: {booking['check_out_date']} → {request.check_out_date}")
        amendment_data["check_out_date"] = request.check_out_date
        dates_changed = True

    rooms_changed = bool(request.room_ids and request.room_ids != booking.get("room_ids", []))

    # Validate the amended stay window and re-check availability whenever dates
    # OR rooms change. Date-only amendments previously skipped this entirely, so
    # extending a stay could silently overlap another booking on the same room.
    final_check_in = request.check_in_date or booking["check_in_date"]
    final_check_out = request.check_out_date or booking["check_out_date"]
    try:
        if date_type.fromisoformat(final_check_out) <= date_type.fromisoformat(final_check_in):
            raise HTTPException(status_code=400, detail="Check-out date must be after check-in date")
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be valid YYYY-MM-DD")

    if dates_changed or rooms_changed:
        if rooms_changed:
            rooms_to_check = request.room_ids
        else:
            rooms_to_check = booking.get("room_ids") or ([booking["room_id"]] if booking.get("room_id") else [])
        for new_room_id in rooms_to_check:
            conflicting = await db.bookings.find_one({
                "id": {"$ne": request.booking_id},
                "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
                # Legacy bookings stored a single room_id, not room_ids — check both
                "$or": [{"room_ids": new_room_id}, {"room_id": new_room_id}],
                "check_in_date": {"$lt": final_check_out},
                "check_out_date": {"$gt": final_check_in},
            })
            if conflicting:
                room = await db.rooms.find_one({"id": new_room_id}, {"_id": 0})
                raise HTTPException(
                    status_code=400,
                    detail=f"Room {room.get('room_number') if room else new_room_id} not available for selected dates"
                )

    # Amend rooms
    if rooms_changed:
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

        # A mix & match booking's nightly room plan (room_segments) is tied
        # to its original dates and rooms. Amend has no way to re-plan it, so
        # once dates or rooms change the booking becomes a plain one: its
        # rooms for the whole amended stay — which is exactly what the
        # availability check above reserved and what is priced below. Left
        # in place, the stale plan kept driving every report with the OLD
        # nights while the guest was billed for the new ones.
        if booking.get("room_segments"):
            amendment_data["room_segments"] = None
            amendment_data["has_room_changes"] = False
            changes.append("Mix & match room plan replaced by the same rooms for the whole stay")

        # Price the amended booking with report_calc.stay_charges() — the
        # same calculation check-in, check-out and every report use. Rate is
        # resolved by the (possibly amended) check-in date, so moving a
        # booking's check-in across a rate change correctly re-prices it.
        all_rooms = await db.rooms.find({}, {"_id": 0}).to_list(500)
        new_total = stay_charges({**booking, **amendment_data}, settings, build_room_maps(all_rooms))["total"]
        old_total = booking.get("total_amount", 0)

        amendment_data["total_amount"] = new_total
        
        # Calculate payment difference and update advance_paid accordingly
        old_advance = booking.get("advance_paid", 0)
        
        if new_total > old_total:
            # Increased cost - additional payment OPTIONAL (can collect later at checkout)
            additional_required = new_total - old_total
            
            # If payment provided, validate and record it
            if request.additional_advance > 0:
                if request.additional_advance < additional_required:
                    # Partial payment allowed
                    pass
                
                # Update advance paid (add the additional amount collected)
                amendment_data["advance_paid"] = old_advance + request.additional_advance
                
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
                
                changes.append(f"Amount: ₹{old_total} → ₹{new_total} (Additional ₹{request.additional_advance} collected, ₹{additional_required - request.additional_advance} due at checkout)")
            else:
                # No payment collected now - will be collected at checkout
                changes.append(f"Amount: ₹{old_total} → ₹{new_total} (Additional ₹{additional_required} will be collected at checkout)")
        
        elif new_total < old_total:
            changes.append(f"Amount: ₹{old_total} → ₹{new_total} (reduced by ₹{old_total - new_total})")

        else:
            # No cost change
            changes.append(f"Booking details updated (Amount unchanged: ₹{new_total})")

        # A refund is owed only for money the guest has actually PAID beyond
        # the new total — i.e. advance minus new total, when that is
        # positive. This used to be set to (old total - new total) whenever
        # the price dropped, regardless of how much had been paid: shortening
        # a Rs 1,500 booking with a Rs 400 advance to Rs 1,000 recorded a
        # Rs 500 "refund due", which the check-out screen then deducted from
        # the bill — the guest was asked for Rs 100 instead of Rs 600.
        current_advance = amendment_data.get("advance_paid", old_advance)
        refund_due = round(max(0.0, current_advance - new_total), 2)
        amendment_data["refund_due"] = refund_due
        amendment_data["refund_reason"] = "Booking amended - advance exceeds new total" if refund_due > 0 else None
        if refund_due > 0:
            changes.append(f"Refund due to guest: ₹{refund_due} (advance paid exceeds the new total)")

        # Balance still to collect (never negative — an overpayment is the
        # refund_due above, not a negative balance).
        amendment_data["balance_amount"] = round(max(0.0, new_total - current_advance), 2)
    
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
    
    # Update booking — only if it is still CONFIRMED (a check-in or
    # cancellation landing in between must not be overwritten).
    result = await db.bookings.update_one(
        {"id": request.booking_id, "status": BookingStatus.CONFIRMED.value},
        {"$set": amendment_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=409, detail="Booking changed while it was being amended; refresh and try again")

    # Record the additional advance in the payments ledger, like every other
    # payment. It was only ever added to the booking's advance_paid, so the
    # money never appeared in the Dashboard's fund figures.
    if amendment_data.get("advance_paid", 0) > (booking.get("advance_paid", 0) or 0):
        payment = Payment(
            booking_id=booking["id"],
            booking_number=booking["booking_number"],
            amount=round(amendment_data["advance_paid"] - (booking.get("advance_paid", 0) or 0), 2),
            payment_type="advance",
            payment_mode=request.payment_mode
        )
        await db.payments.insert_one(serialize_doc(payment.model_dump()))

    # Fetch updated booking
    updated_booking = await db.bookings.find_one({"id": request.booking_id}, {"_id": 0})
    
    return {
        "message": "Booking amended successfully",
        "booking": updated_booking,
        "changes": changes
    }

# ============= GUEST HISTORY =============

@api_router.get("/guest-history")
async def get_guest_history(
    phone_number: Optional[str] = Query(None, description="Guest phone number"),
    aadhaar_number: Optional[str] = Query(None, description="Guest Aadhaar number"),
    guest_name: Optional[str] = Query(None, description="Guest name (full or partial)"),
    current_user: dict = Depends(get_current_user_with_db)
):
    """
    Get booking history for a guest by phone number, Aadhaar, or name.
    Returns all bookings, statistics, and guest information.
    """
    if not phone_number and not aadhaar_number and not guest_name:
        raise HTTPException(
            status_code=400, 
            detail="Please provide at least one search parameter (phone_number, aadhaar_number, or guest_name)"
        )
    
    # Build query - combine multiple search criteria
    or_conditions = []
    
    # Escape all user input before it becomes a regex — otherwise a value like
    # ".*" matches every guest and a crafted pattern like "(a+)+$" can hang the
    # query (ReDoS). re.escape treats the input as a literal substring.
    if phone_number:
        phone_clean = re.escape(phone_number.replace(" ", "").replace("+91", "").replace("-", ""))
        or_conditions.extend([
            {"guest_contact": {"$regex": phone_clean, "$options": "i"}},
            {"guest_contact": {"$regex": f"\\+91.*{phone_clean}", "$options": "i"}}
        ])

    if aadhaar_number:
        aadhaar_clean = re.escape(aadhaar_number.replace(" ", "").replace("-", ""))
        or_conditions.append({"id_proof_number": {"$regex": aadhaar_clean, "$options": "i"}})

    if guest_name:
        or_conditions.append({"guest_name": {"$regex": re.escape(guest_name), "$options": "i"}})
    
    query = {"$or": or_conditions}
    
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
            except Exception as e:
                # Undercounting a guest's stay history is a data-quality bug,
                # not something to hide — log it so a malformed date on an
                # old booking gets noticed and fixed, instead of silently
                # skewing this guest's "nights stayed" number forever.
                logger.warning(
                    f"guest-history: could not compute nights for booking "
                    f"{booking.get('booking_number', booking.get('id'))}: {e}"
                )
    
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
async def get_staff(staff_type: Optional[StaffType] = None, active_only: bool = True, current_user: dict = Depends(get_current_user_with_db)):
    query = {}
    if staff_type:
        query["staff_type"] = staff_type.value
    if active_only:
        query["is_active"] = True
    
    staff = await db.staff.find(query, {"_id": 0}).to_list(100)
    return staff

@api_router.get("/staff/{staff_id}")
async def get_staff_member(staff_id: str, current_user: dict = Depends(get_current_user_with_db)):
    staff = await db.staff.find_one({"id": staff_id}, {"_id": 0})
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    return staff

@api_router.post("/staff")
async def create_staff(staff: StaffCreate, current_user: dict = Depends(require_admin_role)):
    staff_obj = Staff(**staff.model_dump())
    doc = serialize_doc(staff_obj.model_dump())
    await db.staff.insert_one(doc)
    # Return the created staff by fetching it back without _id
    created_staff = await db.staff.find_one({"id": doc["id"]}, {"_id": 0})
    return created_staff

@api_router.put("/staff/{staff_id}")
async def update_staff(staff_id: str, update: StaffUpdate, current_user: dict = Depends(require_admin_role)):
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    result = await db.staff.update_one({"id": staff_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    return await get_staff_member(staff_id)

@api_router.delete("/staff/{staff_id}")
async def delete_staff(staff_id: str, current_user: dict = Depends(require_admin_role)):
    result = await db.staff.delete_one({"id": staff_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Staff not found")
    return {"message": "Staff deleted successfully"}

# ============= REFUNDS =============

@api_router.get("/refunds", response_model=List[dict])
async def get_refunds(status: Optional[RefundStatus] = None, current_user: dict = Depends(get_current_user_with_db)):
    query = {}
    if status:
        query["status"] = status.value
    
    refunds = await db.refunds.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return refunds

@api_router.put("/refunds/{refund_id}")
async def update_refund(refund_id: str, update: RefundUpdate, current_user: dict = Depends(require_staff_or_admin_role)):
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
        # Atomic transition: only flip to completed if not already completed,
        # so re-submitting (double-click, retry) can't insert a second negative
        # payment and double-count the refund in the funds dashboard.
        result = await db.refunds.update_one(
            {"id": refund_id, "status": {"$ne": RefundStatus.COMPLETED.value}},
            {"$set": update_data},
        )
        refund = await db.refunds.find_one({"id": refund_id}, {"_id": 0})
        if refund is None:
            raise HTTPException(status_code=404, detail="Refund not found")
        if result.modified_count == 0:
            # Already completed earlier — idempotent no-op, no duplicate payment
            return refund
        payment = Payment(
            booking_id=refund["booking_id"],
            booking_number=refund["booking_number"],
            amount=-refund["amount"],  # Negative for refund
            payment_type="refund"
        )
        await db.payments.insert_one(serialize_doc(payment.model_dump()))
        return refund

    result = await db.refunds.update_one({"id": refund_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Refund not found")

    return await db.refunds.find_one({"id": refund_id}, {"_id": 0})

# ============= TOILETRY =============

@api_router.get("/toiletry/items", response_model=List[dict])
async def get_toiletry_items(current_user: dict = Depends(get_current_user_with_db)):
    items = await db.toiletry_inventory.find({}, {"_id": 0}).to_list(100)
    return items

@api_router.post("/toiletry/items")
async def create_toiletry_item(item: ToiletryItemCreate, current_user: dict = Depends(require_staff_or_admin_role)):
    item_obj = ToiletryItem(**item.model_dump())
    doc = serialize_doc(item_obj.model_dump())
    await db.toiletry_inventory.insert_one(doc)
    # Return the created item by fetching it back without _id
    created_item = await db.toiletry_inventory.find_one({"id": doc["id"]}, {"_id": 0})
    return created_item

@api_router.put("/toiletry/items/{item_id}")
async def update_toiletry_item(item_id: str, update: ToiletryItemUpdate, current_user: dict = Depends(require_staff_or_admin_role)):
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.toiletry_inventory.update_one({"id": item_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return await db.toiletry_inventory.find_one({"id": item_id}, {"_id": 0})

@api_router.delete("/toiletry/items/{item_id}")
async def delete_toiletry_item(item_id: str, current_user: dict = Depends(require_admin_role)):
    result = await db.toiletry_inventory.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}

@api_router.post("/toiletry/stock-in")
async def stock_in(request: StockInRequest, current_user: dict = Depends(require_staff_or_admin_role)):
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
async def record_consumption(request: ConsumptionRequest, current_user: dict = Depends(require_staff_or_admin_role)):
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
    to_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user_with_db)
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

@api_router.post("/admin/sync-room-status")
async def sync_room_status(current_user: dict = Depends(require_admin_role)):
    """
    Admin utility: Sync room status based on checked-in bookings
    
    Use this to fix inconsistencies where rooms should be occupied 
    but their status field wasn't updated.
    """
    # Get all checked-in bookings
    checked_in_bookings = await db.bookings.find({
        "status": BookingStatus.CHECKED_IN.value
    }, {"_id": 0}).to_list(1000)
    
    # Collect all occupied room IDs
    occupied_room_ids = set()
    for booking in checked_in_bookings:
        for rid in booking.get("room_ids", []):
            occupied_room_ids.add(rid)
        if booking.get("room_id"):
            occupied_room_ids.add(booking["room_id"])
    
    # Update all rooms with checked-in bookings to occupied
    updated_count = 0
    for rid in occupied_room_ids:
        result = await db.rooms.update_one(
            {"id": rid},
            {"$set": {"status": RoomStatus.OCCUPIED.value}}
        )
        if result.modified_count > 0:
            updated_count += 1
    
    # Also mark all other rooms as available (unless in maintenance)
    all_rooms = await db.rooms.find({}, {"_id": 0}).to_list(100)
    freed_count = 0
    for room in all_rooms:
        if room["id"] not in occupied_room_ids and room["status"] == RoomStatus.OCCUPIED.value:
            await db.rooms.update_one(
                {"id": room["id"]},
                {"$set": {"status": RoomStatus.AVAILABLE.value}}
            )
            freed_count += 1
    
    return {
        "message": "Room status synchronized",
        "occupied_rooms_updated": updated_count,
        "freed_rooms": freed_count,
        "total_checked_in_bookings": len(checked_in_bookings),
        "total_occupied_rooms": len(occupied_room_ids)
    }

# ============= APPROVED DATA CORRECTIONS (admin; see services/corrections_service.py) =============

@api_router.get("/admin/corrections")
async def corrections_preview(current_user: dict = Depends(require_admin_role)):
    """What the approved corrections WOULD change (nothing is changed), plus every batch applied so far."""
    return {"preview": await corrections_service.plan_corrections(db), "batches": await corrections_service.list_batches(db)}


@api_router.post("/admin/corrections/apply")
async def corrections_apply(current_user: dict = Depends(require_admin_role)):
    """Apply the approved corrections: full backup first, originals recorded, guarded per record."""
    return await corrections_service.apply_corrections(db, current_user.get("username") or current_user.get("email") or current_user.get("id"))


@api_router.post("/admin/corrections/undo/{batch_id}")
async def corrections_undo(batch_id: str, current_user: dict = Depends(require_admin_role)):
    """Put back the original values of a batch (a record changed since is skipped, not overwritten)."""
    return await corrections_service.undo_batch(db, batch_id, current_user.get("username") or current_user.get("email") or current_user.get("id"))


@api_router.get("/dashboard/occupancy")
async def get_occupancy(current_user: dict = Depends(get_current_user_with_db)):
    """
    Get real-time occupancy data
    
    Calculates occupancy by checking:
    1. Rooms with status = 'occupied' (fast check)
    2. Bookings with status = 'checked_in' (accurate check)
    
    Uses the union of both to handle edge cases where room status wasn't updated
    """
    rooms = await db.rooms.find({}, {"_id": 0}).to_list(100)
    
    # Get all checked-in bookings
    checked_in_bookings = await db.bookings.find({
        "status": BookingStatus.CHECKED_IN.value
    }, {"_id": 0}).to_list(1000)
    
    # Collect all occupied room IDs and room numbers from checked-in bookings
    occupied_room_ids_from_bookings = set()
    occupied_room_numbers_from_bookings = set()
    
    for booking in checked_in_bookings:
        # Collect room IDs
        for rid in booking.get("room_ids", []):
            occupied_room_ids_from_bookings.add(rid)
        if booking.get("room_id"):
            occupied_room_ids_from_bookings.add(booking["room_id"])
        
        # Also collect room numbers (fallback for data inconsistency)
        for room_num in booking.get("room_numbers", []):
            occupied_room_numbers_from_bookings.add(room_num)
    
    # Mark rooms as occupied if either:
    # 1. Room status is "occupied" OR
    # 2. Room ID is in a checked-in booking OR
    # 3. Room number is in a checked-in booking (fallback for data inconsistency)
    def is_room_occupied(room):
        return (
            room["status"] == RoomStatus.OCCUPIED.value or 
            room["id"] in occupied_room_ids_from_bookings or
            room.get("room_number") in occupied_room_numbers_from_bookings
        )
    
    total_rooms = len(rooms)
    cat_i_rooms = [r for r in rooms if r["category"] == RoomCategory.CAT_I.value]
    cat_ii_rooms = [r for r in rooms if r["category"] == RoomCategory.CAT_II.value]
    
    occupied_rooms = [r for r in rooms if is_room_occupied(r)]
    occupied_cat_i = [r for r in cat_i_rooms if is_room_occupied(r)]
    occupied_cat_ii = [r for r in cat_ii_rooms if is_room_occupied(r)]
    
    return {
        "version": "v2.2_fixed_occupancy",  # Proof new code is running
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
async def get_dashboard_bookings(current_user: dict = Depends(get_current_user_with_db)):
    """Get today's and upcoming bookings"""
    today = ist_today_str()
    
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
    to_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user_with_db)
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
    year: Optional[int] = None,
    current_user: dict = Depends(get_current_user_with_db)
):
    """Cash received in the month, net of refunds (owner ruling, Nov 2026).

    Net revenue = advances received + payments collected at check-out
                  - refunds paid out (cancellation refunds and any money
                  handed back to an overpaid guest at check-out).
    Every payment counts once, in the month it was received. This used to add
    "completed stays" (which already contains each stay's advance) to
    "advances received", so every advance on a stay that finished in the
    month was counted twice.

    The month is the IST calendar month (payment timestamps are stored in UTC).
    """
    today = ist_today_str()
    if not month:
        month = int(today[5:7])
    if not year:
        year = int(today[:4])

    start_ist = datetime(year, month, 1, tzinfo=IST)
    end_ist = datetime(year + 1, 1, 1, tzinfo=IST) if month == 12 else datetime(year, month + 1, 1, tzinfo=IST)
    from_ts = start_ist.astimezone(timezone.utc).isoformat()
    to_ts = end_ist.astimezone(timezone.utc).isoformat()

    payments = await db.payments.find({"created_at": {"$gte": from_ts, "$lt": to_ts}}, {"_id": 0}).to_list(20000)
    advance_amount = sum(p["amount"] for p in payments if p["payment_type"] == "advance")
    checkout_amount = sum(p["amount"] for p in payments if p["payment_type"] == "final")
    refunds_paid = abs(sum(p["amount"] for p in payments if p["payment_type"] == "refund"))

    # Money handed back to a guest who had overpaid, settled on the check-out
    # screen as a negative final payment (no payments-ledger row is written for it).
    handed_back = 0.0
    checked_out = await db.bookings.find(
        {"status": BookingStatus.CHECKED_OUT.value, "actual_check_out": {"$gte": from_ts, "$lt": to_ts}},
        {"_id": 0, "final_payment": 1}
    ).to_list(20000)
    for b in checked_out:
        if (b.get("final_payment") or 0) < 0:
            handed_back += -b["final_payment"]
    refunds_amount = refunds_paid + handed_back

    pending_refunds = await db.refunds.find({
        "status": RefundStatus.PENDING.value, "created_at": {"$gte": from_ts, "$lt": to_ts}
    }, {"_id": 0}).to_list(2000)
    completed_refunds = await db.refunds.find({
        "status": RefundStatus.COMPLETED.value, "created_at": {"$gte": from_ts, "$lt": to_ts}
    }, {"_id": 0}).to_list(2000)

    cash_received = advance_amount + checkout_amount
    return {
        "period": {"month": month, "year": year},
        "completed_stays_amount": checkout_amount,        # paid at check-out (field name kept for the dashboard)
        "advance_booking_amount": advance_amount,
        "cash_received": cash_received,
        "refunds_issued": refunds_amount,
        "net_revenue": cash_received - refunds_amount,
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
    category: Optional[RoomCategory] = None,
    current_user: dict = Depends(get_current_user_with_db)
):
    """
    Check available rooms for given dates
    
    Booking Time Logic:
    - Check-in: 13:00 (1 PM) on check-in date
    - Check-out: 08:00 (8 AM) on check-out date
    - Room becomes available FROM check-out date for new bookings
    
    Example: Room booked Apr 16-17 → Available for new booking from Apr 17
    """
    query = {}
    if category:
        query["category"] = category.value
    
    all_rooms = await db.rooms.find(query, {"_id": 0}).to_list(100)
    
    # Get bookings that overlap with requested dates
    # Use $lt and $gt (not $lte/$gte) to allow same-day bookings
    # If existing checkout = new checkin → NO conflict (guest leaves 08:00, new guest arrives 13:00)
    overlapping_bookings = await db.bookings.find({
        "status": {"$in": [BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]},
        "check_in_date": {"$lt": check_out_date},
        "check_out_date": {"$gt": check_in_date}
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
async def get_calendar_data(month: int, year: int, current_user: dict = Depends(get_current_user_with_db)):
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
async def get_guests(search: Optional[str] = None, current_user: dict = Depends(get_current_user_with_db)):
    query = {}
    if search:
        safe = re.escape(search)  # treat input as a literal, not a regex (ReDoS / match-all)
        query["$or"] = [
            {"name": {"$regex": safe, "$options": "i"}},
            {"contact_number": {"$regex": safe, "$options": "i"}}
        ]

    guests = await db.guests.find(query, {"_id": 0}).to_list(100)
    return guests

@api_router.get("/guests/{guest_id}")
async def get_guest(guest_id: str, current_user: dict = Depends(get_current_user_with_db)):
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
async def create_feedback(fb: FeedbackCreate, current_user: dict = Depends(require_staff_or_admin_role)):
    # Validate ratings
    for field in ["cleanliness", "room_comfort", "basic_amenities", "check_in_procedure",
                  "check_out_procedure", "overall_stay", "staff_behaviour"]:
        val = getattr(fb, field)
        if not (1 <= val <= 5):
            raise HTTPException(status_code=400, detail=f"{field} rating must be between 1 and 5")
    
    booking = await db.bookings.find_one({"id": fb.booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Compute duration. calculate_nights already catches malformed dates
    # internally and returns 1 (never raises), so this no longer wraps it in
    # a redundant try/except that silently turned any failure into 0 nights.
    nights = calculate_nights(booking.get("check_in_date", ""), booking.get("check_out_date", ""))
    
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
async def get_feedbacks(booking_id: Optional[str] = None, current_user: dict = Depends(get_current_user_with_db)):
    query = {}
    if booking_id:
        query["booking_id"] = booking_id
    feedbacks = await db.feedbacks.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return feedbacks

@api_router.get("/feedback/analysis")
async def get_feedback_analysis(current_user: dict = Depends(get_current_user_with_db)):
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
async def get_monthly_report(month: int = Query(..., ge=1, le=12), year: int = Query(..., ge=2000), current_user: dict = Depends(get_current_user_with_db)):
    import calendar as cal_mod
    days_in_month = cal_mod.monthrange(year, month)[1]
    month_start_str = f"{year}-{month:02d}-01"
    month_end_str = f"{year}-{month:02d}-{days_in_month:02d}"
    month_start = date_type(year, month, 1)
    month_end = date_type(year, month, days_in_month)

    # Shared inclusion rule + shared money calculation (see utils/report_calc.py)
    bookings = await db.bookings.find(
        report_booking_query(month_start_str, month_end_str), {"_id": 0}
    ).to_list(2000)

    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}

    all_rooms_list = await db.rooms.find({}, {"_id": 0}).to_list(100)
    room_maps = build_room_maps(all_rooms_list)

    # Color-based grouping for Org guests + Non-Org category
    colors_list = settings.get("colors", COLOR_OPTIONS)
    color_stats = {color: {"guests": 0, "days": 0} for color in colors_list}
    color_stats["Non-Org"] = {"guests": 0, "days": 0}
    color_stats["Unassigned"] = {"guests": 0, "days": 0}

    org_cat_i_days = 0
    org_cat_ii_days = 0
    non_org_days = 0
    extra_beds_total = 0      # bed-nights count, for display only
    extra_bed_money_total = 0.0  # actual money — from fin["extra_bed_charge"], not extra_beds_total x 75

    # Accumulate the ACTUAL resolved money from booking_financials() (rate-
    # history and check-in-date aware) instead of re-deriving it afterward
    # from aggregated nights x a single flat "current settings" rate. The
    # old approach ignored any scheduled rate change entirely — a room's
    # nights this month could have been billed at more than one rate, and
    # multiplying total nights by one flat number can't reproduce that. It
    # also silently disagreed with the Room Occupancy and Guest Details
    # reports, which already summed real per-booking amounts correctly.
    cat_i_room_rent_total = 0.0
    cat_i_license_fee_total = 0.0
    cat_ii_room_rent_total = 0.0
    cat_ii_license_fee_total = 0.0
    non_org_room_rent_total = 0.0
    non_org_license_fee_total = 0.0

    for bk in bookings:
        fin = booking_financials(bk, settings, month_start, month_end, room_maps)
        # Not "nights == 0": an uninformed early checkout can be a real 0-night
        # occupant of this month while still owing penalty (billed_nights)
        # revenue here — fin["rooms"] is empty only when truly neither applies.
        if not fin["rooms"]:
            continue

        is_org = bk.get("is_org", False)
        org_color = bk.get("org_color")

        # Room-days for this booking (nights x rooms; segmented bookings already
        # carry per-room night counts). Both the colour table and the license-fee
        # table count ROOM-days so the two tables always reconcile with each other.
        booking_room_days = sum(r["nights"] for r in fin["rooms"])

        color_key = (org_color if (is_org and org_color and org_color in color_stats)
                     else ("Unassigned" if is_org else "Non-Org"))
        if color_key in color_stats:
            color_stats[color_key]["guests"] += 1
            color_stats[color_key]["days"] += booking_room_days

        for room in fin["rooms"]:
            # A room's OWN resolved org status (honors a per-room Non-Org
            # charge_category override) — not the booking-level is_org above,
            # which is for the guest's colour classification only. Using the
            # booking-level flag here would put a Non-Org-overridden room's
            # now-correct money into the wrong category bucket.
            room_is_org = room.get("is_org", is_org)
            if room_is_org:
                if room["category"] == "Cat I":
                    org_cat_i_days += room["nights"]
                    cat_i_room_rent_total += room["room_rent"]
                    cat_i_license_fee_total += room["license_fee"]
                else:
                    org_cat_ii_days += room["nights"]
                    cat_ii_room_rent_total += room["room_rent"]
                    cat_ii_license_fee_total += room["license_fee"]
            else:
                non_org_days += room["nights"]
                non_org_room_rent_total += room["room_rent"]
                non_org_license_fee_total += room["license_fee"]

        extra_beds_total += round(fin["extra_bed_charge"] / EXTRA_BED_RATE)  # bed-nights actually charged
        # fin["extra_bed_charge"] also carries a bed added at checkout
        # (extra_bed_charge_checkout), which extra_beds_total above can't
        # represent as a night count — money must come from here, not from
        # extra_beds_total x 75, or a checkout-added bed would agree with the
        # other three reports' totals but silently disagree with this one.
        extra_bed_money_total += fin["extra_bed_charge"]

    s = settings
    # Display-only reference rates (shown alongside the license-fee table) —
    # today's base setting, not necessarily what every night this month was
    # actually billed at if a rate change happened mid-month. The totals
    # below never use these; they're always the true summed amounts from
    # booking_financials() above.
    cat_i_lf = s.get("cat_i_license_fee", 30)
    cat_ii_lf = s.get("cat_ii_license_fee", 15)
    non_org_lf = s.get("non_org_license_fee", 30)
    cat_i_rr = s.get("cat_i_room_rent", 470)
    cat_ii_rr = s.get("cat_ii_room_rent", 385)
    non_org_rr = s.get("non_org_room_rent", 570)

    room_rent_total = round(cat_i_room_rent_total + cat_ii_room_rent_total + non_org_room_rent_total, 2)
    lf_org_cat_i = round(cat_i_license_fee_total, 2)
    lf_org_cat_ii = round(cat_ii_license_fee_total, 2)
    lf_non_org = round(non_org_license_fee_total, 2)
    total_license_fee = round(lf_org_cat_i + lf_org_cat_ii + lf_non_org, 2)
    extra_bed_amount = round(extra_bed_money_total, 2)
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
    
    # The rooms that actually exist (Room Occupancy counts these too), not a
    # count typed into Settings that can drift from them.
    total_rooms = len(all_rooms_list) or (s.get("cat_i_rooms_count", 6) + s.get("cat_ii_rooms_count", 9))
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
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user_with_db)
):
    """Get room occupancy report with flexible date filters"""
    import calendar as cal_mod
    
    # Initialize period_label to avoid undefined variable warning
    period_label = None
    
    # Determine date range based on filter type
    if filter_type == "daily":
        if not start_date:
            start_date = ist_today_str()
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
    
    # Get all rooms (to include 0-occupancy rooms in output)
    all_rooms = await db.rooms.find({}, {"_id": 0}).sort("room_number", 1).to_list(100)
    room_maps = build_room_maps(all_rooms)

    # Shared inclusion rule: any booking with >= 1 night overlapping the period,
    # same statuses as the allotment/guest-details/monthly reports.
    bookings = await db.bookings.find(
        report_booking_query(start_date, end_date), {"_id": 0}
    ).to_list(5000)

    # Calculate total days in period
    start_dt = date_type.fromisoformat(start_date)
    end_dt = date_type.fromisoformat(end_date)
    total_days = (end_dt - start_dt).days + 1

    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}

    # Accumulate per-room occupancy by iterating bookings
    room_acc = {}  # room_number -> {"occupied_days": int, "revenue": float, "bookings_detail": list}

    def ensure_room(rn: str):
        if rn not in room_acc:
            room_acc[rn] = {"occupied_days": 0, "revenue": 0.0, "bookings_detail": []}

    included_bookings = 0
    for bk in bookings:
        fin = booking_financials(bk, settings, start_dt, end_dt, room_maps)
        # Not "nights == 0": an uninformed early checkout can be a real 0-night
        # occupant of this period while still owing penalty (billed_nights)
        # revenue here — fin["rooms"] is empty only when truly neither applies.
        if not fin["rooms"]:
            continue
        included_bookings += 1

        bk_number = bk.get("booking_number", "N/A")
        bk_name   = bk.get("guest_name", "N/A")
        stay_in, stay_out = effective_stay(bk)
        bk_from = stay_in.isoformat() if stay_in else "N/A"
        bk_to   = stay_out.isoformat() if stay_out else "N/A"
        total_members = 1 + len(bk.get("family_members", []))

        final_paid = 0.0
        if bk.get("status") == "checked_out":
            total_amt = bk.get("total_amount", 0) or 0
            advance   = bk.get("advance_paid", 0) or 0
            final_paid = max(0.0, round(total_amt - advance, 2))

        # Credit every room in the booking; room["revenue"] already carries the
        # extra-bed charge on the first room so per-room revenues sum to the
        # booking total used by the allotment / guest-details reports.
        for room in fin["rooms"]:
            rn = room["room_number"]
            ensure_room(rn)
            room_acc[rn]["occupied_days"] += room["nights"]
            room_acc[rn]["revenue"]       += room["revenue"]
            room_acc[rn]["bookings_detail"].append({
                "booking_number":    bk_number,
                "is_org":            bk.get("is_org", False),
                "org_color":         bk.get("org_color", "N/A"),
                "name":              bk_name,
                "from_date":         bk_from,
                "to_date":           bk_to,
                "days":              room["nights"],
                "total_members":     total_members,
                "rate_per_day":      room["rate_per_night"],
                "total_revenue_due": room["revenue"],
                "bill_no":           bk_number,
                "advance_paid":      bk.get("advance_paid", 0) or 0,
                "final_amount_paid": final_paid,
            })

    # Build room_details list from rooms collection (guarantees all rooms appear, even empty ones)
    room_details = []
    total_occupied = 0
    total_revenue  = 0.0

    for room in all_rooms:
        rn       = room["room_number"]
        category = room["category"]
        acc      = room_acc.get(rn, {"occupied_days": 0, "revenue": 0.0, "bookings_detail": []})

        # Not capped at period length: overlapping bookings for the same room are
        # a data problem the reconcile check should expose, not silently hide.
        occupied_days    = acc["occupied_days"]
        available_days   = max(0, total_days - occupied_days)
        occupancy_percent= round((occupied_days / total_days) * 100, 2) if total_days > 0 else 0

        room_details.append({
            "room_number":      rn,
            "category":         category,
            "occupied_days":    occupied_days,
            "available_days":   available_days,
            "occupancy_percent":occupancy_percent,
            "revenue":          round(acc["revenue"], 2),
            "bookings_detail":  acc["bookings_detail"],
        })

        total_occupied += acc["occupied_days"]
        total_revenue  += acc["revenue"]

    total_room_days  = total_days * len(all_rooms)
    total_available  = max(0, total_room_days - total_occupied)
    avg_occupancy    = round((total_occupied / total_room_days * 100), 2) if total_room_days > 0 else 0

    return {
        "period_label": period_label,
        "start_date": start_date,
        "end_date": end_date,
        "total_rooms": len(all_rooms),
        "total_days": total_days,
        "total_occupied_days": total_occupied,
        "total_available_days": total_available,
        "avg_occupancy": avg_occupancy,
        "total_bookings": included_bookings,
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
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user_with_db)
):
    """Get room allotment report showing all bookings with room assignments"""
    import calendar as cal_mod
    
    # Initialize period_label to avoid undefined variable warning
    period_label = None
    
    # Determine date range based on filter type (same logic as occupancy)
    if filter_type == "daily":
        if not start_date:
            start_date = ist_today_str()
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
    
    # Shared inclusion rule + shared money calculation (see utils/report_calc.py)
    bookings = await db.bookings.find(
        report_booking_query(start_date, end_date), {"_id": 0}
    ).sort("check_in_date", 1).to_list(5000)

    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}
    all_rooms = await db.rooms.find({}, {"_id": 0}).to_list(100)
    room_maps = build_room_maps(all_rooms)

    period_start = date_type.fromisoformat(start_date)
    period_end = date_type.fromisoformat(end_date)

    allotments = []
    total_revenue = 0.0
    total_nights = 0
    total_room_days = 0
    for bk in bookings:
        fin = booking_financials(bk, settings, period_start, period_end, room_maps)
        nights = fin["nights"]
        # Not "nights == 0": an uninformed early checkout can be a real 0-night
        # occupant of this period while still owing penalty (billed_nights)
        # revenue here — fin["rooms"] is empty only when truly neither applies.
        if not fin["rooms"]:
            continue
        total_amount = fin["total_amount"]
        total_revenue += total_amount
        total_nights += nights
        total_room_days += sum(r["nights"] for r in fin["rooms"])

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
            "is_org": bk.get("is_org", False),
            "org_color": bk.get("org_color", "N/A"),
            "room_numbers": [r["room_number"] for r in fin["rooms"]],
            "room_categories": [r["category"] for r in fin["rooms"]],
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
        "total_nights": total_nights,
        "total_room_days": total_room_days,
        "total_revenue": round(total_revenue, 2),
        "allotments": allotments
    }


@api_router.get("/reports/guest-details")
async def get_guest_details_report(
    filter_type: str = Query(...),
    month: Optional[int] = None,
    year: Optional[int] = None,
    quarter: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user_with_db)
):
    """Get comprehensive guest details report - includes ALL party members"""
    import calendar as cal_mod
    
    # Determine date range based on filter type
    if filter_type == "daily":
        if not start_date:
            start_date = ist_today_str()
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
    
    # Shared inclusion rule + shared money calculation (see utils/report_calc.py)
    bookings = await db.bookings.find(
        report_booking_query(start_date, end_date), {"_id": 0}
    ).sort("check_in_date", 1).to_list(5000)

    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}
    all_rooms = await db.rooms.find({}, {"_id": 0}).to_list(100)
    room_maps = build_room_maps(all_rooms)

    period_start = date_type.fromisoformat(start_date)
    period_end = date_type.fromisoformat(end_date)

    guest_party_members = []
    total_nights = 0
    total_revenue = 0
    total_party_members = 0
    total_bookings = 0

    for bk in bookings:
        fin = booking_financials(bk, settings, period_start, period_end, room_maps)
        nights = fin["nights"]
        # Not "nights == 0": an uninformed early checkout can be a real 0-night
        # occupant of this period while still owing penalty (billed_nights)
        # revenue here — fin["rooms"] is empty only when truly neither applies.
        if not fin["rooms"]:
            continue
        total_bookings += 1
        total_nights += nights
        is_org = bk.get("is_org", False)
        total_amount = fin["total_amount"]
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
        "total_bookings": total_bookings,
        "total_nights": total_nights,
        "total_revenue": round(total_revenue, 2),
        "guest_party_members": guest_party_members
    }

@api_router.get("/reports/reconcile")
async def reconcile_reports(month: int = Query(..., ge=1, le=12), year: int = Query(..., ge=2000), current_user: dict = Depends(get_current_user_with_db)):
    """Cross-check that all four reports agree for a month.

    Re-derives the headline numbers of the Room Allotment, Guest Details,
    Room Occupancy and Monthly reports from the same source data and fails
    loudly (consistent=false + mismatch list) if any pair diverges. Run this
    after month-end closing; if it ever fails, a report code path has drifted
    from utils/report_calc.py.
    """
    allotment = await get_room_allotment_report(filter_type="monthly", month=month, year=year)
    guest_details = await get_guest_details_report(filter_type="monthly", month=month, year=year)
    occupancy = await get_room_occupancy_report(filter_type="monthly", month=month, year=year)
    monthly = await get_monthly_report(month=month, year=year)

    occupancy_revenue = round(sum(r["revenue"] for r in occupancy["room_details"]), 2)
    occupancy_room_days = sum(r["occupied_days"] for r in occupancy["room_details"])
    monthly_room_days = (monthly["org_cat_i_days"] + monthly["org_cat_ii_days"]
                         + monthly["non_org_days"])

    mismatches = []

    def check(label: str, a, b):
        if round(a or 0, 2) != round(b or 0, 2):
            mismatches.append({"check": label, "left": a, "right": b})

    check("revenue: allotment vs guest_details",
          allotment["total_revenue"], guest_details["total_revenue"])
    check("revenue: allotment vs occupancy", allotment["total_revenue"], occupancy_revenue)
    check("revenue: allotment vs monthly grand_total",
          allotment["total_revenue"], monthly["grand_total"])
    check("room_days: allotment vs occupancy",
          allotment["total_room_days"], occupancy_room_days)
    check("room_days: allotment vs monthly license tables",
          allotment["total_room_days"], monthly_room_days)
    check("room_days: monthly command table vs monthly license tables",
          monthly["total_days"], monthly_room_days)
    check("bookings: allotment vs occupancy",
          allotment["total_allotments"], occupancy["total_bookings"])
    check("bookings: allotment vs guest_details",
          allotment["total_allotments"], guest_details["total_bookings"])
    check("nights: allotment vs guest_details",
          allotment["total_nights"], guest_details["total_nights"])

    return {
        "month": month,
        "year": year,
        "consistent": len(mismatches) == 0,
        "mismatches": mismatches,
        "totals": {
            "revenue": {
                "room_allotment": allotment["total_revenue"],
                "guest_details": guest_details["total_revenue"],
                "room_occupancy": occupancy_revenue,
                "monthly_grand_total": monthly["grand_total"],
            },
            "room_days": {
                "room_allotment": allotment["total_room_days"],
                "room_occupancy": occupancy_room_days,
                "monthly_command_table": monthly["total_days"],
                "monthly_license_tables": monthly_room_days,
            },
            "bookings": {
                "room_allotment": allotment["total_allotments"],
                "guest_details": guest_details["total_bookings"],
                "room_occupancy": occupancy["total_bookings"],
            },
        },
    }


# ============= AUDIT CHECK (month-end reconciliation) =============
# Read-only, admin-only. The one place that answers, against the live
# database, the three month-end questions: do the four reports agree with
# each other (every month on record), do they agree with what each guest was
# actually billed, and was what was billed collected. Changes nothing.
# Paired with the "Audit check" button on the Reports page; the month-end
# procedure that reads its output is docs/month-end-reconciliation-agent.md.
# Started life as temporary tooling for the Nov 2026 audit and was kept
# because /reports/reconcile alone only proves the reports agree with EACH
# OTHER, not with the money.
async def _backup_summary() -> dict:
    """Latest successful backup, worked out in Python (see
    backup_service.list_backup_metadata for why Mongo's own sort can't be
    used), plus how many exist and how many were taken in the last 30 days."""
    successful = await backup_service.list_backup_metadata(db, {"status": "SUCCESS"})
    now_utc = datetime.now(timezone.utc)
    stamps = [t for t in (backup_service.parse_backup_timestamp(b.get("timestamp")) for b in successful) if t]
    latest = stamps[0] if stamps else None
    return {
        "latest_success": latest.isoformat() if latest else None,
        "hours_since_latest": round((now_utc - latest).total_seconds() / 3600, 1) if latest else None,
        "successful_total": len(stamps),
        "successful_last_30_days": sum(1 for t in stamps if (now_utc - t).days < 30),
        "stored_as_dates_not_text": sum(1 for b in successful if isinstance(b.get("timestamp"), datetime)),
        "kept_in_database_too": sum(1 for b in successful if b.get("stored_in_database")),
        # Do the backup FILES on the server survive a redeploy? If this is far below
        # successful_total, the server's disk is being wiped and only the copies kept
        # in the database (and files downloaded to a computer) can be trusted.
        "files_still_on_server": sum(1 for b in successful if b.get("file_path") and Path(b["file_path"]).exists()),
        "files_missing_from_server": sum(1 for b in successful if b.get("file_path") and not Path(b["file_path"]).exists()),
        "last_download_to_a_computer": (
            await db.backup_downloads.find_one({}, {"_id": 0, "timestamp": 1, "by": 1}, sort=[("timestamp", -1)])
        ),
    }


def previous_closed_month(today_str: str) -> tuple:
    """(year, month) of the calendar month before the one `today_str` falls in."""
    year, month = int(today_str[:4]), int(today_str[5:7])
    return (year - 1, 12) if month == 1 else (year, month - 1)


@api_router.get("/reports/audit-check")
async def audit_check(current_user: dict = Depends(require_admin_role)):
    """Month-end audit of the PREVIOUS CLOSED MONTH only (owner's rule: run on
    17 Nov and it audits 1-31 Oct; there is deliberately no way to point it at
    another month). Read-only.

    Answers, for that month: do the four reports agree with each other; for
    the bookings that CHECKED OUT in it, do the reports agree with what each
    guest was billed and with what was collected; and a few counts of risky
    situations. A final block reports the current state of things that are
    not about any month (backups, open refund records)."""
    today = ist_today_str()
    year, month = previous_closed_month(today)
    month_key = f"{year}-{month:02d}"
    last_day = calendar.monthrange(year, month)[1]
    period_start, period_end = date_type(year, month, 1), date_type(year, month, last_day)

    settings = await db.app_settings.find_one({}, {"_id": 0}) or {}
    room_maps = build_room_maps(await db.rooms.find({}, {"_id": 0}).to_list(500))
    bookings = await db.bookings.find({}, {"_id": 0}).to_list(20000)
    wide_start, wide_end = date_type(2000, 1, 1), date_type(2100, 1, 1)

    # 1. Do the four reports agree with each other for this month?
    try:
        rec = await reconcile_reports(month=month, year=year)
        reports = {"consistent": rec["consistent"], "mismatches": rec["mismatches"], "totals": rec["totals"]}
    except Exception as e:  # report the failure, don't hide it
        reports = {"consistent": False, "error": str(e)}

    # 2. For bookings that checked out in the month: reported vs billed vs
    # collected. Whole-stay amounts, attributed to the month the stay ended
    # in — a stay crossing a month boundary will not match the monthly
    # report's night-by-night split, which is expected.
    def checkout_month(b):
        return (b.get("actual_checkout_date") or b.get("check_out_date") or "")[:7]

    checked_out = [b for b in bookings if b.get("status") == BookingStatus.CHECKED_OUT.value and checkout_month(b) == month_key]
    summary = {"checked_out": len(checked_out), "reported": 0.0, "billed": 0.0, "collected": 0.0,
               "reported_but_not_collected": 0.0, "collected_beyond_reported": 0.0,
               "differ_from_billed": 0, "reported_minus_billed": 0.0, "by_cause": {}}
    differing, unexplained, under_collected, over_collected = [], [], [], []
    for b in checked_out:
        reported = booking_financials(b, settings, wide_start, wide_end, room_maps)["total_amount"]
        billed = round(b.get("total_amount", 0) or 0, 2)
        collected = round((b.get("advance_paid", 0) or 0) + (b.get("final_payment", 0) or 0), 2)
        summary["reported"] = round(summary["reported"] + reported, 2)
        summary["billed"] = round(summary["billed"] + billed, 2)
        summary["collected"] = round(summary["collected"] + collected, 2)
        pay_row = {"bk": b.get("booking_number"), "out": b.get("actual_checkout_date") or b.get("check_out_date"),
                   "reported": reported, "billed": billed, "collected": collected,
                   "advance": b.get("advance_paid", 0) or 0, "final_payment": b.get("final_payment", 0) or 0,
                   "payment_mode": b.get("payment_mode"), "balance_on_record": b.get("balance_amount")}
        if reported - collected > 0.5:
            summary["reported_but_not_collected"] = round(summary["reported_but_not_collected"] + reported - collected, 2)
            under_collected.append({**pay_row, "short_by": round(reported - collected, 2)})
        elif collected - reported > 0.5:
            summary["collected_beyond_reported"] = round(summary["collected_beyond_reported"] + collected - reported, 2)
            over_collected.append({**pay_row, "extra": round(collected - reported, 2)})
        if abs(reported - billed) <= 0.5:
            continue
        tags = []
        if (b.get("actual_checkout_date") or "") > (b.get("check_out_date") or ""):
            tags.append("late_checkout")
        if (b.get("extra_bed_charge_checkout", 0) or 0) > 0:
            tags.append("checkout_extra_bed")
        if b.get("room_segments"):
            tags.append("mix_match")
        if b.get("is_amended"):
            tags.append("extended")
        if "charged_nights" not in b:
            tags.append("never_checked_out_in_app")
        if b.get("charge_reason") == "early_checkout_not_informed":
            tags.append("penalty")
        tag = "+".join(tags) or "unexplained"
        summary["differ_from_billed"] += 1
        summary["reported_minus_billed"] = round(summary["reported_minus_billed"] + reported - billed, 2)
        cause = summary["by_cause"].setdefault(tag, {"bookings": 0, "reported_minus_billed": 0.0})
        cause["bookings"] += 1
        cause["reported_minus_billed"] = round(cause["reported_minus_billed"] + reported - billed, 2)
        row = {"bk": b.get("booking_number"), "out": b.get("actual_checkout_date") or b.get("check_out_date"),
               "reported": reported, "billed": billed, "collected": collected, "why": tag}
        differing.append(row)
        if tag == "unexplained":
            unexplained.append({
                **row, "in": b.get("check_in_date"), "out_booked": b.get("check_out_date"),
                "out_actual": b.get("actual_checkout_date"), "charge_reason": b.get("charge_reason"),
                "charged_nights": b.get("charged_nights"), "is_org": b.get("is_org"),
                "rooms": b.get("room_numbers"), "categories": b.get("room_categories"),
                "charge_categories": [mp.get("charge_category") for mp in (b.get("room_guest_mapping") or [])],
            })
    differing.sort(key=lambda d: abs(d["reported"] - d["billed"]), reverse=True)

    # 3. Counts for this month's check-outs, and a few for stays that touched it.
    touching = [
        b for b in bookings
        if b.get("status") in ("confirmed", "checked_in", "checked_out")
        and (b.get("check_in_date") or "") <= period_end.isoformat()
        and (b.get("actual_checkout_date") or b.get("check_out_date") or "") >= period_start.isoformat()
    ]
    month_counts = {
        "late_checkouts": sum(1 for b in checked_out if (b.get("actual_checkout_date") or "") > (b.get("check_out_date") or "")),
        "uninformed_early_checkouts": sum(1 for b in checked_out if b.get("charge_reason") == "early_checkout_not_informed"),
        "checked_out_with_extra_bed_charge": sum(1 for b in checked_out if (b.get("extra_bed_charge_checkout", 0) or 0) > 0),
        "closed_outside_the_checkout_screen": [b.get("booking_number") for b in checked_out if "charged_nights" not in b],
        "mix_match_stays": [b.get("booking_number") for b in touching if b.get("room_segments")],
        "non_org_bookings_with_an_org_rate_room": [
            b.get("booking_number") for b in touching if not b.get("is_org")
            and any((m.get("charge_category") or "Non-Org") != "Non-Org" for m in (b.get("room_guest_mapping") or []))],
        "cancelled_after_check_in": [
            b.get("booking_number") for b in bookings if b.get("status") == "cancelled" and b.get("actual_check_in")
            and (b.get("check_in_date") or "")[:7] == month_key],
    }

    # 4. Current state — not about any month.
    active = [b for b in bookings if b.get("status") in ("confirmed", "checked_in")]
    wrong_refund_due = [
        {"bk": b.get("booking_number"), "status": b.get("status"), "stored_refund_due": b.get("refund_due"),
         "correct": round(max(0.0, (b.get("advance_paid", 0) or 0) - (b.get("total_amount", 0) or 0)), 2)}
        for b in active
        if abs((b.get("refund_due") or 0) - max(0.0, (b.get("advance_paid", 0) or 0) - (b.get("total_amount", 0) or 0))) > 0.5
    ]
    return {
        "audited_month": month_key,
        "period": {"from": period_start.isoformat(), "to": period_end.isoformat()},
        "as_of": today,
        "reports": reports,
        "checked_out_in_month": summary,
        "differing_bookings": differing[:100],
        # Bookings whose reported value is not covered by advance + final payment (and the
        # reverse), largest first — the list behind reported_but_not_collected.
        "under_collected": sorted(under_collected, key=lambda r: -r["short_by"])[:80],
        "over_collected": sorted(over_collected, key=lambda r: -r["extra"])[:40],
        "unexplained": unexplained,
        "month_counts": month_counts,
        "current_state": {
            "active_bookings_with_wrong_refund_due": wrong_refund_due,
            "backups": await _backup_summary(),
        },
    }


@api_router.get("/reports/manual-occupancy-excel")
async def download_manual_occupancy_excel(
    month: int = Query(..., ge=1, le=12), year: int = Query(..., ge=2000),
    current_user: dict = Depends(get_current_user_with_db)
):
    """Excel export matching the guesthouse's manual 'Summary of Room Occupancy'
    paper ledger format for the given month (one row per room per booking).

    Army No / Rank / Unit / Bill No are left blank for manual completion —
    the app does not store those fields (removed as confidential, paper-only
    data during sanitization). Aadhaar Number and Org/Non-Org are included
    instead so a row can be matched to a person by name.
    """
    import calendar as cal_mod

    buf = await build_manual_occupancy_workbook(db, month, year)
    filename = f"Room_Occupancy_{cal_mod.month_name[month]}_{year}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
        # Use the backup time the admin last saved (it used to reset to the
        # default on every restart).
        saved = ((await db.app_settings.find_one({}, {"_id": 0, "backup_schedule": 1})) or {}).get("backup_schedule") or {}
        scheduler_service.init_scheduler(
            db,
            hour=saved.get("hour", scheduler_service.DEFAULT_BACKUP_HOUR),
            minute=saved.get("minute", scheduler_service.DEFAULT_BACKUP_MINUTE),
        )
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
async def trigger_full_backup(current_user: dict = Depends(require_staff_or_admin_role)):
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


@api_router.get("/backups/download")
async def download_backup(current_user: dict = Depends(require_admin_role)):
    """A complete backup as a file for the computer that asked for it — the
    copy that does not depend on Render or on the database host. Admin only.

    Login records (and their password hashes) are NOT in it; a plain list of
    who has an account is, so accounts can be re-created by hand after a
    recovery. Nothing is written on the server except a note that a download
    happened, which the month-end audit check reads."""
    data = await backup_service.collect_full_backup_data(db, include_users=False)
    counts = {name: len(docs) for name, docs in data["collections"].items()}
    now_ist = datetime.now(IST)
    await db.backup_downloads.insert_one({
        "id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(),
        "by": current_user.get("username") or current_user.get("email") or current_user.get("id"),
        "record_count": counts,
    })
    body = json.dumps(data, default=backup_service._json_default, separators=(",", ":"))
    filename = f"sarai-backup-{now_ist.strftime('%Y-%m-%d-%H%M')}.json"
    return Response(
        content=body, media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "X-Backup-Records": str(sum(counts.values()))},
    )


@api_router.post("/backups/manual/incremental")
async def trigger_incremental_backup(current_user: dict = Depends(require_staff_or_admin_role)):
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
async def get_backup_status(current_user: dict = Depends(require_staff_or_admin_role)):
    """Get current backup status and statistics"""
    try:
        # Get last backup
        last_backup = await backup_service.get_last_backup_metadata(db)
        
        # Get total backup count
        total_backups = await db.backup_metadata.count_documents({"status": "SUCCESS"})
        
        # Get first backup date
        successful = await backup_service.list_backup_metadata(db, {"status": "SUCCESS"})
        first_backup = successful[-1] if successful else None
        
        # Check for missed backups
        missed_check = await scheduler_service.check_missed_backups(db)
        
        # Get scheduler status
        scheduler_status = scheduler_service.get_scheduler_status()
        
        last_download = await db.backup_downloads.find_one({}, {"_id": 0}, sort=[("timestamp", -1)])
        return {
            "last_backup": last_backup,
            "last_download": last_download,
            "total_backups": total_backups,
            "first_backup_date": first_backup.get("timestamp") if first_backup else None,
            "missed_backup_warning": missed_check,
            "scheduler": scheduler_status
        }
    except Exception as e:
        logger.error(f"Error fetching backup status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/backups/history")
async def get_backup_history(limit: int = Query(50, ge=1, le=100), current_user: dict = Depends(require_staff_or_admin_role)):
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
async def restore_full_backup(backup_id: str, current_user: dict = Depends(require_admin_role)):
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
async def restore_last_backup(current_user: dict = Depends(require_admin_role)):
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
async def restore_date_range(request: DateRangeRestore, current_user: dict = Depends(require_admin_role)):
    """Restore all backups within a date range"""
    try:
        start = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
        # A bare end DATE means "through the end of that day", not its first
        # instant — otherwise backups taken on the end date are left out.
        if len(request.end_date.strip()) <= 10:
            end = end + timedelta(days=1) - timedelta(microseconds=1)
        
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
async def update_backup_schedule(request: ScheduleUpdate, current_user: dict = Depends(require_admin_role)):
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
async def get_restore_history(limit: int = Query(20, ge=1, le=50), current_user: dict = Depends(require_staff_or_admin_role)):
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
async def get_migration_status(current_user: dict = Depends(require_admin_role)):
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
async def download_migration_archive(current_user: dict = Depends(require_admin_role)):
    """Download the defense data archive file (admin only — contains confidential
    service data that policy forbids exposing; must never be world-readable)."""
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
async def delete_migration_archive(current_user: dict = Depends(require_admin_role)):
    """Delete the migration archive file (admin only — after verification)."""
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
