from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base, PK_BIGINT

class ProjectAttachment(Base):
    __tablename__ = "project_attachments"
    __table_args__ = {"schema": "project_management"}

    attachment_id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("project_management.projects.project_id"), nullable=False, index=True)
    uploaded_by = Column(BigInteger, ForeignKey("identity.users.user_id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    content_type = Column(String(100), default="application/pdf", nullable=False)
    category = Column(String(50), default="ADVISORY_REFERENCE", nullable=False)
    storage_path = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project")
    uploader = relationship("User")
