import io
import json
import re
from collections import OrderedDict
from flask import Response, Blueprint, request, jsonify, g
from datetime import datetime, timedelta

from extensions import db
from models.patient import Patient
from models.appointment import Appointment, AppointmentStatus
from models.models import Doctor, DoctorSchedule, Department, Prescription

# ==========================================
# Dashboard & Patient Routes Blueprint
# ==========================================
# This module provides all functionalities related to the patient facing dashboard,
# including booking appointments, viewing medical history, and generating reports.

dashboard_bp = Blueprint("dashboard_bp", __name__)

DAILY_BOOKING_LIMIT = 3

@dashboard_bp.before_request
def require_login_for_dashboard_api():
    """
    Ensures the user is logged in before accessing any dashboard-related data.
    """
    if not g.user:
        msg = getattr(g, "auth_error", "Authentication required")
        return jsonify({"message": msg}), 401
    return None


def _parse_medications(raw_json):
    try:
        meds = json.loads(raw_json or "[]")
        if isinstance(meds, list):
            return meds
    except Exception:
        pass
    return []


def _serialize_prescription(rx):
    return {
        "id": rx.id,
        "doctor": rx.doctor.name if rx.doctor else "N/A",
        "diagnosis": rx.diagnosis,
        "medications": _parse_medications(rx.medications_json),
        "instructions": rx.instructions or "",
        "notes": rx.notes or "",
        "status": rx.status or "active",
        "prescribed_at": rx.prescribed_at.strftime("%Y-%m-%d %H:%M") if rx.prescribed_at else None,
        "prescribed_on": rx.prescribed_at.strftime("%B %d, %Y") if rx.prescribed_at else None,
        "follow_up_date": rx.follow_up_date.strftime("%Y-%m-%d") if rx.follow_up_date else None,
        "follow_up_full": rx.follow_up_date.strftime("%B %d, %Y") if rx.follow_up_date else None,
    }


def _derive_appointment_state(apt, now=None):
    now = now or datetime.now()
    dt = apt.appointment_datetime
    status = apt.status

    base = {
        "display_status": status or AppointmentStatus.BOOKED,
        "display_label": (status or AppointmentStatus.BOOKED).replace("_", " "),
        "reschedulable": False,
        "cancelable": False,
        "status_note": "",
    }

    if not dt:
        return base

    if status == AppointmentStatus.COMPLETED:
        base["display_status"] = "completed"
        base["display_label"] = "Completed"
        return base

    if status == AppointmentStatus.CANCELLED:
        base["display_status"] = "cancelled"
        base["display_label"] = "Cancelled"
        return base

    # For booked appointments, derive missed/not-visited states based on elapsed time.
    if dt >= now:
        base["display_status"] = "booked"
        base["display_label"] = "Booked"
        base["reschedulable"] = True
        base["cancelable"] = True
        return base

    if dt.date() == now.date():
        base["display_status"] = "not_attended"
        base["display_label"] = "Not Attended"
        base["reschedulable"] = True
        base["status_note"] = "Appointment time passed today. Please reschedule."
        return base

    elapsed = now - dt
    if elapsed >= timedelta(days=2):
        base["display_status"] = "not_visited_cancelled"
        base["display_label"] = "Not Visited Cancelled"
        base["status_note"] = "Appointment not visited for 2+ days. Marked as cancelled."
    else:
        base["display_status"] = "not_visited"
        base["display_label"] = "Not Visited"
        base["status_note"] = "Appointment was missed."
    return base


