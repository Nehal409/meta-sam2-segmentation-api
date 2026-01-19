from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1 import health, jobs
from app.core.database import Base, engine
from app.core.logger import logger
from app.cron.cleanup import add_cleanup_cron


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    yield
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="SAM-2 Image Segmentation API",
    description="RESTful API for automatic image segmentation using Meta's SAM-2 model",
    version="2.0.0",
    lifespan=lifespan,
)

# Mount static files for serving mask images
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Add scheduled cleanup task
add_cleanup_cron(app)

# Include routers
app.include_router(health.router)
app.include_router(jobs.router)
