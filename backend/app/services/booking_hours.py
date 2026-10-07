"""Shared salon-local business-hour policy; all query/storage instants remain UTC."""
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from fastapi import HTTPException
from app.core.config import settings

BUSINESS_OPEN_HOUR = 8
BUSINESS_CLOSE_HOUR = 19


def salon_zone():
    try:
        if not settings.salon_timezone:
            raise ValueError()
        return ZoneInfo(settings.salon_timezone)
    except (ValueError, ZoneInfoNotFoundError):
        raise HTTPException(503, 'Salon timezone is not configured. Please contact the salon.')


def utc_naive(instant):
    return (instant.replace(tzinfo=timezone.utc) if instant.tzinfo is None else instant).astimezone(timezone.utc).replace(tzinfo=None)


def business_day_bounds(local_date):
    zone = salon_zone()
    opened = datetime.combine(local_date, time(BUSINESS_OPEN_HOUR), zone)
    closed = datetime.combine(local_date, time(BUSINESS_CLOSE_HOUR), zone)
    return utc_naive(opened), utc_naive(closed)


def validate_business_hours(start_time, end_time):
    start, end = utc_naive(start_time), utc_naive(end_time)
    local_date = start.replace(tzinfo=timezone.utc).astimezone(salon_zone()).date()
    opened, closed = business_day_bounds(local_date)
    if start < opened or end > closed or end <= start:
        raise HTTPException(400, f'Appointments must start and finish within 08:00–19:00 ({salon_zone()}).')


def booking_policy():
    return {'opening_time':'08:00', 'closing_time':'19:00', 'timezone':str(salon_zone())}