def _build_simple_pdf(lines):
    # Minimal single/multi-page PDF generator without external deps.
    pages = []
    page_lines = []
    max_lines_per_page = 34
    for line in lines:
        page_lines.append(line)
        if len(page_lines) >= max_lines_per_page:
            pages.append(page_lines)
            page_lines = []
    if page_lines:
        pages.append(page_lines)
    if not pages:
        pages = [["HMS Medical Report"]]

    objects = []

    def _esc(text):
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    # 1: catalog, 2: pages root, 3..5 fonts
    objects.append("<< /Type /Catalog /Pages 2 0 R >>")

    page_obj_ids = []
    content_obj_ids = []
    # 1=catalog, 2=pages root, 3=Helvetica, 4=Helvetica-Bold, 5=Helvetica-Oblique
    # Page/content objects must start after these.
    next_id = 6
    for _ in pages:
        page_obj_ids.append(next_id)
        next_id += 1
        content_obj_ids.append(next_id)
        next_id += 1

    kids = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_obj_ids)} >>")
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >>")

    for idx, page in enumerate(pages):
        page_obj = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >> >> "
            f"/Contents {content_obj_ids[idx]} 0 R >>"
        )
        objects.append(page_obj)

        y = 690
        page_num = idx + 1
        content_lines = []

        # Soft watermark (center diagonal)
        content_lines.append("q")
        content_lines.append("0.93 g")
        content_lines.append("BT")
        content_lines.append("/F2 54 Tf")
        content_lines.append("0.7071 0.7071 -0.7071 0.7071 150 300 Tm")
        content_lines.append("(HMS CONFIDENTIAL) Tj")
        content_lines.append("ET")
        content_lines.append("Q")

        # Header logo mark (vector square + pulse line)
        content_lines.append("q")
        content_lines.append("0.11 0.33 0.84 rg")
        content_lines.append("36 732 26 26 re f")
        content_lines.append("1 1 1 RG")
        content_lines.append("2 w")
        content_lines.append("39 745 m 43 745 l 45 740 l 49 751 l 53 744 l 59 744 l S")
        content_lines.append("Q")

        # Header text and report metadata
        content_lines.append("BT")
        content_lines.append("/F2 13 Tf")
        content_lines.append("1 0 0 1 72 746 Tm (HMS City Hospital) Tj")
        content_lines.append("/F1 9 Tf")
        content_lines.append("1 0 0 1 72 733 Tm (Official Medical Report - Patient Copy) Tj")
        content_lines.append("ET")

        # Header divider
        content_lines.append("q")
        content_lines.append("0.75 G")
        content_lines.append("1 w")
        content_lines.append("36 724 m 576 724 l S")
        content_lines.append("Q")

        # Body text
        content_lines.append("BT")
        content_lines.append("/F1 10 Tf")
        for line in page:
            safe = _esc(str(line))
            content_lines.append(f"1 0 0 1 40 {y} Tm ({safe}) Tj")
            y -= 16
            if y < 40:
                break
        content_lines.append("ET")

        # Footer
        content_lines.append("BT")
        content_lines.append("/F3 8 Tf")
        content_lines.append(f"1 0 0 1 40 22 Tm (Generated by HMS EMR | Page {page_num}) Tj")
        content_lines.append("1 0 0 1 395 22 Tm (Confidential - Authorized Access Only) Tj")
        content_lines.append("ET")
        content_stream = "\n".join(content_lines)
        objects.append(f"<< /Length {len(content_stream.encode('latin-1', errors='replace'))} >>\nstream\n{content_stream}\nendstream")

    pdf = "%PDF-1.4\n"
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf.encode("latin-1", errors="replace")))
        pdf += f"{i} 0 obj\n{obj}\nendobj\n"

    xref_start = len(pdf.encode("latin-1", errors="replace"))
    pdf += f"xref\n0 {len(objects) + 1}\n"
    pdf += "0000000000 65535 f \n"
    for i in range(1, len(objects) + 1):
        pdf += f"{offsets[i]:010d} 00000 n \n"
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF"

    return pdf.encode("latin-1", errors="replace")


def _line(width=82, char="-"):
    return char * width


def _wrap_text(value, width=78):
    text = str(value or "").strip()
    if not text:
        return ["N/A"]
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= width:
            cur = f"{cur} {w}"
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _add_wrapped_field(lines, label, value, label_width=20, width=78):
    wrapped = _wrap_text(value, width=width)
    lines.append(f"{label:<{label_width}}: {wrapped[0]}")
    for i in range(1, len(wrapped)):
        lines.append(f"{'':<{label_width}}  {wrapped[i]}")


def _normalize_medication_item(item):
    if isinstance(item, dict):
        return {
            "name": str(item.get("name") or item.get("medicine") or "Medication").strip(),
            "dose": str(item.get("dose") or item.get("strength") or "").strip(),
            "frequency": str(item.get("frequency") or item.get("timing") or "").strip(),
            "duration": str(item.get("duration") or "").strip(),
            "instruction": str(item.get("instruction") or item.get("notes") or "").strip(),
        }

    raw = str(item or "").strip()
    if not raw:
        return {
            "name": "Medication",
            "dose": "",
            "frequency": "",
            "duration": "",
            "instruction": "Take as directed",
        }

    name_part, instruction = raw, ""
    if " - " in raw:
        name_part, instruction = [p.strip() for p in raw.split(" - ", 1)]

    comma_parts = [p.strip() for p in name_part.split(",") if p.strip()]
    name_and_dose = comma_parts[0] if comma_parts else name_part
    frequency = comma_parts[1] if len(comma_parts) > 1 else ""
    duration = comma_parts[2] if len(comma_parts) > 2 else ""

    name = name_and_dose
    dose = ""
    dose_match = re.search(r"(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu))", name_and_dose, flags=re.IGNORECASE)
    if dose_match:
        dose = dose_match.group(1)
        name = name_and_dose.replace(dose, "").strip(" -")

    return {
        "name": name or "Medication",
        "dose": dose,
        "frequency": frequency,
        "duration": duration,
        "instruction": instruction or "Take as directed by physician",
    }


