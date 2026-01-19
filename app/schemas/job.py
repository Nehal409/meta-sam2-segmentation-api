from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


class JobCreate(BaseModel):
    """Schema for creating a new job"""

    image_url: HttpUrl = Field(..., description="URL of the image to segment")
    uuid: Optional[str] = Field(
        default_factory=lambda: str(uuid4()), description="Optional UUID for the job"
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
