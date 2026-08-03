from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.service import Service


DEFAULT_SERVICES = [
    {"name": "Classic Haircut", "price_cents": 3500, "duration_minutes": 30},
    {"name": "Hair Color", "price_cents": 8500, "duration_minutes": 90},
    {"name": "Refreshing Facial", "price_cents": 6500, "duration_minutes": 60},
    {"name": "Relaxing Massage", "price_cents": 9000, "duration_minutes": 60},
]


def seed_default_services() -> None:
    db = SessionLocal()
    try:
        has_services = db.query(Service.id).first()
        if has_services:
            return

        for service in DEFAULT_SERVICES:
            db.add(Service(**service))
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_default_services()
    yield


app = FastAPI(title="Salon Booking API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/health")
def health():
    return {"status": "ok"}
