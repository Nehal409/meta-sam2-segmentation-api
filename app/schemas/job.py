from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class JobCreate(BaseModel):
    """Schema for creating a new job"""

    image_url: HttpUrl = Field(
        ...,
        description="URL of the image to segment",
        examples=["https://example.com/image.jpg"],
    )

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, v: HttpUrl) -> HttpUrl:
        """Validate image URL format and protocol"""
        url_str = str(v)
        
        # Ensure it's HTTP or HTTPS
        if not url_str.startswith(("http://", "https://")):
            raise ValueError("Image URL must use http:// or https:// protocol")
        
        # Check for common image extensions
        image_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff")
        if not any(url_str.lower().endswith(ext) for ext in image_extensions):
            # Don't fail, just log a warning - some URLs might not have extensions
            pass
        
        return v


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
