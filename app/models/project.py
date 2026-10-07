from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base, PK_BIGINT

class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')", name="chk_projects_status"),
        {"schema": "project_management"}
    )

    project_id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    project_name = Column(String(200), nullable=False)
    project_code = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), default="ACTIVE", nullable=False)
    created_by = Column(BigInteger, ForeignKey("identity.users.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    creator = relationship("User", foreign_keys=[created_by])
    profile = relationship("ProjectProfile", back_populates="project", uselist=False, cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    requirements = relationship("RegulatoryRequirement", back_populates="project", cascade="all, delete-orphan")
    invitations = relationship("AdvisorInvitation", back_populates="project", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="project", cascade="all, delete-orphan")

class ProjectProfile(Base):
    __tablename__ = "project_profiles"
    __table_args__ = {"schema": "project_management"}

    project_profile_id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("project_management.projects.project_id"), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    jurisdiction = Column(String(100), nullable=False)
    regulatory_scope = Column(Text, nullable=False)
    objectives = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="profile")

class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member"),
        CheckConstraint("member_status IN ('ACTIVE', 'REVOKED')", name="chk_project_member_status"),
        CheckConstraint("service_role IN ('OWNER', 'LEGAL', 'REGULATORY', 'TECH', 'FUNDING_BUSINESS', 'MARKETING')", name="chk_project_member_service_role"),
        {"schema": "project_management"}
    )

    project_member_id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("project_management.projects.project_id"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("identity.users.user_id"), nullable=False, index=True)
    service_role = Column(String(50), default="OWNER", nullable=False)
    service_scope = Column(String(100), default="PROJECT_CONTROL", nullable=False)
    member_status = Column(String(20), default="ACTIVE", nullable=False)
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="memberships")
