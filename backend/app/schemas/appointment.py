from pydantic import BaseModel, EmailStr
from datetime import datetime

class AppointmentCreate(BaseModel):
    customer_name: str
    customer_email: EmailStr
    service_id: int
    start_time: datetime
    notes: str | None = None

class AppointmentOut(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    service_id: int
    start_time: datetime
    notes: str | None

    class Config:
        from_attributes = True
