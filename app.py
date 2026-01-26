import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import cities_router, districts_router, items_router, tasks_router
from core.database import init_db

stream_handler = logging.StreamHandler()
file_handler = logging.FileHandler("app.log")

handlers = [stream_handler]

if False:
    handlers.append(file_handler)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=handlers,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting OLX Database API...")
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down OLX Database API...")


app = FastAPI(
    title="OLX Database API",
    description="FastAPI service for managing OLX monitoring tasks and item records",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    summary="API Root",
    description="Returns basic information about the OLX Database API",
    tags=["General"],
)
async def root():
    """Root endpoint providing API information."""
    return {
        "message": "OLX Database API is running",
    }


@app.get(
    "/health",
    summary="Health Check",
    description="Health check endpoint",
    tags=["General"],
)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "olx-database-api"}


# Register routers
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(items_router, prefix="/api/v1")
app.include_router(cities_router, prefix="/api/v1")
app.include_router(districts_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
