from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import false
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logger import logger
from app.core.security import verify_api_key
from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobListResponse, JobResponse
from app.services.job_processor import process_segmentation_job

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=201)
def create_job(
    job_data: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),  # API key required
):
    """
    Create a new segmentation job.

    The job will be processed asynchronously in the background.
    Returns the job details with status 'PENDING'.
    A unique UUID will be automatically generated for the job.
    """
    # Generate unique UUID for the job
    job_uuid = str(uuid4())

    # Create new job
    job = Job(
        uuid=job_uuid,
        image_url=str(job_data.image_url),
        status=JobStatus.PENDING,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    logger.info(f"Created job {job_uuid} for image {job_data.image_url}")

    # Add background task to process the job
    background_tasks.add_task(process_segmentation_job, job_uuid)

    return JobResponse(**job.to_dict())


@router.get("/{job_uuid}", response_model=JobResponse)
def get_job(
    job_uuid: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),  # API key required
):
    """
    Get job status and results by UUID.

    Returns the job details including status and segmentation results (if available).
    """
    job = db.query(Job).filter(Job.uuid == job_uuid).first()

    if not job:
        raise HTTPException(
            status_code=404, detail=f"Job with UUID {job_uuid} not found"
        )

    return JobResponse(**job.to_dict())


@router.get("", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    status: str = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),  # API key required
):
    """
    List all jobs with pagination.

    Optionally filter by status (PENDING, PROCESSING, COMPLETED, ERROR).
    """
    query = db.query(Job)

    # Filter by status if provided
    if status:
        try:
            status_enum = JobStatus[status.upper()]
            query = query.filter(Job.status == status_enum)
        except KeyError:
            # Invalid status value, return empty result
            query = query.filter(false())

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


@router.delete("/{job_uuid}", status_code=204)
def delete_job(
    job_uuid: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),  # API key required
):
    """
    Delete a job by UUID.

    This will remove the job from the database. The associated mask files
    will be cleaned up by the scheduled cleanup task.
    """
    job = db.query(Job).filter(Job.uuid == job_uuid).first()

    if not job:
        raise HTTPException(
            status_code=404, detail=f"Job with UUID {job_uuid} not found"
        )

    db.delete(job)
    db.commit()

    logger.info(f"Deleted job {job_uuid}")

    return JSONResponse(status_code=204, content=None)
