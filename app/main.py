from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.core.database import Base, engine, get_db
from app.core.logger import logger
from app.cron.cleanup import add_cleanup_cron
from app.models.job import Job
from app.schemas.job import JobCreate, JobListResponse, JobResponse
from app.services.job_processor import process_segmentation_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="SAM-2 Image Segmentation API",
    description="RESTful API for automatic image segmentation using Meta's SAM-2 model",
    version="2.0.0",
    lifespan=lifespan,
)

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

add_cleanup_cron(app)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    logger.info("Health check called.")
    return {"status": "ok"}


@app.post("/api/v1/jobs", response_model=JobResponse, status_code=201)
def create_job(
    job_data: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a new segmentation job.
    
    The job will be processed asynchronously in the background.
    Returns the job details with status 'PENDING'.
    """
    # Check if UUID already exists
    if job_data.uuid:
        existing_job = db.query(Job).filter(Job.uuid == job_data.uuid).first()
        if existing_job:
            raise HTTPException(
                status_code=409,
                detail=f"Job with UUID {job_data.uuid} already exists",
            )
        job_uuid = job_data.uuid
    else:
        # Generate new UUID if not provided
        from uuid import uuid4
        job_uuid = str(uuid4())
    
    # Create new job
    job = Job(
        uuid=job_uuid,
        image_url=str(job_data.image_url),
        status="PENDING",
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    logger.info(f"Created job {job_uuid} for image {job_data.image_url}")
    
    # Add background task to process the job
    background_tasks.add_task(process_segmentation_job, job_uuid)
    
    return JobResponse(**job.to_dict())


@app.get("/api/v1/jobs/{job_uuid}", response_model=JobResponse)
def get_job(job_uuid: str, db: Session = Depends(get_db)):
    """
    Get job status and results by UUID.
    
    Returns the job details including status and segmentation results (if available).
    """
    job = db.query(Job).filter(Job.uuid == job_uuid).first()
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with UUID {job_uuid} not found")
    
    return JobResponse(**job.to_dict())


@app.get("/api/v1/jobs", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    status: str = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    """
    List all jobs with pagination.
    
    Optionally filter by status (PENDING, PROCESSING, COMPLETED, ERROR).
    """
    query = db.query(Job)
    
    # Filter by status if provided
    if status:
        query = query.filter(Job.status == status.upper())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    jobs = query.order_by(Job.created_at.desc()).offset(offset).limit(page_size).all()
    
    return JobListResponse(
        jobs=[JobResponse(**job.to_dict()) for job in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


@app.delete("/api/v1/jobs/{job_uuid}", status_code=204)
def delete_job(job_uuid: str, db: Session = Depends(get_db)):
    """
    Delete a job by UUID.
    
    This will remove the job from the database. The associated mask files
    will be cleaned up by the scheduled cleanup task.
    """
    job = db.query(Job).filter(Job.uuid == job_uuid).first()
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with UUID {job_uuid} not found")
    
    db.delete(job)
    db.commit()
    
    logger.info(f"Deleted job {job_uuid}")
    
    return JSONResponse(status_code=204, content=None)
