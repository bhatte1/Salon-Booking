from datetime import datetime
from pydantic import BaseModel, EmailStr


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
    start_time: datetime
    notes: str | None = None
    status: str

    class Config:
        from_attributes = True

class AppointmentStatusUpdate(BaseModel):
    status: str