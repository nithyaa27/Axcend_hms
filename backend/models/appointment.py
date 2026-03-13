from datetime import datetime
from extensions import db


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

    status = db.Column(db.String(50), nullable=False, default=AppointmentStatus.BOOKED)
    mail_sent = db.Column(db.Boolean, default=False)
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

        if not dt or status in {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED, AppointmentStatus.NOT_VISITED_CANCELLED}:
            return status

        # If it's already updated by the background task, return that
        if status in {AppointmentStatus.NOT_ATTENDED, AppointmentStatus.NOT_VISITED}:
            return status

        # Derive if still marked as 'booked'
        if dt >= now:
            return AppointmentStatus.BOOKED

        # Has passed
        if dt.date() == now.date():
            return AppointmentStatus.NOT_ATTENDED
        
        elapsed = now - dt
        if elapsed >= timedelta(days=2):
            return AppointmentStatus.NOT_VISITED_CANCELLED
        
        return AppointmentStatus.NOT_VISITED