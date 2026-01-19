from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1 import health, jobs
from app.cron.cleanup import add_cleanup_cron

# Create FastAPI app
app = FastAPI(
    title="SAM-2 Image Segmentation API",
    description="RESTful API for automatic image segmentation using Meta's SAM-2 model",
    version="2.0.0",
)

# Mount static files for serving mask images
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Add scheduled cleanup task
add_cleanup_cron(app)

# Include routers
app.include_router(health.router)
app.include_router(jobs.router)
