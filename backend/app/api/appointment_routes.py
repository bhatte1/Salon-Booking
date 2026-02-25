from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.service import Service
from app.schemas.appointment import AppointmentCreate, AppointmentOut

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("", response_model=list[AppointmentOut])
def list_appointments(db: Session = Depends(get_db)):
    return db.query(Appointment).order_by(Appointment.start_time.desc()).all()


@router.post("", response_model=AppointmentOut)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    # 0) Normalize time to UTC naive (consistent storage)
    # Frontend sends ISO "Z" timestamps => timezone-aware UTC datetime
    start_utc = payload.start_time
    if start_utc.tzinfo is not None:
        start_utc = start_utc.astimezone(timezone.utc).replace(tzinfo=None)

    # 1) Ensure service exists
    svc = db.query(Service).filter(Service.id == payload.service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    # 2) Reject bookings in the past
    now_utc = datetime.utcnow()
    if start_utc < now_utc:
        raise HTTPException(status_code=400, detail="Cannot book in the past")

    # 3) System-design: advisory lock to prevent race condition
    # Lock key: (service_id, minute_bucket)
    minute_bucket = int(start_utc.timestamp() // 60)
    db.execute(
        text("SELECT pg_advisory_xact_lock(:k1, :k2)"),
        {"k1": int(payload.service_id), "k2": minute_bucket},
    )

    # 4) Check overlap (basic rule: same service cannot overlap)
    end_utc = start_utc + timedelta(minutes=svc.duration_minutes)
    window_start = start_utc - timedelta(minutes=svc.duration_minutes)

    conflict = (
        db.query(Appointment)
        .filter(
            Appointment.service_id == payload.service_id,
            Appointment.start_time < end_utc,
            Appointment.end_time > start_utc,
        )
        .first()
    )

    if conflict:
        raise HTTPException(status_code=409, detail="Time slot already booked")

    # 5) Create appointment
    appt = Appointment(
        customer_name=payload.customer_name,
        customer_email=str(payload.customer_email),
        service_id=payload.service_id,
        start_time=start_utc,
        end_time=end_utc,  # 👈 THIS LINE IS THE IMPORTANT ONE
        notes=payload.notes,
    )

    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt