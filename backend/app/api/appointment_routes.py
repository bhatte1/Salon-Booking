from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.service import Service
from app.schemas.appointment import AppointmentCreate, AppointmentOut

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.appointment import AppointmentCreateAuthenticated

from app.schemas.appointment import AppointmentStatusUpdate

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
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
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


@router.post("/me", response_model=AppointmentOut)
def create_my_appointment(
    payload: AppointmentCreateAuthenticated,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 0) Normalize time to UTC naive (same as your existing logic)
    start_utc = payload.start_time
    if start_utc.tzinfo is not None:
        start_utc = start_utc.astimezone(timezone.utc).replace(tzinfo=None)

    # 1) Ensure service exists
    svc = db.query(Service).filter(Service.id == payload.service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    # 2) Reject bookings in the past
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    if start_utc < now_utc:
        raise HTTPException(status_code=400, detail="Cannot book in the past")

    # 3) Advisory lock to reduce race conditions
    minute_bucket = int(start_utc.timestamp() // 60)
    db.execute(
        text("SELECT pg_advisory_xact_lock(:k1, :k2)"),
        {"k1": int(payload.service_id), "k2": minute_bucket},
    )

    # 4) Compute end time
    end_utc = start_utc + timedelta(minutes=svc.duration_minutes)

    # 5) Canonical overlap check
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

    # 6) Create appointment linked to current user
    appt = Appointment(
        user_id=current_user.id,
        customer_name=current_user.full_name,
        customer_email=current_user.email,
        service_id=payload.service_id,
        start_time=start_utc,
        end_time=end_utc,
        status="pending",
        notes=payload.notes,
    )

    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt

@router.get("/me/list", response_model=list[AppointmentOut])
def list_my_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Appointment)
        .filter(Appointment.user_id == current_user.id)
        .order_by(Appointment.start_time.desc())
        .all()
    )


@router.get("/owner/all", response_model=list[AppointmentOut])
def list_all_appointments_for_owner(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can view all appointments")

    return (
        db.query(Appointment)
        .order_by(Appointment.start_time.desc())
        .all()
    )

@router.patch("/owner/{appointment_id}/status", response_model=AppointmentOut)
def update_appointment_status(
    appointment_id: int,
    payload: AppointmentStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can update appointment status")

    allowed_statuses = {"pending", "confirmed", "completed", "cancelled"}
    if payload.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")

    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.status = payload.status
    db.commit()
    db.refresh(appt)
    return appt