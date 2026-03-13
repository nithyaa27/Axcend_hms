from datetime import datetime
from extensions import db

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default="success")  # success, error_invalid_email, error_network
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", backref="notifications")

    def __repr__(self):
        return f"<Notification {self.id} for Patient {self.patient_id}>"
