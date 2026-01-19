from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    """Schema for creating a new job"""

    image_url: str = Field(
        ...,
        description="URL of the image to segment",
        examples=["https://example.com/image.jpg"],
    )


class JobResponse(BaseModel):
    """Schema for job response"""

    id: int
    uuid: str
    image_url: str
    status: str
    error_message: Optional[str] = None
    masks: Optional[List[Dict[str, Any]]] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Schema for listing jobs"""

    jobs: List[JobResponse]
    total: int
    page: int = 1
    page_size: int = 10
