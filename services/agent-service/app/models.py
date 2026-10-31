from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    agent_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    contact_number: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    specialization: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    assigned_property_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )