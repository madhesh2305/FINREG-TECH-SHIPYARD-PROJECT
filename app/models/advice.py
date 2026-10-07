from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class Advice(Base):
    __tablename__ = "advice"
    __table_args__ = (
        CheckConstraint("advice_status IN ('DRAFT', 'SUBMITTED', 'REVIEWED', 'ARCHIVED')", name="chk_advice_status"),
        {"schema": "advice"}
    )

    advice_id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("project_management.projects.project_id"), nullable=False, index=True)
    advisor_profile_id = Column(BigInteger, ForeignKey("advisor_management.advisor_profiles.advisor_profile_id"), nullable=False, index=True)
    title = Column(String(250), nullable=False)
    advice_text = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    assumptions = Column(Text, nullable=False)
    advice_status = Column(String(20), default="SUBMITTED", nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    source_links = relationship("AdviceSourceLink", back_populates="advice", cascade="all, delete-orphan")

class AdviceSourceLink(Base):
    __tablename__ = "advice_source_links"
    __table_args__ = (
        UniqueConstraint("advice_id", "source_id", name="uq_advice_source_link"),
        {"schema": "advice"}
    )

    advice_source_link_id = Column(BigInteger, primary_key=True, autoincrement=True)
    advice_id = Column(BigInteger, ForeignKey("advice.advice.advice_id"), nullable=False)
    source_id = Column(BigInteger, ForeignKey("regulatory.regulatory_sources.source_id"), nullable=False)
    reference_note = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    advice = relationship("Advice", back_populates="source_links")
