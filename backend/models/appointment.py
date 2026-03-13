from datetime import datetime, timedelta
from utils.datetime_utils import local_now
from extensions import db   # ✅ fixed: was "from models import db"


class AppointmentStatus:
    BOOKED    = "booked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NOT_ATTENDED = "not_attended"
    NOT_VISITED = "not_visited"
    NOT_VISITED_CANCELLED = "not_visited_cancelled"


class Appointment(db.Model):

    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)

    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"),   nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)

    appointment_datetime = db.Column(db.DateTime, nullable=False)

    status = db.Column(db.String(32), nullable=False, default=AppointmentStatus.BOOKED)
    reminder_email_status = db.Column(db.String(50), nullable=True)
    reminder_email_kind = db.Column(db.String(20), nullable=True)
    reminder_email_message = db.Column(db.Text, nullable=True)
    reminder_email_sent_at = db.Column(db.DateTime, nullable=True)
    reminder_email_updated_at = db.Column(db.DateTime, nullable=True)
    reminder_email_read = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    doctor  = db.relationship("Doctor",  backref="appointments")
    patient = db.relationship("Patient", backref="appointments")

    def __repr__(self):
        return f"<Appointment {self.id}>"


def derive_persisted_appointment_status(appointment, now=None):
    now = now or local_now()
    dt = appointment.appointment_datetime
    status = appointment.status or AppointmentStatus.BOOKED

    if not dt:
        return status

    if status in {
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELLED,
    }:
        return status

    if dt >= now:
        return AppointmentStatus.BOOKED

    if dt.date() == now.date():
        return AppointmentStatus.NOT_ATTENDED

    elapsed = now - dt
    if elapsed >= timedelta(days=2):
        return AppointmentStatus.NOT_VISITED_CANCELLED

    return AppointmentStatus.NOT_VISITED
