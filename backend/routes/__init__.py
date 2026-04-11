from .settings import router as settings_router
from .rooms import router as rooms_router
from .bookings import router as bookings_router
from .staff import router as staff_router
from .refunds import router as refunds_router
from .toiletry import router as toiletry_router
from .dashboard import router as dashboard_router
from .guests import router as guests_router
from .reports import router as reports_router
from .feedback import router as feedback_router
from .backup import router as backup_router

__all__ = [
    "settings_router",
    "rooms_router",
    "bookings_router",
    "staff_router",
    "refunds_router",
    "toiletry_router",
    "dashboard_router",
    "guests_router",
    "reports_router",
    "feedback_router",
    "backup_router"
]
