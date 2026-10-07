from fastapi import APIRouter
from app.api.service_routes import router as service_router
from app.api.appointment_routes import router as appointment_router
from app.api.auth_routes import router as auth_router

from app.api.chat_routes import router as chat_router

api_router = APIRouter(prefix="/api")
api_router.include_router(service_router)
api_router.include_router(appointment_router)
api_router.include_router(auth_router)
api_router.include_router(chat_router)
