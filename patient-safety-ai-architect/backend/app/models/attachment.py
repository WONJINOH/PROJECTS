"""
Attachment Model

Files stored locally: uploads/incidents/{incident_id}/
DB stores: file:// style URI
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class Attachment(Base):
    """Incident attachment model."""

    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)

    # File metadata
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes

    # Storage URI (file:// style)
    # Example: file://uploads/incidents/123/document.pdf
    storage_uri = Column(String(500), nullable=False)

    # References
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Metadata
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="attachments")

    def __repr__(self) -> str:
        return f"<Attachment {self.id} ({self.original_filename})>"
