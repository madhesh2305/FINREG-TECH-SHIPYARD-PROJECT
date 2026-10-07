from sqlalchemy import BigInteger, Integer
from sqlalchemy.orm import DeclarativeBase

# Primary key helper: BIGINT in PostgreSQL, INTEGER in SQLite for autoincrement compatibility
PK_BIGINT = BigInteger().with_variant(Integer, "sqlite")

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy domain models."""
    pass
