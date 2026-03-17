from datetime import datetime, timedelta
from celery_app import celery_app
import os
import smtplib
from email.message import EmailMessage

# Instead of relative imports that might fail in worker context, 
# we use the app context to access models.
from extensions import db

def send_email(to_email, subject, body):
    # Using secrets from environment or defaults from app/email_utils
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
        
        print(f"[DEBUG] Checking reminders. Now={now}, Window={reminder_window}")
        
        # Find appointments that are booked, not yet notified, and upcoming soon
        appts = Appointment.query.filter(
            Appointment.status == AppointmentStatus.BOOKED,
            Appointment.mail_sent == False,
            Appointment.appointment_datetime <= reminder_window,
            Appointment.appointment_datetime >= now
        ).all()
        
        for appt in appts:
            patient = appt.patient
            if not patient or not patient.email:
                print(f"[WARNING] No email for patient in appointment {appt.id}")
                appt.mail_sent = True
                appt.remark = "Failed: No email provided"
                db.session.commit()
                continue
                
            subject = "Appointment Reminder"
            body = f"""
Hello {patient.name},

This is a friendly reminder that you have an upcoming appointment scheduled on 
{appt.appointment_datetime.strftime('%A, %B %d, %Y at %I:%M %p')}.

Please make sure to arrive a few minutes early. If you need to reschedule or have any questions, 
feel free to contact us.

Thank you,
HMS
            """
            
            try:
                send_email(patient.email, subject, body)
                appt.mail_sent = True
                appt.remark = "Successfully sent"
                db.session.commit()
                print(f"[INFO] Reminder sent for appt {appt.id} to {patient.email}")
            except Exception as e:
                db.session.rollback()
                appt.mail_sent = False
                appt.remark = f"Failed: {str(e)}"
                db.session.commit()
                print(f"[ERROR] Failed to process appt {appt.id}: {e}")

@celery_app.task(name="tasks.sync_appointment_statuses")
def sync_appointment_statuses():
    from app import app
    from models.appointment import Appointment, AppointmentStatus
    
    with app.app_context():
        now = datetime.now()
        # 1. Handle Missed Appointments (10 mins after slot)
        # Find BOOKED appointments that passed > 10 mins ago
        # Note: If status is VISITED, they have arrived, so we don't send missed mail.
        ten_mins_ago = now - timedelta(minutes=10)
        missed_apts = Appointment.query.filter(
            Appointment.status == AppointmentStatus.BOOKED,
            Appointment.appointment_datetime <= ten_mins_ago
        ).all()

        for apt in missed_apts:
            # Change status to NOT_ATTENDED so it's picked up by auto-cancel later
            # and won't be picked up by this loop again.
            apt.status = AppointmentStatus.NOT_ATTENDED
            if not apt.missed_mail_sent:
                patient = apt.patient
                doctor = apt.doctor
                if patient and patient.email:
                    time_str = apt.appointment_datetime.strftime('%I:%M %p')
                    subject = "Missed Appointment Notification"
                    body = f"""
Hello {patient.name},

You missed your scheduled appointment with Dr. {doctor.name if doctor else 'your doctor'} at {time_str}.

We missed you today! Please visit the dashboard to reschedule your appointment at your earliest convenience. 
Note: If you do not reschedule within 24 hours, the appointment will be cancelled.

If you have already visited or rescheduled, please ignore this message.

Thank you,
HMS Team
"""
                    try:
                        send_email(patient.email, subject, body)
                        apt.missed_mail_sent = True
                    except Exception as e:
                        print(f"[ERROR] Failed to send missed email for appt {apt.id}: {e}")

        # 2. Handle Auto-Cancellation (24 hours after missed)
        # Find NOT_ATTENDED appointments that passed > 24 hours ago
        one_day_ago = now - timedelta(hours=24)
        to_cancel_apts = Appointment.query.filter(
            Appointment.status == AppointmentStatus.NOT_ATTENDED,
            Appointment.appointment_datetime <= one_day_ago
        ).all()

        if to_cancel_apts:
            print(f"[INFO] Auto-cancelling {len(to_cancel_apts)} missed appointments.")
            for apt in to_cancel_apts:
                apt.status = AppointmentStatus.CANCELLED
                apt.remark = "Auto-cancelled: No reschedule within 24 hours after missing"
        
        try:
            db.session.commit()
            print(f"[INFO] Successfully synced appointment statuses.")
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Failed to sync appointment statuses: {e}")

# scheduler configuration (following HMS_Source pattern)
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
