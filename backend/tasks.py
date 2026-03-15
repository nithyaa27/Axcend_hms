import os
import smtplib
import sys
from pathlib import Path
import importlib.util
from email.message import EmailMessage
import io
from datetime import datetime, timedelta

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from celery_app import celery_app
from extensions import db
from utils.datetime_utils import local_now

# Email Configuration
# The prompt provided: "take sender gmail for celery work as hmsproject26@gmail.com and password default empty"
# Note that Google SMTP does not work with empty passwords, it requires an App Password.
SMTP_HOST = os.environ.get("HMS_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("HMS_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("HMS_SMTP_USER", "hmsproject26@gmail.com")
SMTP_PASSWORD = os.environ.get("HMS_SMTP_APP_PASSWORD", "")  # Unified password env var

EMAIL_NOTIFICATION_TYPES = {"success", "error_invalid_email", "error_network"}
EMAIL_IN_FLIGHT_TYPES = {"queued", "sending"}

def get_flask_app():
    """Helper to get Flask app context for Celery tasks"""
    try:
        from app import app
        return app
    except ModuleNotFoundError:
        app_path = Path(__file__).resolve().with_name("app.py")
        app_dir = str(app_path.parent)
        if app_dir not in sys.path:
            sys.path.insert(0, app_dir)

        spec = importlib.util.spec_from_file_location("app", app_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load Flask app from {app_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.app

def send_email(to_email, subject, body, attachment_name=None, attachment_data=None):
    if not SMTP_PASSWORD:
        print(f"[ERROR] Cannot send email to {to_email}: SMTP_PASSWORD is empty.")
        return False, "error_network"
        
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.set_content(body)

    if attachment_name and attachment_data:
        msg.add_attachment(
            attachment_data,
            maintype="application",
            subtype="pdf",
            filename=attachment_name
        )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
<<<<<<< Updated upstream
        print(f"[INFO] Email sent successfully to {to_email}")
        return True, "success"
    except smtplib.SMTPRecipientsRefused:
        print(f"[ERROR] Invalid email address: {to_email}")
        return False, "error_invalid_email"
    except Exception as exc:
        print(f"[ERROR] Failed to send email to {to_email}: {exc}")
        return False, "error_network"
=======
        print(f"[INFO] Email sent to {to_email}")
    except Exception as e:
        print(f"[ERROR] Failed to send email to {to_email}: {e}")
        raise
>>>>>>> Stashed changes


def update_appointment_reminder_status(appointment, message, status_type, reminder_kind=None):
    appointment.reminder_email_status = (
        status_type if status_type in EMAIL_NOTIFICATION_TYPES else "error_network"
    )
    if reminder_kind is not None:
        appointment.reminder_email_kind = reminder_kind
    appointment.reminder_email_message = message
    appointment.reminder_email_sent_at = local_now()
    appointment.reminder_email_updated_at = local_now()
    appointment.reminder_email_read = False
    db.session.commit()


def mark_appointment_reminder_queued(appointment, reminder_kind):
    appointment.reminder_email_status = "queued"
    appointment.reminder_email_kind = reminder_kind
    appointment.reminder_email_message = "Reminder queued for delivery."
    appointment.reminder_email_updated_at = local_now()
    appointment.reminder_email_read = False


def reminder_already_processed(appointment, reminder_kind):
    if appointment.reminder_email_kind != reminder_kind:
        return False

    return appointment.reminder_email_status in (EMAIL_NOTIFICATION_TYPES | EMAIL_IN_FLIGHT_TYPES)


def sync_appointment_status_if_needed(appointment, now):
    from models.appointment import derive_persisted_appointment_status

    new_status = derive_persisted_appointment_status(appointment, now)
    if appointment.status != new_status:
        appointment.status = new_status
        return True
    return False


def reminder_can_be_sent(appointment, reminder_kind, now):
    sync_appointment_status_if_needed(appointment, now)
    if appointment.status != "booked":
        return False

    if reminder_kind == "pre_appointment":
        if not appointment.appointment_datetime:
            return False
        reminder_window_end = now + timedelta(minutes=15)
        return now < appointment.appointment_datetime <= reminder_window_end

    if reminder_kind == "today":
        return appointment.appointment_datetime and appointment.appointment_datetime > now

    return True


def build_patient_reminder_message(patient_name, doctor_name, appointment_datetime, reminder_kind):
    if reminder_kind == "pre_appointment":
        subject = "Appointment Reminder: In 15 Minutes"
        body = (
            f"Hello {patient_name}, this is a reminder for your appointment in 15 minutes "
            f"with Dr. {doctor_name} at {appointment_datetime.strftime('%I:%M %p')}."
        )
    else:
        when_label = "tomorrow" if reminder_kind == "tomorrow" else "today"
        subject = f"Appointment Reminder: {'Tomorrow' if reminder_kind == 'tomorrow' else 'Today'}!"
        body = (
            f"Hello {patient_name}, this is a reminder for your appointment {when_label} "
            f"with {doctor_name} at {appointment_datetime.strftime('%I:%M %p')}."
        )
    return subject, body


@celery_app.task(name="tasks.sync_appointment_statuses_task")
def sync_appointment_statuses_task():
    flask_app = get_flask_app()
    with flask_app.app_context():
        from models.appointment import Appointment, derive_persisted_appointment_status

        appointments = Appointment.query.all()
        now = local_now()
        changed = 0

        for appointment in appointments:
            if sync_appointment_status_if_needed(appointment, now):
                changed += 1

        if changed:
            db.session.commit()

        return f"Synchronized {changed} appointment statuses."


@celery_app.task(
    bind=True,
    name="tasks.send_patient_reminder_email_task",
    autoretry_for=(RuntimeError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def send_patient_reminder_email_task(self, appointment_id, reminder_kind):
    flask_app = get_flask_app()
    with flask_app.app_context():
        from models.appointment import Appointment
        from models.patient import Patient
        from models.models import Doctor

        appt = Appointment.query.get(appointment_id)
        now = local_now()

        if not appt:
            return f"Skipped appointment {appointment_id}: no longer eligible."

        status_changed = sync_appointment_status_if_needed(appt, now)
        if status_changed:
            db.session.commit()

        if not reminder_can_be_sent(appt, reminder_kind, now):
            return f"Skipped appointment {appointment_id}: no longer eligible."

        if reminder_already_processed(appt, reminder_kind) and appt.reminder_email_status != "queued":
            return f"Skipped appointment {appointment_id}: reminder already processed for {reminder_kind}."

        appt.reminder_email_status = "sending"
        appt.reminder_email_kind = reminder_kind
        appt.reminder_email_message = "Reminder is being sent."
        appt.reminder_email_updated_at = local_now()
        db.session.commit()

        patient = Patient.query.get(appt.patient_id)
        doctor = Doctor.query.get(appt.doctor_id)

        if not patient or not patient.email:
            return f"Skipped appointment {appointment_id}: patient email missing."

        doctor_name = doctor.name if doctor else "Doctor"
        subject, body = build_patient_reminder_message(
            patient.name,
            doctor_name,
            appt.appointment_datetime,
            reminder_kind
        )

        success, status_type = send_email(patient.email, subject, body)

        if status_type == "error_network" and self.request.retries < self.max_retries:
            raise RuntimeError(f"Temporary email delivery failure for appointment {appointment_id}")

        if status_type == "success":
            msg_content = (
                f"Your appointment reminder was sent to {patient.email}. "
                f"Please check your email."
            )
        elif status_type == "error_invalid_email":
            msg_content = (
                f"We could not send your appointment reminder to {patient.email}. "
                f"Please update your email address to keep receiving reminders."
            )
        else:
            msg_content = (
                f"We could not deliver your appointment reminder to {patient.email} due to an email service issue. "
                f"Please check again later."
            )

        update_appointment_reminder_status(appt, msg_content, status_type, reminder_kind=reminder_kind)
        return f"Reminder processed for appointment {appointment_id} with status {status_type}."

@celery_app.task(name="tasks.send_patient_reminders_task")
def send_patient_reminders_task():
    flask_app = get_flask_app()
    with flask_app.app_context():
        from models.appointment import Appointment
        from models.patient import Patient
        from models.models import Doctor

        now = local_now()
        tomorrow_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow_start + timedelta(days=1)

        print(f"[INFO] Running patient reminders task for appointments between {tomorrow_start} and {tomorrow_end}")

        appointments = Appointment.query.filter(
            Appointment.appointment_datetime >= tomorrow_start,
            Appointment.appointment_datetime < tomorrow_end,
            Appointment.status == "booked"
        ).all()

        count = 0
        changed = False
        for appt in appointments:
            if sync_appointment_status_if_needed(appt, now):
                changed = True
            if not reminder_can_be_sent(appt, "tomorrow", now):
                continue
            if reminder_already_processed(appt, "tomorrow"):
                continue
            patient = Patient.query.get(appt.patient_id)
            if patient and patient.email:
                mark_appointment_reminder_queued(appt, "tomorrow")
                changed = True
                send_patient_reminder_email_task.delay(appt.id, "tomorrow")
                count += 1
        if changed:
            db.session.commit()

        return f"Queued reminder emails for {count} patients."

@celery_app.task(name="tasks.send_today_reminders_task")
def send_today_reminders_task():
    """Send one reminder during the 15-minute pre-appointment window."""
    flask_app = get_flask_app()
    with flask_app.app_context():
        from models.appointment import Appointment
        from models.patient import Patient
        from models.models import Doctor

        now = local_now()
        reminder_window_end = now + timedelta(minutes=15)

        print(f"[INFO] Running pre-appointment reminder task for appointments between {now} and {reminder_window_end}")

        appointments = Appointment.query.filter(
            Appointment.appointment_datetime > now,
            Appointment.appointment_datetime <= reminder_window_end,
            Appointment.status == "booked"
        ).all()

        count = 0
        changed = False
        for appt in appointments:
            if sync_appointment_status_if_needed(appt, now):
                changed = True
            if not reminder_can_be_sent(appt, "pre_appointment", now):
                continue
            if reminder_already_processed(appt, "pre_appointment"):
                continue
            patient = Patient.query.get(appt.patient_id)
            if patient and patient.email:
                mark_appointment_reminder_queued(appt, "pre_appointment")
                changed = True
                send_patient_reminder_email_task.delay(appt.id, "pre_appointment")
                count += 1
        if changed:
            db.session.commit()

        return f"Queued pre-appointment reminder emails for {count} patients."

def generate_doctor_schedule_pdf(doctor_name, date_str, appointments_data):
    """Generates a PDF using reportlab containing the schedule."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title = Paragraph(f"Schedule for Dr. {doctor_name}", styles['Title'])
    subtitle = Paragraph(f"Date: {date_str}", styles['Heading2'])
    
    elements.extend([title, Spacer(1, 12), subtitle, Spacer(1, 12)])
    
    if not appointments_data:
        elements.append(Paragraph("No appointments scheduled for this day.", styles['Normal']))
    else:
        # Table data
        data = [["Time", "Patient Name", "Status"]]
        for appt in appointments_data:
            data.append([
                appt["time"],
                appt["patient_name"],
                appt["status"]
            ])
            
        table = Table(data, colWidths=[100, 250, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)
        
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
    

@celery_app.task(name="tasks.send_doctor_schedules_task")
def send_doctor_schedules_task():
    flask_app = get_flask_app()
    with flask_app.app_context():
        from models.appointment import Appointment
        from models.patient import Patient
        from models.models import Doctor

        now = local_now()
        tomorrow_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow_start + timedelta(days=1)
        date_str = tomorrow_start.strftime('%B %d, %Y')

        print(f"[INFO] Running doctor schedule task for {date_str}")

        doctors = Doctor.query.all()
        count = 0

        for doctor in doctors:
            if not doctor.email:
                continue

            appointments = Appointment.query.filter(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_datetime >= tomorrow_start,
                Appointment.appointment_datetime < tomorrow_end
            ).order_by(Appointment.appointment_datetime).all()
            
            # Even if there are no appointments, we might want to let the doctor know?
            # For now, let's only send if there are appointments or send an empty schedule if requested.
            if not appointments:
                continue

            appt_data = []
            for appt in appointments:
                patient = Patient.query.get(appt.patient_id)
                patient_name = patient.name if patient else "Unknown"
                
                appt_data.append({
                    "time": appt.appointment_datetime.strftime('%I:%M %p'),
                    "patient_name": patient_name,
                    "status": appt.status.capitalize()
                })
            
            pdf_bytes = generate_doctor_schedule_pdf(doctor.name, date_str, appt_data)
            
            subject = f"Your Schedule for Tomorrow ({date_str})"
            body = f"Hello Dr. {doctor.name},\n\nPlease find attached your appointment schedule for tomorrow.\n\nBest regards,\nHospital Management System"
            attachment_name = f"schedule_{date_str.replace(' ', '_').replace(',', '')}.pdf"
            
            success = send_email(doctor.email, subject, body, attachment_name, pdf_bytes)
            if success:
                count += 1
                
        return f"Sent schedules to {count} doctors."

