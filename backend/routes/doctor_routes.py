import json
from datetime import date, datetime, timedelta
from flask import Blueprint, jsonify, request, g

from extensions import db
from models.appointment import Appointment, AppointmentStatus
from models.models import Doctor, DoctorAvailability, Prescription
from models.patient import Patient

doctor_bp = Blueprint("doctor_bp", __name__, url_prefix="/api/doctor")
MISSED_APPOINTMENT_GRACE_MINUTES = 30


def _require_doctor_route_access(doctor_id):
    if not g.user:
        msg = getattr(g, "auth_error", "Authentication required")
        return jsonify({"message": msg}), 401
    
    role = (getattr(g.user, "role", "") or "").strip().lower()
    if role not in {"doctor", "admin"}:
        return jsonify({"error": "Doctor role required"}), 403

    if role == "doctor":
        if g.user.id != doctor_id:
            return jsonify({"error": "Forbidden: doctor identity mismatch"}), 403
            
    return None


def _parse_prescription_text(medications_json):
    try:
        meds = json.loads(medications_json or "[]")
        if isinstance(meds, list):
            values = [str(item).strip() for item in meds if str(item).strip()]
            return "\n".join(values)
    except Exception:
        pass
    return ""


def _auto_cancel_missed_booked_for_doctor(doctor_id):
    cutoff = datetime.now() - timedelta(minutes=MISSED_APPOINTMENT_GRACE_MINUTES)
    stale_rows = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status == AppointmentStatus.BOOKED,
        Appointment.appointment_datetime < cutoff,
    ).all()
    if not stale_rows:
        return 0
    for appt in stale_rows:
        appt.status = AppointmentStatus.CANCELLED
    db.session.commit()
    return len(stale_rows)


def _get_reference_date(doctor_id):
    today = datetime.now().date()
    ordered_rows = (
        Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status != AppointmentStatus.CANCELLED,
        )
        .order_by(Appointment.appointment_datetime.asc())
        .all()
    )
    if not ordered_rows:
        return today

    for appt in ordered_rows:
        appt_date = appt.appointment_datetime.date()
        if appt_date >= today:
            return today

    future_booked = next(
        (appt for appt in ordered_rows if appt.status == AppointmentStatus.BOOKED),
        None,
    )
    if future_booked:
        return future_booked.appointment_datetime.date()

    return ordered_rows[0].appointment_datetime.date()


def _serialize_appointment(appt, rx, now_local):
    follow_up_date = rx.follow_up_date.isoformat() if rx and rx.follow_up_date else None
    can_treat_now = (
        appt.status == AppointmentStatus.BOOKED
        and appt.appointment_datetime is not None
        and appt.appointment_datetime <= now_local
    )
    can_edit_treatment = appt.status == AppointmentStatus.COMPLETED and rx is not None
    patient = appt.patient

    return {
        "id": appt.id,
        "reference": f"apt-{appt.id}",
        "datetime": appt.appointment_datetime.isoformat(),
        "date": appt.appointment_datetime.date().isoformat(),
        "time": appt.appointment_datetime.strftime("%I:%M %p").lstrip("0"),
        "status": appt.status,
        "patient_name": patient.name if patient else f"Patient {appt.patient_id}",
        "patient_id": patient.id if patient else appt.patient_id,
        "patient_uid": (patient.patient_uid if patient and patient.patient_uid else f"patient-{appt.patient_id}"),
        "patient_email": patient.email if patient else None,
        "patient_phone": patient.phone if patient else None,
        "has_treatment": rx is not None,
        "can_treat_now": can_treat_now,
        "can_edit_treatment": can_edit_treatment,
        "action_label": "Edit Treatment" if can_edit_treatment else ("Add Treatment" if can_treat_now else "Await Time"),
        "follow_up_date": follow_up_date,
    }


