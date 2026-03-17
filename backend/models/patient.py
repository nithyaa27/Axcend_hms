from datetime import datetime
from extensions import db
from werkzeug.security import check_password_hash

class Patient(db.Model):

    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    patient_uid = db.Column(db.String(10), unique=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10), nullable=False)
    role = db.Column(db.String(20), default="patient")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def check_password(self, password):
        return check_password_hash(self.password, password)