def _build_report_lines(patient, appointments, prescriptions, generated_at):
    now = datetime.now()
    total = len(appointments)
    upcoming = sum(1 for a in appointments if a.status == AppointmentStatus.BOOKED and a.appointment_datetime and a.appointment_datetime >= now)
    completed = sum(1 for a in appointments if a.status == AppointmentStatus.COMPLETED)
    cancelled = sum(1 for a in appointments if a.status == AppointmentStatus.CANCELLED)

    lines = []
    lines.append(_line(82, "="))
    lines.append("HMS CITY HOSPITAL")
    lines.append("Comprehensive Medical & Diagnostic Center")
    lines.append("Patient Medical Report")
    lines.append(_line(82, "="))
    lines.append(f"Generated On           : {generated_at.strftime('%B %d, %Y %I:%M %p')}")
    lines.append("Document Type          : Consolidated Clinical Summary")
    lines.append("")
    lines.append("PATIENT DEMOGRAPHICS")
    lines.append(_line(82, "-"))
    _add_wrapped_field(lines, "Patient Name", patient.name)
    _add_wrapped_field(lines, "Patient ID", patient.patient_uid)
    _add_wrapped_field(lines, "Email", patient.email)
    _add_wrapped_field(lines, "Gender", patient.gender)
    lines.append("")
    lines.append("VISIT SUMMARY")
    lines.append(_line(82, "-"))
    lines.append(f"{'Total Appointments':<20}: {total}")
    lines.append(f"{'Upcoming':<20}: {upcoming}")
    lines.append(f"{'Completed':<20}: {completed}")
    lines.append(f"{'Cancelled':<20}: {cancelled}")
    lines.append("")
    lines.append("APPOINTMENT HISTORY")
    lines.append(_line(82, "-"))
    if not appointments:
        lines.append("No appointment records found.")
    else:
        for idx, a in enumerate(appointments, 1):
            dt = a.appointment_datetime
            date_text = dt.strftime("%B %d, %Y") if dt else "N/A"
            time_text = dt.strftime("%I:%M %p").lstrip("0") if dt else "N/A"
            doctor_name = a.doctor.name if a.doctor else "N/A"
            dept = a.doctor.department.name if a.doctor and a.doctor.department else "N/A"

            lines.append(f"{idx:02d}. Status: {str(a.status).upper()}")
            lines.append(f"    Date/Time          : {date_text} at {time_text}")
            lines.append(f"    Consulting Doctor  : {doctor_name}")
            lines.append(f"    Department         : {dept}")
            lines.append(_line(82, "."))

    lines.append("")
    lines.append("PRESCRIPTION RECORDS")
    lines.append(_line(82, "-"))
    if not prescriptions:
        lines.append("No prescription records found.")
    else:
        by_doctor = OrderedDict()
        for rx in prescriptions:
            by_doctor.setdefault(rx.get("doctor") or "N/A", []).append(rx)

        for doctor_name, doctor_rx in by_doctor.items():
            lines.append(f"Prescribing Doctor     : {doctor_name}")
            lines.append(_line(82, "."))
            for idx, rx in enumerate(doctor_rx, 1):
                lines.append(f"Rx {idx:02d} | Prescription ID: {rx.get('id')} | Status: {str(rx.get('status') or 'active').upper()}")
                lines.append(f"    Date Issued        : {rx.get('prescribed_on') or 'N/A'}")
                _add_wrapped_field(lines, "    Clinical Diagnosis", rx.get("diagnosis") or "N/A", label_width=24, width=54)

                meds = rx.get("medications") or []
                lines.append("    Medication Plan    :")
                if not meds:
                    lines.append("      1) No medications documented.")
                else:
                    for med_idx, med in enumerate(meds, 1):
                        info = _normalize_medication_item(med)
                        dose_text = f" ({info['dose']})" if info.get("dose") else ""
                        lines.append(f"      {med_idx}) {info['name']}{dose_text}")
                        lines.append(f"         Frequency     : {info.get('frequency') or 'As directed'}")
                        lines.append(f"         Duration      : {info.get('duration') or 'As advised'}")
                        for wrapped in _wrap_text(info.get("instruction") or "Take as directed by physician", width=44):
                            lines.append(f"         Instruction   : {wrapped}")

                _add_wrapped_field(lines, "    General Advice", rx.get("instructions") or "N/A", label_width=24, width=54)
                _add_wrapped_field(lines, "    Follow-up Date", rx.get("follow_up_full") or "N/A", label_width=24, width=54)
                _add_wrapped_field(lines, "    Physician Notes", rx.get("notes") or "N/A", label_width=24, width=54)
                lines.append(_line(82, "."))

    lines.append("")
    lines.append(_line(82, "="))
    lines.append("Confidential Medical Record: For patient and authorized clinical use only.")
    lines.append("End of Report")
    lines.append(_line(82, "="))
    return lines


# ─────────────────────────────────────────
# API: DASHBOARD STATS
# ─────────────────────────────────────────

@dashboard_bp.route("/api/dashboard_data")
def get_dashboard_data():
    """
    Fetches the patient's dashboard summary, including visit statistics and
    basic profile information.
    """
    now  = datetime.now()
    now  = datetime.now()
    apts = Appointment.query.filter_by(patient_id=g.user.id).all()

    total     = len(apts)
    upcoming  = sum(1 for a in apts if a.status == AppointmentStatus.BOOKED    and a.appointment_datetime >= now)
    completed = sum(1 for a in apts if a.status == AppointmentStatus.COMPLETED)
    cancelled = sum(1 for a in apts if a.status == AppointmentStatus.CANCELLED)

    return jsonify({
        "status": "success",
        "stats": {
            "total_visits": total,
            "upcoming":     upcoming,
            "completed":    completed,
            "cancelled":    cancelled,
        },
        "patient": {
            "patient_uid": g.user.patient_uid,
            "name":        g.user.name,
            "email":       g.user.email,
            "gender":      g.user.gender,
        }
    })


# ─────────────────────────────────────────
# API: MY APPOINTMENTS (upcoming / past)
# ─────────────────────────────────────────
@dashboard_bp.route("/api/appointments", methods=["GET"])
def list_appointments():
    """
    Lists the patient's appointments, filtered by 'upcoming' or 'past' status.
    """
    tab = request.args.get("tab", "upcoming")
    now = datetime.now()
    base = Appointment.query.filter_by(patient_id=g.user.id)

    if tab == "upcoming":
        apts = (base
                .filter(Appointment.status == AppointmentStatus.BOOKED,
                        Appointment.appointment_datetime >= now)
                .order_by(Appointment.appointment_datetime.asc())
                .all())
    else:
        apts = (base
                .filter((Appointment.appointment_datetime < now) |
                        (Appointment.status != AppointmentStatus.BOOKED))
                .order_by(Appointment.appointment_datetime.desc())
                .all())

    def fmt(a):
        dt = a.appointment_datetime
        derived = _derive_appointment_state(a, now)
        return {
            "id":        a.id,
            "date":      dt.strftime("%d/%m/%Y").lstrip("0").replace("/0", "/") if dt else None,
            "date_full": dt.strftime("%A, %B %d, %Y") if dt else None,
            "time":      dt.strftime("%I:%M %p").lstrip("0") if dt else None,
            "appointment_datetime": dt.isoformat() if dt else None,
            "status":    a.get_derived_status(now),
            "display_status": derived["display_status"],
            "display_label": derived["display_label"],
            "reschedulable": derived["reschedulable"],
            "cancelable": derived["cancelable"],
            "status_note": derived["status_note"],
            "doctor":    a.doctor.name           if a.doctor else None,
            "specialty": a.doctor.specialization if a.doctor else None,
        }

    return jsonify({"status": "success", "tab": tab, "appointments": [fmt(a) for a in apts]})


# ─────────────────────────────────────────
# API: BOOK APPOINTMENT
# ─────────────────────────────────────────
@dashboard_bp.route("/api/appointments", methods=["POST"])
def book_appointment():
    """
    Validates and processes a new appointment booking request for the logged-in patient.
    Checks for slot clashes and daily booking limits.
    """
    d         = request.get_json() or {}
    doctor_id = d.get("doctor_id")
    date_str  = d.get("date")
    time_slot = d.get("time_slot", "").strip()

    if not all([doctor_id, date_str, time_slot]):
        return jsonify({"status": "error", "message": "doctor_id, date, time_slot required"}), 400

    doc = Doctor.query.get(doctor_id)
    if not doc:
        return jsonify({"status": "error", "message": "Doctor not found"}), 404

    try:
        apt_dt = datetime.strptime(f"{date_str} {time_slot}", "%Y-%m-%d %I:%M %p")
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid date/time format"}), 400

    # Rule 1: No past bookings
    if apt_dt < datetime.now():
        return jsonify({"status": "error", "message": "Cannot book appointments in the past"}), 400

    # Rule 2: Doctor's slot already taken
    doctor_clash = Appointment.query.filter_by(
        doctor_id            = doc.id,
        appointment_datetime = apt_dt,
        status               = AppointmentStatus.BOOKED
    ).first()
    if doctor_clash:
        return jsonify({"status": "error", "message": f"Dr. {doc.name} is already booked at {time_slot}."}), 409

    # Rule 3: Patient already has appointment at same time
    patient_time_clash = Appointment.query.filter_by(
        patient_id           = g.user.id,
        appointment_datetime = apt_dt,
        status               = AppointmentStatus.BOOKED
    ).first()
    if patient_time_clash:
        return jsonify({"status": "error", "message": f"You already have an appointment at {time_slot}."}), 409

    # Rule 4: Max 3 appointments per day
    day_start = apt_dt.replace(hour=0,  minute=0,  second=0,  microsecond=0)
    day_end   = apt_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    daily_count = Appointment.query.filter(
        Appointment.patient_id           == g.user.id,
        Appointment.status               == AppointmentStatus.BOOKED,
        Appointment.appointment_datetime >= day_start,
        Appointment.appointment_datetime <= day_end
    ).count()

    if daily_count >= DAILY_BOOKING_LIMIT:
        return jsonify({"status": "error", "message": f"Maximum {DAILY_BOOKING_LIMIT} appointments per day allowed."}), 429

    new_apt = Appointment(
        patient_id           = g.user.id,
        doctor_id            = doc.id,
        appointment_datetime = apt_dt,
        status               = AppointmentStatus.BOOKED,
    )
    db.session.add(new_apt)
    db.session.commit()

    return jsonify({
        "status":  "success",
        "message": f"Appointment booked with Dr. {doc.name} on {apt_dt.strftime('%B %d, %Y')} at {time_slot}"
    }), 201


# ─────────────────────────────────────────
# API: APPOINTMENT DETAIL
# ─────────────────────────────────────────
@dashboard_bp.route("/api/appointments/<int:apt_id>", methods=["GET"])

def get_appointment(apt_id):
    apt = Appointment.query.filter_by(id=apt_id, patient_id=g.user.id).first_or_404()
    dt  = apt.appointment_datetime
    derived = _derive_appointment_state(apt, datetime.now())
    return jsonify({
        "status": "success",
        "appointment": {
            "id":         apt.id,
            "date_full":  dt.strftime("%A, %B %d, %Y") if dt else None,
            "time":       dt.strftime("%I:%M %p").lstrip("0") if dt else None,
            "appointment_datetime": dt.isoformat() if dt else None,
            "status":     apt.status,
            "display_status": derived["display_status"],
            "display_label": derived["display_label"],
            "reschedulable": derived["reschedulable"],
            "cancelable": derived["cancelable"],
            "status_note": derived["status_note"],
            "doctor":     apt.doctor.name           if apt.doctor else None,
            "doctor_id":  apt.doctor_id,
            "specialty":  apt.doctor.specialization if apt.doctor else None,
            "department": apt.doctor.department.name if apt.doctor and apt.doctor.department else None,
        }
    })


# ─────────────────────────────────────────
# API: CANCEL APPOINTMENT
# ─────────────────────────────────────────
@dashboard_bp.route("/api/appointments/<int:apt_id>/cancel", methods=["POST"])
def cancel_appointment(apt_id):
    """
    Marks a booked appointment as 'CANCELLED' if it is in the future.
    """
    apt = Appointment.query.filter_by(id=apt_id, patient_id=g.user.id).first_or_404()

    if apt.status != AppointmentStatus.BOOKED:
        return jsonify({"status": "error", "message": f"Cannot cancel a '{apt.status}' appointment"}), 400

    if apt.appointment_datetime and apt.appointment_datetime < datetime.now():
        return jsonify({
            "status": "error",
            "message": "Past appointments cannot be cancelled."
        }), 400

    apt.status = AppointmentStatus.CANCELLED
    db.session.commit()
    return jsonify({"status": "success", "message": "Appointment cancelled"})


# ─────────────────────────────────────────
# API: RESCHEDULE APPOINTMENT
# ─────────────────────────────────────────
@dashboard_bp.route("/api/appointments/<int:apt_id>/reschedule", methods=["PUT"])

def reschedule_appointment(apt_id):
    apt = Appointment.query.filter_by(id=apt_id, patient_id=g.user.id).first_or_404()

    if apt.status not in {AppointmentStatus.BOOKED, AppointmentStatus.NOT_ATTENDED}:
        return jsonify({"status": "error", "message": "Only booked or not attended appointments can be rescheduled"}), 400

    now = datetime.now()
    apt_dt = apt.appointment_datetime
    if apt_dt and apt_dt.date() < now.date():
        return jsonify({
            "status": "error",
            "message": "Appointment was not visited and cannot be rescheduled after the day has passed."
        }), 400

    d        = request.get_json() or {}
    date_str = d.get("date")
    slot     = d.get("time_slot", "").strip()

    if not date_str or not slot:
        return jsonify({"status": "error", "message": "date and time_slot required"}), 400

    try:
        new_dt = datetime.strptime(f"{date_str} {slot}", "%Y-%m-%d %I:%M %p")
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid date/time format"}), 400

    if new_dt < now:
        return jsonify({"status": "error", "message": "Cannot reschedule to a past date"}), 400

    clash = Appointment.query.filter(
        Appointment.doctor_id            == apt.doctor_id,
        Appointment.appointment_datetime == new_dt,
        Appointment.status               == AppointmentStatus.BOOKED,
        Appointment.id                   != apt.id
    ).first()
    if clash:
        return jsonify({"status": "error", "message": "That slot is already taken"}), 409

    apt.appointment_datetime = new_dt
    apt.status = AppointmentStatus.BOOKED
    apt.mail_sent = False  # Allow new reminder emails
    db.session.commit()
    return jsonify({"status": "success", "message": "Appointment rescheduled"})


# ─────────────────────────────────────────
# API: FIND DOCTORS
# ─────────────────────────────────────────
@dashboard_bp.route("/api/doctors", methods=["GET"])
def find_doctors():
    """
    Search and filter utility for finding doctors by name, department, or specialization.
    """
    search  = request.args.get("search", "").strip()
    dept_id = request.args.get("department_id", type=int)
    spec    = request.args.get("specialization", "").strip()
    now     = datetime.now()

    query = Doctor.query
    if search:
        query = query.filter(Doctor.name.ilike(f"%{search}%"))
    if dept_id:
        query = query.filter_by(department_id=dept_id)
    if spec:
        query = query.filter(Doctor.specialization.ilike(f"%{spec}%"))

    result = []
    for doc in query.all():
        booked = Appointment.query.filter(
            Appointment.doctor_id            == doc.id,
            Appointment.status               == AppointmentStatus.BOOKED,
            Appointment.appointment_datetime >= now,
        ).count()

        status_raw = (doc.status or "").strip().lower()
        is_available = status_raw in {"available", "yes", "true", "1", "active"}

        result.append({
            "id":             doc.id,
            "name":           doc.name,
            "specialization": doc.specialization,
            "is_available":   is_available,
            "department":     doc.department.name if doc.department else None,
            "phone":          getattr(doc, "phone", None),
            "booked_slots":   booked,
        })

    return jsonify({"status": "success", "doctors": result})


# ─────────────────────────────────────────
# API: DOCTOR SLOTS
# ─────────────────────────────────────────
@dashboard_bp.route("/api/doctors/<int:doctor_id>/slots", methods=["GET"])
def doctor_slots(doctor_id):
    """
    Calculates available time slots for a doctor on a specific date, taking into
    account their schedule, existing bookings, and office hours.
    """
    date_str = request.args.get("date")
    if not date_str:
        return jsonify({"status": "error", "message": "date required"}), 400

    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid date"}), 400

    doc = Doctor.query.get(doctor_id)
    if not doc:
        return jsonify({"status": "error", "message": "Doctor not found"}), 404

    # Fixed clinical slots every 1 hour for daytime OPD.
    all_slots = [
        "9:00 AM","10:00 AM","11:00 AM","12:00 PM",
        "1:00 PM","2:00 PM","3:00 PM","4:00 PM",
        "5:00 PM","6:00 PM","7:00 PM","8:00 PM",
        "9:00 PM","10:00 PM","11:00 PM","12:00 AM"
    ]

    doctor_booked = {
        a.appointment_datetime.strftime("%I:%M %p").lstrip("0")
        for a in Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status    == AppointmentStatus.BOOKED,
            db.func.date(Appointment.appointment_datetime) == target.isoformat()
        ).all()
    }

    patient_booked = {
        a.appointment_datetime.strftime("%I:%M %p").lstrip("0")
        for a in Appointment.query.filter(
            Appointment.patient_id == g.user.id,
            Appointment.status     == AppointmentStatus.BOOKED,
            db.func.date(Appointment.appointment_datetime) == target.isoformat()
        ).all()
    }

    day_start = datetime.combine(target, datetime.min.time())
    day_end   = datetime.combine(target, datetime.max.time())
    daily_count = Appointment.query.filter(
        Appointment.patient_id           == g.user.id,
        Appointment.status               == AppointmentStatus.BOOKED,
        Appointment.appointment_datetime >= day_start,
        Appointment.appointment_datetime <= day_end
    ).count()

    daily_limit_reached = daily_count >= DAILY_BOOKING_LIMIT

    weekday = target.strftime("%A")
    schedules = DoctorSchedule.query.filter_by(doctor_id=doctor_id, day_of_week=weekday).all()
    has_schedule = len(schedules) > 0
    is_leave = any((s.work_type or "").strip().lower() == "leave" for s in schedules)

    # If no schedule exists, assume 09:00-17:00 working day.
    if has_schedule and not is_leave:
        windows = []
        for s in schedules:
            try:
                start_t = datetime.strptime((s.shift_start or "09:00").strip(), "%H:%M").time()
                end_t = datetime.strptime((s.shift_end or "17:00").strip(), "%H:%M").time()
                windows.append((start_t, end_t))
            except ValueError:
                windows.append((datetime.strptime("09:00", "%H:%M").time(), datetime.strptime("17:00", "%H:%M").time()))
    else:
        windows = [(datetime.strptime("09:00", "%H:%M").time(), datetime.strptime("17:00", "%H:%M").time())]

    lunch_start = datetime.strptime("13:00", "%H:%M").time()
    lunch_end = datetime.strptime("14:00", "%H:%M").time()
    now_local = datetime.now()

    result = []
    for s in all_slots:
        slot_time = datetime.strptime(s, "%I:%M %p").time()
        slot_dt = datetime.combine(target, slot_time)
        in_window = any(start_t <= slot_time < end_t for (start_t, end_t) in windows)
        is_lunch = lunch_start <= slot_time < lunch_end
        is_past_time = target == now_local.date() and slot_dt <= now_local

        if is_leave:
            reason = "doctor_off"
        elif not in_window:
            reason = "outside_schedule"
        elif is_lunch:
            reason = "lunch_break"
        elif is_past_time:
            reason = "past_time"
        elif daily_limit_reached:
            reason = "daily_limit"
        elif s in doctor_booked:
            reason = "doctor_taken"
        elif s in patient_booked:
            reason = "your_appointment"
        else:
            reason = None

        result.append({
            "slot":      s,
            "available": reason is None,
            "reason":    reason
        })

    return jsonify({
        "status":              "success",
        "slots":               result,
        "daily_count":         daily_count,
        "daily_limit":         DAILY_BOOKING_LIMIT,
        "daily_limit_reached": daily_limit_reached
    })


@dashboard_bp.route("/api/prescriptions", methods=["GET"])
def list_prescriptions():
    rows = (Prescription.query
            .filter_by(patient_id=g.user.id)
            .order_by(Prescription.prescribed_at.desc())
            .all())
    return jsonify({"status": "success", "prescriptions": [_serialize_prescription(p) for p in rows]})


@dashboard_bp.route("/api/prescriptions/<int:prescription_id>", methods=["GET"])
def get_prescription_detail(prescription_id):
    p = Prescription.query.filter_by(id=prescription_id, patient_id=g.user.id).first_or_404()
    return jsonify({"status": "success", "prescription": _serialize_prescription(p)})


# ─────────────────────────────────────────
# API: DOWNLOAD REPORT (text)
# ─────────────────────────────────────────
@dashboard_bp.route("/api/download_report")

def download_report():
    p    = g.user
    now  = datetime.now()
    apts = (Appointment.query
            .filter_by(patient_id=p.id)
            .order_by(Appointment.appointment_datetime.desc())
            .all())
    prescriptions = (Prescription.query
                     .filter_by(patient_id=p.id)
                     .order_by(Prescription.prescribed_at.desc())
                     .all())
    rx_data = [_serialize_prescription(rx) for rx in prescriptions]

    report_lines = _build_report_lines(p, apts, rx_data, now)
    out = io.StringIO()
    out.write("\n".join(report_lines) + "\n")

    response = Response(out.getvalue(), mimetype="text/plain")
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{p.name.replace(" ", "_")}_Medical_Report.txt"'
    )
    return response