@doctor_bp.route("/<int:doctor_id>/dashboard", methods=["GET"])
def dashboard(doctor_id):
    auth_error = _require_doctor_route_access(doctor_id)
    if auth_error:
        return auth_error

    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    reference_date = _get_reference_date(doctor_id)
    start_of_today = datetime.combine(reference_date, datetime.min.time())
    end_of_7th_day = datetime.combine(reference_date + timedelta(days=6), datetime.max.time())

    today_count = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status == AppointmentStatus.BOOKED,
        db.func.date(Appointment.appointment_datetime) == reference_date,
    ).count()

    upcoming_count = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status == AppointmentStatus.BOOKED,
        Appointment.appointment_datetime >= start_of_today,
        Appointment.appointment_datetime <= end_of_7th_day,
    ).count()

    total_patients = db.session.query(db.func.count(db.func.distinct(Appointment.patient_id))).filter(
        Appointment.doctor_id == doctor_id
    ).scalar()

    now_local = datetime.now()
    schedule = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status != AppointmentStatus.CANCELLED,
        Appointment.appointment_datetime >= start_of_today,
        Appointment.appointment_datetime <= end_of_7th_day,
    ).order_by(Appointment.appointment_datetime.asc()).all()
    availability = DoctorAvailability.query.filter_by(doctor_id=doctor_id).all()
    rx_by_appointment = {
        rx.appointment_id: rx
        for rx in Prescription.query.filter(
            Prescription.doctor_id == doctor_id,
            Prescription.appointment_id.isnot(None),
        ).all()
    }

    schedule_data = []
    completed_data = []
    for appt in schedule:
        rx = rx_by_appointment.get(appt.id)
        item = _serialize_appointment(appt, rx, now_local)
        schedule_data.append(item)

        if appt.status == AppointmentStatus.COMPLETED:
            completed_data.append(
                {
                    "appointment_id": appt.id,
                    "patient_name": item["patient_name"],
                    "datetime": item["datetime"],
                    "follow_up_date": item["follow_up_date"],
                }
            )

    availability_data = [{"date": av.date.isoformat(), "is_available": bool(av.is_available)} for av in availability]

    return jsonify(
        {
            "doctor": {
                "id": doctor.id,
                "name": doctor.name,
                "email": doctor.email,
                "specialization": doctor.specialization,
            },
            "stats": {
                "today_appointments": today_count,
                "upcoming_7_days": upcoming_count,
                "total_patients": total_patients or 0,
            },
            "schedule": schedule_data,
            "availability": availability_data,
            "completed_appointments": completed_data,
            "reference_date": reference_date.isoformat(),
        }
    )


@doctor_bp.route("/<int:doctor_id>/availability", methods=["POST"])
def update_availability(doctor_id):
    auth_error = _require_doctor_route_access(doctor_id)
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    dates = data.get("dates")
    if not isinstance(dates, dict):
        return jsonify({"error": "Invalid payload: dates must be an object"}), 400

    for date_str, is_available in dates.items():
        try:
            parsed_date = date.fromisoformat(date_str)
            parsed_is_available = bool(is_available)
        except Exception:
            return jsonify({"error": f"Invalid availability payload for '{date_str}'"}), 400

        existing = DoctorAvailability.query.filter_by(doctor_id=doctor_id, date=parsed_date).first()
        if existing:
            existing.is_available = parsed_is_available
        else:
            db.session.add(
                DoctorAvailability(
                    doctor_id=doctor_id,
                    date=parsed_date,
                    is_available=parsed_is_available,
                )
            )

    db.session.commit()
    return jsonify({"success": True})


