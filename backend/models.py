from extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default="patient")
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    reset_token = db.Column(db.String(200))
    reset_token_expiry = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
