import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import items_router, tasks_router
from core.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
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
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    docs_url="/docs",
    redoc_url="/redoc",
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
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
