from datetime import datetime
from extensions import db


class AppointmentStatus:
    BOOKED    = "booked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NOT_ATTENDED = "not_attended"
    NOT_VISITED = "not_visited"
    NOT_VISITED_CANCELLED = "not_visited_cancelled"
    VISITED = "visited"


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

        # 1. Terminal statuses stay as they are
        if not dt or status in {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED, AppointmentStatus.NOT_VISITED_CANCELLED}:
            return status

        elapsed = now - dt

        # 2. If it's more than 24 hours past the appointment, it's auto-cancelled
        if elapsed >= timedelta(hours=24):
            return AppointmentStatus.CANCELLED

        # 3. If it's already updated by the background task, return that (unless 24h passed above)
        if status in {AppointmentStatus.NOT_ATTENDED, AppointmentStatus.NOT_VISITED}:
            return status

        # 4. If it's still marked as 'booked'
        if dt >= now:
            return AppointmentStatus.BOOKED

        # 5. It's in the past but less than 24 hours
        return AppointmentStatus.NOT_ATTENDED