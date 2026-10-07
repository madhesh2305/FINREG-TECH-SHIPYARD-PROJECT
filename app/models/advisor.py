from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base, PK_BIGINT

class AdvisorProfile(Base):
    __tablename__ = "advisor_profiles"
    __table_args__ = {"schema": "advisor_management"}

    advisor_profile_id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("identity.users.user_id"), unique=True, nullable=False)
    organization_name = Column(String(200), nullable=False)
    professional_title = Column(String(150), nullable=False)
    specialization = Column(String(150), nullable=False)
    bio = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="advisor_profile")

class AdvisorInvitation(Base):
    __tablename__ = "advisor_invitations"
    __table_args__ = (
        CheckConstraint("invitation_status IN ('PENDING', 'ACCEPTED', 'REVOKED', 'EXPIRED')", name="chk_invitation_status"),
        {"schema": "advisor_management"}
    )

    invitation_id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("project_management.projects.project_id"), nullable=False, index=True)
    invited_by = Column(BigInteger, ForeignKey("identity.users.user_id"), nullable=False)
    advisor_email = Column(String(120), nullable=False)
    access_level = Column(String(50), nullable=False)
    invitation_status = Column(String(20), default="PENDING", nullable=False)
    invitation_token = Column(Text, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[invited_by])
