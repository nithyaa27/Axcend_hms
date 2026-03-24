from datetime import datetime
from extensions import db


class AppointmentStatus:
    BOOKED    = "booked"
    ATTENDING = "attending"
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

    status = db.Column(db.String(50), nullable=False, default=AppointmentStatus.BOOKED)
    mail_sent = db.Column(db.Boolean, default=False)
    missed_mail_sent = db.Column(db.Boolean, default=False)
    remark = db.Column(db.String(255), nullable=True) # Successfully sent or failed

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    doctor  = db.relationship("Doctor",  backref="appointments")
    patient = db.relationship("Patient", backref="appointments")

    def __repr__(self):
        return f"<Appointment {self.id}>"

    def get_derived_status(self, now=None):
        from datetime import datetime, timedelta
        now = now or datetime.now()
        dt = self.appointment_datetime
        status = self.status

        # 1. If it's already a 'final' or 'processed' status, return it directly.
        # This keeps 'completed', 'cancelled', 'not_attended', etc. stable.
        if not dt or status != AppointmentStatus.BOOKED:
            return status

        # 2. Logic for currently 'booked' appointments
        elapsed = now - dt

        # If it's more than 24 hours past the appointment, it's auto-cancelled
        if elapsed >= timedelta(hours=24):
            return AppointmentStatus.CANCELLED

        # 10 minute grace period for the doctor to mark it as 'attending'
        # If it's more than 10 mins past the scheduled time and still 'booked', it's 'not_attended'
        if dt < now and elapsed > timedelta(minutes=10):
            return AppointmentStatus.NOT_ATTENDED

        # Otherwise (even if it's currently in that 10-min window), it's still 'booked'
        return AppointmentStatus.BOOKED