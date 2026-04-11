from enum import Enum

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

COLOR_OPTIONS = [
    "Red", "Green", "Brown", "Orange", "Yellow", 
    "Violet", "Black", "Blue", "White", "Light Blue"
]
