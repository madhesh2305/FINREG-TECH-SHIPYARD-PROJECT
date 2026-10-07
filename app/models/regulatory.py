from datetime import datetime, date, timezone
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base, PK_BIGINT

class RegulatorySource(Base):
    __tablename__ = "regulatory_sources"
    __table_args__ = (
        CheckConstraint("validation_status IN ('PENDING', 'VALIDATED', 'REJECTED')", name="chk_source_validation_status"),
        {"schema": "regulatory"}
    )

    source_id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    source_title = Column(String(250), nullable=False)
    issuing_authority = Column(String(200), nullable=False)
    jurisdiction = Column(String(100), nullable=False)
    source_url = Column(Text, nullable=False)
    version_label = Column(String(50), nullable=False)
    publication_date = Column(Date, nullable=False)
    retrieved_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    validation_status = Column(String(20), default="VALIDATED", nullable=False)
    topic = Column(String(150), nullable=False)
    relevance = Column(Text, nullable=False)
    applicability_rationale = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    requirements = relationship("RegulatoryRequirement", back_populates="source")

class RegulatoryRequirement(Base):
    __tablename__ = "regulatory_requirements"
    __table_args__ = (
        UniqueConstraint("project_id", "requirement_code", name="uq_project_requirement_code"),
        CheckConstraint("applicability_status IN ('APPLICABLE', 'NOT_APPLICABLE', 'UNDER_REVIEW')", name="chk_requirement_applicability"),
        CheckConstraint("requirement_status IN ('OPEN', 'IN_REVIEW', 'COMPLETED', 'BLOCKED')", name="chk_requirement_status"),
        {"schema": "regulatory"}
    )

    requirement_id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("project_management.projects.project_id"), nullable=False, index=True)
    source_id = Column(BigInteger, ForeignKey("regulatory.regulatory_sources.source_id"), nullable=False, index=True)
    requirement_code = Column(String(50), nullable=False)
    requirement_title = Column(String(250), nullable=False)
    requirement_text = Column(Text, nullable=False)
    applicability_status = Column(String(20), default="APPLICABLE", nullable=False)
    requirement_status = Column(String(20), default="OPEN", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="requirements")
    source = relationship("RegulatorySource", back_populates="requirements")
