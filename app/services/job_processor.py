"""Background job processor for segmentation tasks"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.constants import COMPLETED, ERROR, PROCESSING
from app.core.database import SessionLocal
from app.core.logger import logger
from app.models.job import Job
from app.services.segmentation import run_segmentation
from app.utils.image_downloader import download_image


def process_segmentation_job(job_uuid: str) -> None:
    """
    Process a segmentation job in the background.
    This function is called as a background task.
    """
    db: Session = SessionLocal()

    try:
        # Get job from database
        job = db.query(Job).filter(Job.uuid == job_uuid).first()

        if not job:
            logger.error(f"Job {job_uuid} not found in database")
            return

        logger.info(f"Processing job {job_uuid} with image {job.image_url}")

        # Update status to PROCESSING
        job.status = PROCESSING
        db.commit()

        try:
            # Download image
            image = download_image(job.image_url)

            # Apply SAM-2 segmentation
            segments_data = run_segmentation(image, job_uuid)

            # Update job with results
            job.status = COMPLETED
            job.masks = segments_data
            job.completed_at = datetime.now(timezone.utc)
            db.commit()

            logger.info(
                f"Job {job_uuid} completed successfully with {len(segments_data)} segments"
            )

        except Exception as e:
            logger.error(f"Failed to process job {job_uuid}: {e}")
            # Update job with error status
            job.status = ERROR
            job.error_message = str(e)
            db.commit()
            raise

    except Exception as e:
        logger.error(f"Error processing job {job_uuid}: {e}")
    finally:
        db.close()
