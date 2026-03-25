from datetime import datetime
from extensions import db
from werkzeug.security import check_password_hash, generate_password_hash


class Admin(db.Model):
    """
    Dedicated Admin model — separate from the Patient table.
    Admins are hospital system administrators with full management access.
    """
    __tablename__ = "admins"

    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(100), nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role     = db.Column(db.String(20), default="admin")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)