# ─────────────────────────────────────────
# API: DOWNLOAD JSON
# ─────────────────────────────────────────
@dashboard_bp.route("/api/download_report_pdf")
def download_report_pdf():
    p    = g.user
    now  = datetime.now()
    apts = (Appointment.query
            .filter_by(patient_id=p.id)
            .order_by(Appointment.appointment_datetime.desc())
            .all())
    prescriptions = (Prescription.query
                     .filter_by(patient_id=p.id)
                     .order_by(Prescription.prescribed_at.desc())
                     .all())
    rx_data = [_serialize_prescription(rx) for rx in prescriptions]

    lines = _build_report_lines(p, apts, rx_data, now)

    pdf_bytes = _build_simple_pdf(lines)
    response = Response(pdf_bytes, mimetype="application/pdf")
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{p.name.replace(" ", "_")}_Medical_Report.pdf"'
    )
    return response


@dashboard_bp.route("/api/download_json")

def download_json():
    p    = g.user
    now  = datetime.now()
    apts = Appointment.query.filter_by(patient_id=p.id).all()

    payload = {
        "exported_at": now.isoformat(),
        "patient": {
            "patient_uid": p.patient_uid,
            "name":        p.name,
            "email":       p.email,
            "gender":      p.gender,
        },
        "summary": {
            "total":     len(apts),
            "upcoming":  sum(1 for a in apts if a.status == AppointmentStatus.BOOKED and a.appointment_datetime >= now),
            "completed": sum(1 for a in apts if a.status == AppointmentStatus.COMPLETED),
            "cancelled": sum(1 for a in apts if a.status == AppointmentStatus.CANCELLED),
        },
        "appointments": [
            {
                "date":   a.appointment_datetime.strftime("%Y-%m-%d") if a.appointment_datetime else None,
                "time":   a.appointment_datetime.strftime("%I:%M %p").lstrip("0") if a.appointment_datetime else None,
                "status": a.status,
                "doctor": a.doctor.name           if a.doctor else None,
                "dept":   a.doctor.department.name if a.doctor and a.doctor.department else None,
            }
            for a in apts
        ],
    }

    response = Response(json.dumps(payload, indent=2), mimetype="application/json")
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{p.name.replace(" ", "_")}_data.json"'
    )
    return response


# ─────────────────────────────────────────
# API: NOTIFICATIONS (Using Appointment table remarks)
# ─────────────────────────────────────────

@dashboard_bp.route("/api/notifications", methods=["GET"])
def get_notifications():
    """
    Returns email notification statuses derived from Appointment table remarks.
    """
    # We fetch appointments where an email attempt was made (remark exists)
    # AND the appointment has not yet passed.
    history = Appointment.query.filter(
        Appointment.patient_id == g.user.id,
        Appointment.remark.isnot(None),
        Appointment.appointment_datetime > datetime.now()
    ).order_by(Appointment.updated_at.desc()).limit(20).all()

    notifications = []
    for a in history:
        msg = a.remark or ""
        # Classification for frontend UI
        if "Successfully" in msg:
            ntype = "success"
            title = "Email Sent"
            appt_time = a.appointment_datetime.strftime('%I:%M %p') if a.appointment_datetime else "N/A"
            text  = f"Reminder mail is successfully sent to your registered mail id for your doctor appointment at {appt_time}"
        elif "No email provided" in msg or "invalid" in msg.lower():
            ntype = "invalid_email"
            title = "Invalid Email ID"
            text  = "We couldn't send your appointment reminder because your email ID is missing or invalid. Please update it."
        else:
            ntype = "failed"
            title = "Delivery Failed"
            text  = f"Failed to send reminder for appointment with Dr. {a.doctor.name if a.doctor else 'N/A'}. This might be due to a network issue."

        notifications.append({
            "id": a.id,
            "type": ntype,
            "title": title,
            "message": text,
            "time": a.updated_at.isoformat() + "Z" if a.updated_at else None,
            "appointment_id": a.id
        })

    return jsonify({
        "status": "success",
        "notifications": notifications
    })


@dashboard_bp.route("/api/profile/email", methods=["PUT"])
def update_email():
    """
    Allows the patient to update their email address.
    """
    d = request.get_json() or {}
    new_email = (d.get("email") or "").strip().lower()

    if not new_email:
        return jsonify({"status": "error", "message": "Email is required"}), 400

    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, new_email):
        return jsonify({"status": "error", "message": "Invalid email format"}), 400

    existing = Patient.query.filter(Patient.email == new_email, Patient.id != g.user.id).first()
    if existing:
        return jsonify({"status": "error", "message": "This email is already registered"}), 409

    g.user.email = new_email
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Email updated successfully"
    })



