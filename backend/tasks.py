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

    # We do NOT catch the exception here, so the caller knows if it failed
    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
    print(f"[INFO] Email successfully relay to {to_email}")

@celery_app.task(name="tasks.send_appointment_reminders")
def send_appointment_reminders():
    from app import app
    from models.appointment import Appointment, AppointmentStatus
    from models.models import ReminderSettings
    from utils.reminder_utils import get_or_create_reminder_settings, month_period
    
    with app.app_context():
        now = datetime.now()
        settings = get_or_create_reminder_settings()
        currentTime = now.strftime("%H:%M")
        
        # ─── DAILY REMINDER DISPATCH ─────────────────────────────────────────
        if settings.daily_enabled:
            is_new_day = (settings.last_daily_sent_on is None or settings.last_daily_sent_on < now.date())
            if is_new_day and currentTime >= settings.daily_time:
                # Mark as dispatching today to avoid race/overlap
                settings.last_daily_sent_on = now.date()
                db.session.commit()
                
                # Fetch all Booked appointments for TODAY
                today_start = datetime.combine(now.date(), datetime.min.time())
                today_end = datetime.combine(now.date(), datetime.max.time())
                
                appts = Appointment.query.filter(
                    Appointment.status == AppointmentStatus.BOOKED,
                    Appointment.appointment_datetime >= today_start,
                    Appointment.appointment_datetime <= today_end
                ).all()
                
                for appt in appts:
                    patient = appt.patient
                    if not patient or not patient.email:
                        appt.mail_sent = True
                        appt.remark = "Skipped: No email provided"
                        db.session.commit()
                        continue
                        
                    subject = "Today's Appointment Reminder – HMS"
                    body = (
                        f"Hello {patient.name},\n\n"
                        f"This is a friendly reminder of your appointment today, "
                        f"{appt.appointment_datetime.strftime('%B %d, %Y at %I:%M %p')}.\n\n"
                        f"Please arrive at least 15 minutes early.\n\n"
                        f"Thank you,\nHMS Admin"
                    )
                    
                    try:
                        send_email(patient.email, subject, body)
                        appt.mail_sent = True
                        appt.remark = "Successfully sent (Daily)"
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        appt.mail_sent = False
                        appt.remark = f"Failed: {str(e)}"
                        db.session.commit()

        # ─── MONTHLY REMINDER DISPATCH ───────────────────────────────────────
        if settings.monthly_enabled:
            curr_period = month_period(now)
            is_new_period = (settings.last_monthly_sent_period != curr_period)
            is_target_day = (now.day == (settings.monthly_day or 1))
            
            if is_new_period and is_target_day and currentTime >= settings.monthly_time:
                settings.last_monthly_sent_period = curr_period
                db.session.commit()
                
                # Find all patients with appointments booked for THIS MONTH
                month_end = (now.date().replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                month_end_dt = datetime.combine(month_end, datetime.max.time())
                
                appts = Appointment.query.filter(
                    Appointment.status == AppointmentStatus.BOOKED,
                    Appointment.appointment_datetime >= now,
                    Appointment.appointment_datetime <= month_end_dt
                ).all()
                
                # We group by patient to avoid spamming multiple monthly mails if they have multiple appts
                notified_patients = set()
                
                for appt in appts:
                    patient = appt.patient
                    if not patient or not patient.email or patient.id in notified_patients:
                        continue
                        
                    subject = "Monthly Health Schedule Overview – HMS"
                    body = (
                        f"Hello {patient.name},\n\n"
                        f"This is your monthly schedule overview for {now.strftime('%B %Y')}.\n"
                        f"You have upcoming appointments at our facility. Please check your dashboard for details.\n\n"
                        f"Stay healthy!\nHMS Team"
                    )
                    
                    try:
                        send_email(patient.email, subject, body)
                        notified_patients.add(patient.id)
                    except Exception: 
                        pass # Monthly is secondary, don't break the loop

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
    "check-appointments-every-5-seconds": {
        "task": "tasks.send_appointment_reminders",
        "schedule": 5.0,
    },
    "sync-appointment-statuses-every-minute": {
        "task": "tasks.sync_appointment_statuses",
        "schedule": 60.0,
    },
}

