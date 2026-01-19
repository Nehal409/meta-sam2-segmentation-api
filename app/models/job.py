from enum import Enum as PyEnum
from typing import Any, Dict

from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.sql import func

from app.core.constants import COMPLETED, ERROR, PENDING, PROCESSING
from app.core.database import Base


class JobStatus(PyEnum):
    """Job status enumeration"""

    PENDING = PENDING
    PROCESSING = PROCESSING
    COMPLETED = COMPLETED
    ERROR = ERROR


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, nullable=False)
    image_url = Column(Text, nullable=False)
    status = Column(
        Enum(JobStatus, name="job_status"),
        nullable=False,
        index=True,
        default=JobStatus.PENDING,
    )
    error_message = Column(Text, nullable=True)
    masks = Column(JSON, nullable=True)  # Store segments data as JSON
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "image_url": self.image_url,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "error_message": self.error_message,
            "masks": self.masks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }
