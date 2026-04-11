from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from .base import COLOR_OPTIONS

class CancellationSlab(BaseModel):
    hours_before: int
    charge_percent: float

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
    room_categories: List[dict] = Field(default_factory=lambda: [
        {
            "id": "cat-i",
            "name": "Cat I",
            "rate": 500.0,
            "def_civ_rate": 600.0,
            "room_count": 6,
            "prefix": "C1",
            "capacity": 2
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
