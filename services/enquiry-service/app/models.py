from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Enquiry(Base):
    __tablename__ = "enquiries"

    enquiry_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    property_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    customer_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    customer_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    customer_contact: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    viewing_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="Pending",
        nullable=False,
    )
