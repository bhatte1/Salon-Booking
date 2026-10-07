"""Allowlisted salon data access, shared by the conversational booking assistant."""
from fastapi import HTTPException
from app.api.appointment_routes import get_service_availability
from app.api.service_routes import list_services


class ModelUnavailable(Exception):
    pass


def require_customer(user):
    if not user or not user.is_active or user.role != 'customer':
        raise HTTPException(403, 'Customer access required')


def retrieve_services(db, user):
    require_customer(user)
    return [{'id':svc.id, 'name':svc.name, 'price_cents':svc.price_cents,
             'duration_minutes':svc.duration_minutes} for svc in list_services(db=db)]


def retrieve_availability(db, user, service_id, booking_date):
    require_customer(user)
    return get_service_availability(service_id=service_id, booking_date=booking_date,
                                    current_user=user, db=db)
