from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    __table_args__ = (
        CheckConstraint("analysis_status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')", name="chk_ai_analysis_status"),
        {"schema": "ai"}
    )

    analysis_id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("project_management.projects.project_id"), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False)
    prompt_text = Column(Text, nullable=False)
    output_summary = Column(Text, nullable=False)
    model_name = Column(String(100), nullable=False)
    analysis_status = Column(String(20), default="COMPLETED", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    conflicts = relationship("ConflictGap", back_populates="analysis", cascade="all, delete-orphan")

class AIAnalysisAdvice(Base):
    __tablename__ = "ai_analysis_advice"
    __table_args__ = (
        UniqueConstraint("analysis_id", "advice_id", name="uq_ai_analysis_advice"),
        {"schema": "ai"}
    )

    ai_analysis_advice_id = Column(BigInteger, primary_key=True, autoincrement=True)
    analysis_id = Column(BigInteger, ForeignKey("ai.ai_analyses.analysis_id"), nullable=False)
    advice_id = Column(BigInteger, ForeignKey("advice.advice.advice_id"), nullable=False)

class AIAnalysisSource(Base):
    __tablename__ = "ai_analysis_sources"
    __table_args__ = (
        UniqueConstraint("analysis_id", "source_id", name="uq_ai_analysis_source"),
        CheckConstraint("relevance_score IS NULL OR (relevance_score >= 0 AND relevance_score <= 1)", name="chk_relevance_score"),
        {"schema": "ai"}
    )

    ai_analysis_source_id = Column(BigInteger, primary_key=True, autoincrement=True)
    analysis_id = Column(BigInteger, ForeignKey("ai.ai_analyses.analysis_id"), nullable=False)
    source_id = Column(BigInteger, ForeignKey("regulatory.regulatory_sources.source_id"), nullable=False)
    relevance_score = Column(Numeric(5, 4), nullable=True)
    retrieval_rank = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class ConflictGap(Base):
    __tablename__ = "conflict_gaps"
    __table_args__ = (
        CheckConstraint("issue_type IN ('CONFLICT', 'GAP', 'ASSUMPTION_DIVERGENCE')", name="chk_conflict_gap_type"),
        CheckConstraint("severity IN ('LOW', 'MEDIUM', 'HIGH')", name="chk_conflict_gap_severity"),
        CheckConstraint("review_status IN ('OPEN', 'UNDER_REVIEW', 'RESOLVED', 'DISMISSED')", name="chk_conflict_gap_status"),
        {"schema": "ai"}
    )

    conflict_gap_id = Column(BigInteger, primary_key=True, autoincrement=True)
    analysis_id = Column(BigInteger, ForeignKey("ai.ai_analyses.analysis_id"), nullable=False)
    project_id = Column(BigInteger, ForeignKey("project_management.projects.project_id"), nullable=False, index=True)
    issue_type = Column(String(50), nullable=False)
    title = Column(String(250), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), default="MEDIUM", nullable=False)
    review_status = Column(String(20), default="OPEN", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    analysis = relationship("AIAnalysis", back_populates="conflicts")
