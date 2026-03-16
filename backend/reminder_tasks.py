from calendar import monthrange
from datetime import datetime, time, timedelta

from extensions import db
from models.appointment import Appointment, AppointmentStatus
from models.models import PatientReminder
from models.patient import Patient
from utils.email_utils import send_patient_reminder_email
from utils.reminder_utils import get_or_create_reminder_settings, month_period

MIN_DAILY_REMINDER_LEAD_MINUTES = 30


def _combine_today(clock_value):
    hour, minute = [int(part) for part in clock_value.split(":", 1)]
    now = datetime.now()
    return datetime.combine(now.date(), time(hour=hour, minute=minute))


def _time_reached(clock_value, now=None):
    current = now or datetime.now()
    target = _combine_today(clock_value)
    return current >= target


def _create_patient_reminder(patient_id, reminder_type, title, message, scheduled_for, appointment_id=None):
    existing = PatientReminder.query.filter_by(
        patient_id=patient_id,
        reminder_type=reminder_type,
        scheduled_for=scheduled_for,
        related_appointment_id=appointment_id,
    ).first()
    if existing:
        return False

    reminder = PatientReminder(
        patient_id=patient_id,
        reminder_type=reminder_type,
        title=title,
        message=message,
        scheduled_for=scheduled_for,
        related_appointment_id=appointment_id,
    )
    db.session.add(reminder)
    return True


def _has_daily_reminder_for_appointment(patient_id, appointment_id, target_date):
    existing = PatientReminder.query.filter(
        PatientReminder.patient_id == patient_id,
        PatientReminder.reminder_type == "daily",
        PatientReminder.related_appointment_id == appointment_id,
        db.func.date(PatientReminder.scheduled_for) == target_date.isoformat(),
    ).first()
    return existing is not None


def _send_daily_reminders(settings):
    now = datetime.now()
    today = now.date()
    scheduled_for = _combine_today(settings.daily_time)
    reminder_cutoff = now + timedelta(minutes=MIN_DAILY_REMINDER_LEAD_MINUTES)
    appointments = (
        Appointment.query
        .filter(
            db.func.date(Appointment.appointment_datetime) == today.isoformat(),
            Appointment.status == AppointmentStatus.BOOKED,
            Appointment.appointment_datetime >= reminder_cutoff,
        )
        .all()
    )

    sent_count = 0
    for appointment in appointments:
        patient = appointment.patient
        doctor = appointment.doctor
        if not patient:
            continue

        message = (
            f"Reminder: you have an appointment today with "
            f"{doctor.name if doctor else 'your doctor'} at "
            f"{appointment.appointment_datetime.strftime('%I:%M %p').lstrip('0')}."
        )
        if _has_daily_reminder_for_appointment(patient.id, appointment.id, today):
            continue

        created = _create_patient_reminder(
            patient.id,
            "daily",
            "Today's Appointment Reminder",
            message,
            scheduled_for,
            appointment.id,
        )
        if created:
            sent_count += 1
            if patient.email:
                send_patient_reminder_email(patient.email, "HMS Appointment Reminder", message)

    settings.last_daily_sent_on = today
    db.session.commit()
    return sent_count


def _send_monthly_reminders(settings):
    current = datetime.now()
    current_period = month_period(current)
    if settings.last_monthly_sent_period == current_period:
        return 0

    last_day = monthrange(current.year, current.month)[1]
    effective_day = min(settings.monthly_day, last_day)
    scheduled_for = datetime(
        current.year,
        current.month,
        effective_day,
        int(settings.monthly_time.split(":")[0]),
        int(settings.monthly_time.split(":")[1]),
    )

    patients = Patient.query.filter_by(role="patient").all()
    sent_count = 0
    for patient in patients:
        message = (
            "Monthly reminder: please review your appointments, prescriptions, "
            "and follow-up care in the HMS patient dashboard."
        )
        created = _create_patient_reminder(
            patient.id,
            "monthly",
            "Monthly Health Reminder",
            message,
            scheduled_for,
        )
        if created:
            sent_count += 1
            if patient.email:
                send_patient_reminder_email(patient.email, "HMS Monthly Reminder", message)

    settings.last_monthly_sent_period = current_period
    db.session.commit()
    return sent_count


def run_scheduled_reminders():
    settings = get_or_create_reminder_settings()
    now = datetime.now()
    results = {"daily": 0, "monthly": 0}

    if settings.daily_enabled and _time_reached(settings.daily_time, now):
        results["daily"] = _send_daily_reminders(settings)

    last_day = monthrange(now.year, now.month)[1]
    effective_day = min(settings.monthly_day, last_day)
    if settings.monthly_enabled and now.day == effective_day and _time_reached(settings.monthly_time, now):
        results["monthly"] = _send_monthly_reminders(settings)

    return results
