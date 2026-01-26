"""
API routers initialization.
"""

from .cities import router as cities_router
from .districts import router as districts_router
from .items import router as items_router
from .tasks import router as tasks_router

__all__ = ["tasks_router", "items_router", "cities_router", "districts_router"]
