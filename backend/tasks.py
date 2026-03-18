from datetime import datetime, timedelta
from celery_app import celery_app
import os
import smtplib
from email.message import EmailMessage
from extensions import db

def send_email(to_email, subject, body):
    # Using secrets from environment or defaults
    EMAIL_USER = os.environ.get("EMAIL_USER", "hmsproject26@gmail.com")
    EMAIL_PASS = os.environ.get("EMAIL_PASS", "lfynpsyxnqvjiypd")
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print(f"[INFO] Email sent to {to_email}")
    except Exception as e:
        print(f"[ERROR] Failed to send email to {to_email}: {e}")

@celery_app.task(name="tasks.send_appointment_reminders")
def send_appointment_reminders():
    from app import app
    from models.appointment import Appointment, AppointmentStatus
    
    with app.app_context():
        now = datetime.now()
        reminder_window = now + timedelta(minutes=45)
        
        
        appts = Appointment.query.filter(
            Appointment.status == AppointmentStatus.BOOKED,
            Appointment.mail_sent == False,
            Appointment.appointment_datetime <= reminder_window,
            Appointment.appointment_datetime >= now
        ).all()
        
        for appt in appts:
            patient = appt.patient
            if not patient or not patient.email:
                appt.mail_sent = True
                appt.remark = "Failed: No email provided"
                db.session.commit()
                continue
                
            subject = "Appointment Reminder – HMS"
            body = (
                f"Hello {patient.name},\n\n"
                f"This is a friendly reminder that you have an upcoming appointment scheduled on\n"
                f"{appt.appointment_datetime.strftime('%A, %B %d, %Y at %I:%M %p')}.\n\n"
                f"Please make sure to arrive a 15 minutes early. If you need to reschedule or have any questions,\n"
                f"feel free to contact us.\n\n"
                f"Thank you,\n"
                f"HMS"
            )
            
            try:
                send_email(patient.email, subject, body)
                appt.mail_sent = True
                appt.remark = "Successfully sent"
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                appt.mail_sent = False
                appt.remark = f"Failed: {str(e)}"
                db.session.commit()

@celery_app.task(name="tasks.sync_appointment_statuses")
def sync_appointment_statuses():
    from app import app
    from models.appointment import Appointment, AppointmentStatus
    
    with app.app_context():
        now = datetime.now()
        ten_mins_ago = now - timedelta(minutes=10)
        missed_apts = Appointment.query.filter(
            Appointment.status == AppointmentStatus.BOOKED,
            Appointment.appointment_datetime <= ten_mins_ago
        ).all()

        for apt in missed_apts:
            apt.status = AppointmentStatus.NOT_ATTENDED
            if not apt.missed_mail_sent:
                patient = apt.patient
                if patient and patient.email:
                    try:
                        doctor_name = apt.doctor.name if apt.doctor else "your doctor"
                        appt_time = apt.appointment_datetime.strftime("%I:%M %p")
                        missed_subject = "Missed Appointment Notification – HMS"
                        missed_body = (
                            f"Hello {patient.name},\n\n"
                            f"You missed your scheduled appointment with Dr. {doctor_name} at {appt_time}.\n\n"
                            f"We missed you today! Please visit the dashboard to reschedule your appointment at your earliest convenience.\n"
                            f"Note: If you do not reschedule within 24 hours, the appointment will be cancelled.\n\n"
                            f"If you have already visited or rescheduled, please ignore this message.\n\n"
                            f"Thank you,\n"
                            f"HMS Team"
                        )
                        send_email(patient.email, missed_subject, missed_body)
                        apt.missed_mail_sent = True
                    except Exception: pass

        one_day_ago = now - timedelta(hours=24)
        to_cancel_apts = Appointment.query.filter(
            Appointment.status == AppointmentStatus.NOT_ATTENDED,
            Appointment.appointment_datetime <= one_day_ago
        ).all()

        for apt in to_cancel_apts:
            apt.status = AppointmentStatus.CANCELLED
            apt.remark = "Auto-cancelled: No reschedule within 24 hours"
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()

# scheduler configuration
celery_app.conf.beat_schedule = {
    "check-appointments-every-30-seconds": {
        "task": "tasks.send_appointment_reminders",
        "schedule": 30.0,
    },
    "sync-appointment-statuses-every-minute": {
        "task": "tasks.sync_appointment_statuses",
        "schedule": 60.0,
    },
}

