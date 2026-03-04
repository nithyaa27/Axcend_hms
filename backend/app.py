from flask import Flask
from flask_cors import CORS
from extensions import db
from models import User
from routes.auth import auth_bp
from werkzeug.security import generate_password_hash
from flask_jwt_extended import JWTManager
import os

app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "http://localhost:8080"}},
    supports_credentials=True
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

#  Hardcoded Configuration
app.config["SECRET_KEY"] = "this_should_be_at_least_32_characters_long"
app.config["JWT_SECRET_KEY"] = "this_should_be_at_least_32_characters_long"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "hms.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

jwt = JWTManager(app)  #  Initialize JWT

db.init_app(app)
app.register_blueprint(auth_bp, url_prefix="/auth")

# Create tables and default users
with app.app_context():
    db.create_all()

    admin = User.query.filter_by(email="admin@gmail.com").first()
    if not admin:
        admin = User(
            name="Admin",
            email="admin@gmail.com",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()

    doctor = User.query.filter_by(email="doctor@gmail.com").first()
    if not doctor:
        doctor = User(
            name="Dr. John",
            email="doctor@gmail.com",
            password=generate_password_hash("doctor123"),
            role="doctor"
        )
        db.session.add(doctor)
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
