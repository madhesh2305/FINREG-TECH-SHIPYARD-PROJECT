from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base, PK_BIGINT

class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "identity"}

    role_id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "identity"}

    user_id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    role_id = Column(BigInteger, ForeignKey("identity.roles.role_id"), nullable=False)
    full_name = Column(String(150), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    role = relationship("Role", back_populates="users")
    memberships = relationship("ProjectMember", back_populates="user")
    advisor_profile = relationship("AdvisorProfile", back_populates="user", uselist=False)

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    __table_args__ = {"schema": "identity"}

    token_id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    jti = Column(String(255), unique=True, index=True, nullable=True)
    token_signature = Column(String(255), unique=True, index=True, nullable=False)
    revoked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = {"schema": "identity"}

    id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("identity.users.user_id"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
