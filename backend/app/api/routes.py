from fastapi import APIRouter
from app.api.service_routes import router as service_router
from app.api.appointment_routes import router as appointment_router

api_router = APIRouter(prefix="/api")
api_router.include_router(service_router)
api_router.include_router(appointment_router)
