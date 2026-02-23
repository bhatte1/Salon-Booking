from pydantic import BaseModel

class ServiceCreate(BaseModel):
    name: str
    price_cents: int
    duration_minutes: int

class ServiceOut(BaseModel):
    id: int
    name: str
    price_cents: int
    duration_minutes: int

    class Config:
        from_attributes = True
