import sys
import os
sys.path.append(os.getcwd())

from app import app
from extensions import db
from models.appointment import Appointment
from models.patient import Patient
from models.models import Doctor
from tasks import send_today_reminders_task
from datetime import datetime, timedelta

def run_test():
    with app.app_context():
        # Check if there's a patient and doctor
        patient = Patient.query.first()
        doctor = Doctor.query.first()
        
        if not patient or not doctor:
            print("No patient or doctor found. Seeding required.")
            return

        # Ensure there is an appointment for today
        today = datetime.now()
        appt = Appointment.query.filter(
            Appointment.appointment_datetime >= today.replace(hour=0, minute=0, second=0, microsecond=0),
            Appointment.appointment_datetime < today.replace(hour=23, minute=59, second=59)
        ).first()
        
        if not appt:
            print("No appointment today. Creating one for testing...")
            appt = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                appointment_datetime=today + timedelta(minutes=5),
                status="booked"
            )
            db.session.add(appt)
            db.session.commit()
            print(f"Created appointment for {patient.name} at {appt.appointment_datetime}")

        print("Triggering send_today_reminders_task...")
        result = send_today_reminders_task()
        print(f"Task result: {result}")

if __name__ == "__main__":
    run_test()