@doctor_bp.route("/<int:doctor_id>/appointments/<int:appointment_id>/treatment", methods=["GET"])
def get_treatment(doctor_id, appointment_id):
    auth_error = _require_doctor_route_access(doctor_id)
    if auth_error:
        return auth_error

    appointment = Appointment.query.filter_by(id=appointment_id, doctor_id=doctor_id).first()
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    rx = Prescription.query.filter_by(appointment_id=appointment_id, doctor_id=doctor_id).first()
    history_query = Prescription.query.filter(
        Prescription.doctor_id == doctor_id,
        Prescription.patient_id == appointment.patient_id,
    )
    if rx:
        history_query = history_query.filter(Prescription.id != rx.id)
    previous_rows = history_query.order_by(Prescription.prescribed_at.desc()).limit(5).all()
    history = [
        {
            "id": row.id,
            "appointment_id": row.appointment_id,
            "diagnosis": row.diagnosis,
            "prescription": _parse_prescription_text(row.medications_json),
            "notes": row.notes or "",
            "prescribed_at": row.prescribed_at.isoformat() if row.prescribed_at else None,
        }
        for row in previous_rows
    ]
    if not rx:
        return jsonify({"treatment": None, "history": history})

    return jsonify(
        {
            "treatment": {
                "id": rx.id,
                "appointment_id": appointment_id,
                "diagnosis": rx.diagnosis,
                "prescription": _parse_prescription_text(rx.medications_json),
                "notes": rx.notes or "",
                "follow_up_date": rx.follow_up_date.isoformat() if rx.follow_up_date else None,
            },
            "history": history,
        }
    )


@doctor_bp.route("/<int:doctor_id>/appointments/<int:appointment_id>/treatment", methods=["POST"])
def create_or_update_treatment(doctor_id, appointment_id):
    auth_error = _require_doctor_route_access(doctor_id)
    if auth_error:
        return auth_error

    data = request.get_json() or {}
    diagnosis = (data.get("diagnosis") or "").strip()
    prescription_text = (data.get("prescription") or "").strip()
    notes = (data.get("notes") or "").strip()
    follow_up_date_raw = (data.get("follow_up_date") or "").strip()

    if not diagnosis or not prescription_text:
        return jsonify({"error": "Diagnosis and prescription are required"}), 400

    appointment = Appointment.query.filter_by(id=appointment_id, doctor_id=doctor_id).first()
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404
    if appointment.status == AppointmentStatus.CANCELLED:
        return jsonify({"error": "Cannot add or update treatment for cancelled appointment"}), 409
    if appointment.status == AppointmentStatus.BOOKED and appointment.appointment_datetime and appointment.appointment_datetime > datetime.now():
        return jsonify({"error": "Treatment can be added only at or after appointment time"}), 409

    follow_up_date = None
    if follow_up_date_raw:
        try:
            follow_up_date = date.fromisoformat(follow_up_date_raw)
        except ValueError:
            return jsonify({"error": "follow_up_date must be YYYY-MM-DD"}), 400

    rx = Prescription.query.filter_by(appointment_id=appointment_id, doctor_id=doctor_id).first()
    if rx:
        # Keep immutable edit history by snapshotting old values before overwrite.
        snapshot = Prescription(
            appointment_id=appointment_id,
            patient_id=appointment.patient_id,
            doctor_id=doctor_id,
            diagnosis=rx.diagnosis,
            medications_json=rx.medications_json,
            instructions=rx.instructions,
            notes=rx.notes,
            follow_up_date=rx.follow_up_date,
            status="archived",
        )
        db.session.add(snapshot)

        rx.diagnosis = diagnosis
        rx.medications_json = json.dumps([prescription_text])
        rx.notes = notes or None
        rx.instructions = notes or None
        rx.follow_up_date = follow_up_date
        rx.status = "active"
    else:
        rx = Prescription(
            appointment_id=appointment_id,
            patient_id=appointment.patient_id,
            doctor_id=doctor_id,
            diagnosis=diagnosis,
            medications_json=json.dumps([prescription_text]),
            instructions=notes or None,
            notes=notes or None,
            follow_up_date=follow_up_date,
            status="active",
        )
        db.session.add(rx)

    appointment.status = AppointmentStatus.COMPLETED
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "treatment": {
                "id": rx.id,
                "appointment_id": appointment_id,
                "diagnosis": rx.diagnosis,
                "prescription": prescription_text,
                "notes": rx.notes,
                "follow_up_date": rx.follow_up_date.isoformat() if rx.follow_up_date else None,
            },
        }
    )


