from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr, Field, field_serializer
from app.core.config import settings


class AppointmentCreate(BaseModel):
    customer_name: str
    customer_email: EmailStr
    service_id: int
    start_time: datetime
    notes: str | None = None


class AppointmentCreateAuthenticated(BaseModel):
    service_id: int
    start_time: datetime
    notes: str | None = None


class AppointmentOut(BaseModel):
    id: int
    customer_name: str
    customer_email: EmailStr
    service_id: int
    service_name: str | None = None
    start_time: datetime
    notes: str | None = None
    status: str
    salon_timezone: str = Field(default_factory=lambda: settings.salon_timezone or "UTC")

    @field_serializer("start_time")
    def serialize_start_time(self, value: datetime):
        # PostgreSQL stores UTC-naive values. Mark them as UTC in the API,
        # never let a browser interpret them as its local wall clock.
        utc = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
        return utc.isoformat().replace("+00:00", "Z")

    class Config:
        from_attributes = True

class AppointmentStatusUpdate(BaseModel):
    status: str


class AvailabilitySlotOut(BaseModel):
    start_time: str
    start_utc: str
    available: bool


class AppointmentAvailabilityOut(BaseModel):
    service_id: int
    date: str
    slots: list[AvailabilitySlotOut]
    timezone: str
    opening_time: str
    closing_time: str
