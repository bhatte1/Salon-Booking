from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    customer_name: Mapped[str] = mapped_column(String(120))
    customer_email: Mapped[str] = mapped_column(String(200), index=True)

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    user = relationship("User")

    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    service = relationship("Service")

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=False), index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=False), index=True)

    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)

    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    @property
    def service_name(self) -> str | None:
        """Expose the related service's customer-facing name in API responses."""
        return self.service.name if self.service else None