@doctor_bp.route("/<int:doctor_id>/completed-appointments", methods=["GET"])
def completed_appointments(doctor_id):
    auth_error = _require_doctor_route_access(doctor_id)
    if auth_error:
        return auth_error

    completed = (
        Appointment.query.filter_by(doctor_id=doctor_id, status=AppointmentStatus.COMPLETED)
        .order_by(Appointment.appointment_datetime.desc())
        .all()
    )
    rx_by_appointment = {
        rx.appointment_id: rx
        for rx in Prescription.query.filter(
            Prescription.doctor_id == doctor_id,
            Prescription.appointment_id.isnot(None),
        ).all()
    }

    data = []
    for appt in completed:
        rx = rx_by_appointment.get(appt.id)
        data.append(
            {
                "appointment_id": appt.id,
                "patient_name": appt.patient.name if appt.patient else f"Patient {appt.patient_id}",
                "datetime": appt.appointment_datetime.isoformat(),
                "follow_up_date": rx.follow_up_date.isoformat() if rx and rx.follow_up_date else None,
                "has_treatment": rx is not None,
                "diagnosis": rx.diagnosis if rx else None,
                "prescription": _parse_prescription_text(rx.medications_json) if rx else None,
                "notes": rx.notes if rx else None,
            }
        )

    return jsonify({"completed_appointments": data})


@doctor_bp.route("/<int:doctor_id>/appointments/<int:appointment_id>", methods=["GET"])
def appointment_detail(doctor_id, appointment_id):
    auth_error = _require_doctor_route_access(doctor_id)
    if auth_error:
        return auth_error

    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    appointment = Appointment.query.filter_by(id=appointment_id, doctor_id=doctor_id).first()
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    rx = Prescription.query.filter_by(appointment_id=appointment_id, doctor_id=doctor_id).first()
    appointment_data = _serialize_appointment(appointment, rx, datetime.now())

    return jsonify(
        {
            "doctor": {
                "id": doctor.id,
                "name": doctor.name,
                "email": doctor.email,
                "specialization": doctor.specialization,
            },
            "appointment": appointment_data,
            "patient": {
                "id": appointment.patient.id,
                "patient_uid": appointment_data["patient_uid"],
                "name": appointment.patient.name,
                "email": appointment.patient.email,
                "phone": appointment.patient.phone,
            },
            "treatment": (
                {
                    "id": rx.id,
                    "diagnosis": rx.diagnosis,
                    "prescription": _parse_prescription_text(rx.medications_json),
                    "notes": rx.notes or "",
                    "follow_up_date": rx.follow_up_date.isoformat() if rx.follow_up_date else None,
                }
                if rx
                else None
            ),
        }
    )


@doctor_bp.route("/<int:doctor_id>/appointments/<int:appointment_id>/status", methods=["PATCH"])
def update_appointment_status(doctor_id, appointment_id):
    auth_error = _require_doctor_route_access(doctor_id)
    if auth_error:
        return auth_error

    data = request.get_json() or {}
    status = (data.get("status") or "").strip().lower()
    if status not in {AppointmentStatus.BOOKED, AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED}:
        return jsonify({"error": "status must be booked/completed/cancelled"}), 400

    appointment = Appointment.query.filter_by(id=appointment_id, doctor_id=doctor_id).first()
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    if status == AppointmentStatus.COMPLETED:
        existing_rx = Prescription.query.filter_by(appointment_id=appointment_id, doctor_id=doctor_id).first()
        if not existing_rx:
            return jsonify({"error": "Add prescription/treatment before marking completed"}), 409

    appointment.status = status
    db.session.commit()
    return jsonify({"success": True, "appointment_id": appointment.id, "status": appointment.status})
