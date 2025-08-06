"""
API routers initialization.
"""

from .items import router as items_router
from .tasks import router as tasks_router

__all__ = ["tasks_router", "items_router"]
