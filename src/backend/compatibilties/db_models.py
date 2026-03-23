# src/backend/compatibilities/db_models.py
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class InformedNonCompatibleMLC(Base):
    __tablename__ = "informed_non_compatible_mlc"
    __table_args__ = (
        UniqueConstraint("mlc", name="uq_informed_non_compatible_mlc_mlc"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mlc: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    has_exception: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        default=False,
        index=True,
    )
    informed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )