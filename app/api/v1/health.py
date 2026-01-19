from fastapi import APIRouter

from app.core.logger import logger

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """
    Health check endpoint.

    """
    logger.info("Health check called.")
    return {"status": "ok"}
