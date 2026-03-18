import os
import re
import smtplib
from email.message import EmailMessage
from datetime import datetime
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from itsdangerous import BadSignature, SignatureExpired
from werkzeug.security import check_password_hash, generate_password_hash

from sqlalchemy import text
from extensions import db
from routes.admin_routes import admin_bp
from routes.dashboard_routes import dashboard_bp
from routes.doctor_routes import doctor_bp
from utils.network_utils import get_actual_frontend_url
from utils.token_utils import create_jwt_token, decode_jwt_token, get_serializer

# ==========================================
# Flask Application Setup & Configuration
# ==========================================

app = Flask(__name__)

# Database Configuration
# We use a purely local SQLite database stored in the 'instance' folder.
basedir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(basedir, "instance")
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir, exist_ok=True)

db_path = os.path.join(instance_dir, "hms.db")
db_uri = f"sqlite:///{db_path}"

app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config["SECRET_KEY"] = os.getenv("HMS_SECRET_KEY", "dev-secret-key")

# Extensions
db.init_app(app)

CORS(
    app,
    resources={
        r"/auth/*": {"origins": re.compile(r".*")},
        r"/api/*":  {"origins": re.compile(r".*")},
    },
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    supports_credentials=True
)

# Global user logic for the request
@app.before_request
def load_user_from_token():
    """
    Middleware to extract the JWT token from the Authorization header,
    decode it, and load the corresponding user (Patient or Doctor) into the Flask global object `g`.
    This allows subsequent route handlers to access the current user via `g.user`.
    """
    # Skip CORS preflight
    if request.method == "OPTIONS":
        return "", 200
    
    g.user = None
    g.auth_error = None
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return

    token = auth_header.split(" ")[1]
    payload, err = decode_jwt_token(token)
    
    if err:
        g.auth_error = err
        return

    if payload:
        user_id = payload.get("user_id")
        role = payload.get("role")

        if role == "doctor":
            from models.models import Doctor
            g.user = db.session.get(Doctor, user_id)
        else:
            from models.patient import Patient
            g.user = db.session.get(Patient, user_id)


ROLE_DASHBOARD_PATHS = {
    "patient": "/patient",
    "doctor": "/doctor",
    "admin": "/admin",
}

DEFAULT_ADMIN = {
    "email": "admin@gmail.com",
    "password": "Admin@123",
    "role": "admin",
    "name": "Admin",
    "gender": "Not Specified",
}

def _send_reset_email(recipient_email, reset_link):
    """
    Sends a password reset email using SMTP.
    Configures the connection based on environment variables.
    """
    smtp_host = os.getenv("HMS_SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("HMS_SMTP_PORT", "587"))
    smtp_user = os.getenv("HMS_SMTP_USER", "hmsproject26@gmail.com")
    smtp_password = os.getenv("HMS_SMTP_APP_PASSWORD", "lfynpsyxnqvjiypd")

    if not smtp_password:
        return False, "SMTP app password is not configured"

    msg = EmailMessage()
    msg["Subject"] = "HMS Password Reset Request"
    msg["From"] = smtp_user
    msg["To"] = recipient_email
    msg.set_content(
        "You requested to reset your HMS password.\n\n"
        f"Use this link to reset your password: {reset_link}\n\n"
        "This link expires in 1 hour."
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        return True, None
    except Exception as exc:
        return False, str(exc)

def _validate_password(password):
    """
    Validates a password against security requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character"
    return None

def _validate_name(name):
    """
    Validates that the name is at least 3 characters long and contains only letters.
    """
    clean_name = (name or "").strip()
    if len(clean_name) < 3:
        return "Name must be at least 3 characters long"
    if not clean_name.replace(" ", "").isalpha():
        return "Name should contain only letters"
    return None

def _validate_email(email):
    # Basic email pattern validation
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return "Please enter a valid email address"
    return None

def _next_patient_uid():
    """
    Generates a unique patient UID (e.g., P0001, P0002).
    Always uses MAX(patient_uid) + 1 so it is safe:
    - On a fresh / empty database  → starts at P0001
    - After records are deleted    → never reuses an old UID
    """
    from models.patient import Patient
    from sqlalchemy import func
    max_uid = db.session.query(func.max(Patient.patient_uid)).scalar()
    if max_uid and len(max_uid) > 1 and max_uid[1:].isdigit():
        next_num = int(max_uid[1:]) + 1
    else:
        next_num = 1          # fresh / empty database
    return f"P{next_num:04d}"

def _ensure_default_admin():
    """
    Ensures that a default administrator account exists in the database.
    This runs every time the application starts.
    """
    from models.patient import Patient

    email = DEFAULT_ADMIN["email"].strip().lower()
    admin_user = Patient.query.filter_by(email=email).first()

    if not admin_user:
        admin_user = Patient(
            name=DEFAULT_ADMIN["name"],
            email=email,
            password=generate_password_hash(DEFAULT_ADMIN["password"]),
            gender=DEFAULT_ADMIN["gender"],
            patient_uid=_next_patient_uid(),
            role=DEFAULT_ADMIN["role"],
        )
        db.session.add(admin_user)
        db.session.commit()
        return

    admin_user.name = DEFAULT_ADMIN["name"]
    admin_user.password = generate_password_hash(DEFAULT_ADMIN["password"])
    admin_user.role = DEFAULT_ADMIN["role"]
    admin_user.gender = admin_user.gender or DEFAULT_ADMIN["gender"]
    admin_user.patient_uid = admin_user.patient_uid or _next_patient_uid()
    db.session.commit()

def _build_login_response(user):
    """
    Helper to construct a standard JSON response for successful authentication,
    including a JWT token and redirect path based on user role.
    """
    role = getattr(user, "role", "patient") or "patient"
    token = create_jwt_token(user.id, user.email, role)
    
    response = {
        "status": "success",
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": role,
        "token": token,
        "redirect_to": ROLE_DASHBOARD_PATHS.get(role, "/patient"),
    }
    
    if role == "doctor":
        response["doctor_id"] = user.id
        
    return response

@app.route("/api/register", methods=["POST"])
@app.route("/auth/register", methods=["POST"])
def register():
    """
    Endpoint for patient registration. 
    Validates input and creates a new Patient record in the database.
    """
    data = request.get_json() or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    age = data.get("age")
    password = data.get("password") or ""
    gender = (data.get("gender") or "Not Specified").strip() or "Not Specified"

    if not name or not email or not password:
        return jsonify({"message": "All required fields are mandatory"}), 400

    name_error = _validate_name(name)
    if name_error:
        return jsonify({"message": name_error}), 400

    email_error = _validate_email(email)
    if email_error:
        return jsonify({"message": email_error}), 400

    pass_error = _validate_password(password)
    if pass_error:
        return jsonify({"message": pass_error}), 400

    if phone:
        if not phone.isdigit():
            return jsonify({"message": "Phone number must contain only digits"}), 400
        if len(phone) != 10:
            return jsonify({"message": "Phone number must be 10 digits"}), 400

    age_value = None
    if age is not None and str(age).strip() != "":
        try:
            age_value = int(age)
            if age_value < 1 or age_value > 120:
                return jsonify({"message": "Age must be between 1 and 120"}), 400
        except (TypeError, ValueError):
            return jsonify({"message": "Age must be numeric"}), 400

    from models.patient import Patient
    existing = Patient.query.filter_by(email=email).first()
    if existing:
        return jsonify({"message": "Email already registered"}), 400

    user = Patient(
        name=name,
        email=email,
        phone=phone or None,
        age=age_value,
        password=generate_password_hash(password),
        gender=gender,
        role="patient",
        patient_uid=_next_patient_uid(),
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Patient registered successfully"}), 201

@app.route("/api/forgot-password", methods=["POST"])
@app.route("/auth/forgot-password", methods=["POST"])
def forgot_password():
    """
    Generates a password reset token for a user (Patient or Doctor) 
    and sends it via email.
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"status": "error", "message": "Email is required"}), 400

    from models.patient import Patient
    from models.models import Doctor

    user = Patient.query.filter_by(email=email).first()
    if not user:
        user = Doctor.query.filter_by(email=email).first()

    if not user:
        return jsonify({"status": "error", "message": "Email not registered"}), 404

    token = get_serializer().dumps({"email": email})
    
    # Use dynamic IP detection for the frontend URL
    origin = request.headers.get("Origin", "")
    frontend_base = get_actual_frontend_url(origin).rstrip("/")
    reset_link = f"{frontend_base}/reset/{token}"

    sent, err = _send_reset_email(email, reset_link)
    if not sent:
        return jsonify({"status": "error", "message": f"Failed to send reset email: {err}"}), 500

    response = {
        "status": "success",
        "message": "Reset link generated and sent to email",
    }

    if os.getenv("HMS_EXPOSE_RESET_TOKEN", "0") == "1":
        response["reset_token"] = token
        response["reset_url"] = f"/reset/{token}"
        response["frontend_reset_url"] = reset_link

    return jsonify(response), 200

@app.route("/api/reset-password", methods=["POST"])
@app.route("/auth/reset-password", methods=["POST"])
def reset_password():
    """
    Resets the user's password using a valid reset token.
    """
    data = request.get_json() or {}
    token = data.get("token") or ""
    password = data.get("password") or ""

    if not token or not password:
        return jsonify({"status": "error", "message": "Token and password are required"}), 400

    pass_error = _validate_password(password)
    if pass_error:
        return jsonify({"status": "error", "message": pass_error}), 400

    try:
        payload = get_serializer().loads(token, max_age=3600)
        email = (payload.get("email") or "").strip().lower()
    except SignatureExpired:
        return jsonify({"status": "error", "message": "Reset token expired"}), 400
    except BadSignature:
        return jsonify({"status": "error", "message": "Invalid reset token"}), 400

    from models.patient import Patient
    from models.models import Doctor

    user = Patient.query.filter_by(email=email).first()
    if not user:
        user = Doctor.query.filter_by(email=email).first()

    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    if hasattr(user, 'password_hash'):
        user.password_hash = generate_password_hash(password)
        user.set_password_status = "password set successfully"
    else:
        user.password = generate_password_hash(password)

    db.session.commit()
    return jsonify({"status": "success", "message": "Password reset successful"}), 200

@app.route("/api/doctor/set-password", methods=["POST"])
def doctor_set_password():
    """
    Special endpoint for doctors to set their initial password 
    when their account is first created by an admin.
    """
    data = request.get_json() or {}
    token = data.get("token")
    password = data.get("password")

    if not password:
        return jsonify({"status": "error", "message": "Password is required"}), 400
    
    pass_error = _validate_password(password)
    if pass_error:
        return jsonify({"status": "error", "message": pass_error}), 400
    
    try:
        payload = get_serializer().loads(token, max_age=3600)
        doctor_id = payload.get("doctor_id")
    except Exception as e:
        return jsonify({"status": "error", "message": "The setup link is invalid or has expired."}), 400

    from models.models import Doctor
    try:
        doctor = db.session.get(Doctor, int(doctor_id))
    except (ValueError, TypeError):
         return jsonify({"status": "error", "message": f"Invalid doctor ID in link: {doctor_id}"}), 400

    if not doctor:
        return jsonify({
            "status": "error", 
            "message": f"Doctor with ID {doctor_id} not found. The account may have been deleted or re-created. Please ask Admin to resend the link."
        }), 404

    doctor.update_password(password)
    db.session.commit()

    return jsonify({"status": "success", "message": "Password set successfully"})

@app.route('/api/login', methods=['POST'])
@app.route('/auth/login', methods=['POST'])
def login():
    """
    Authenticates users (Admin, Doctor, Patient).
    Uses email and password, verifying against the appropriate table.
    """
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    role_hint = (data.get('role_hint') or '').strip().lower()

    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400

    from models.patient import Patient
    from models.models import Doctor

    user = None
    is_doctor = False

    if role_hint == "doctor":
        user = Doctor.query.filter_by(email=email).first()
        is_doctor = True
    else:
        user = Patient.query.filter_by(email=email).first()
        is_doctor = False

    if not user:
        if role_hint == "doctor":
            user = Patient.query.filter_by(email=email).first()
            is_doctor = False
        else:
            user = Doctor.query.filter_by(email=email).first()
            is_doctor = True

    if not user:
        return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401

    password_ok = False
    if is_doctor:
        if getattr(user, 'set_password_status', "") != "password set successfully":
            return jsonify({'status': 'error', 'message': 'Please set your password first'}), 400
        password_ok = user.check_password(password)
    else:
        try:
            password_ok = check_password_hash(user.password, password)
        except (ValueError, TypeError):
            password_ok = False
        if not password_ok and user.password == password:
            user.password = generate_password_hash(password)
            db.session.commit()
            password_ok = True

    if password_ok:
        return jsonify(_build_login_response(user))

    return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401

@app.route('/api/logout', methods=['POST'])
@app.route('/auth/logout', methods=['POST'])
def logout():
    return jsonify({'status': 'success'})

@app.route('/api/me', methods=['GET'])
@app.route('/auth/me', methods=['GET'])
def me():
    """
    Returns current logged-in user details based on the JWT token.
    """
    if not g.user:
        msg = getattr(g, "auth_error", "Not logged in")
        return jsonify({'status': 'error', 'message': msg}), 401

    role = getattr(g.user, "role", "patient") or "patient"
    return jsonify({
        'status': 'success',
        'user': {
            'id': g.user.id,
            'name': g.user.name,
            'email': g.user.email,
            'role': role,
            'redirect_to': ROLE_DASHBOARD_PATHS.get(role, '/patient'),
        }
    })

# Blueprints
app.register_blueprint(dashboard_bp)
app.register_blueprint(admin_bp)
# app.register_blueprint(auth_bp) # Moved to app.py
app.register_blueprint(doctor_bp)

# Create tables
with app.app_context():
    db.create_all()
    # Safe migration: add 'remark' column to appointments if it doesn't exist yet.
    # This handles Docker containers whose DB was created before this column was added.
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE appointments ADD COLUMN remark VARCHAR(255)"))
            conn.commit()
    except Exception:
        pass

    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE appointments ADD COLUMN missed_mail_sent BOOLEAN DEFAULT 0"))
            conn.commit()
    except Exception:
        pass
    try:
        with db.engine.connect() as conn:
            # Check for existing column names if we previously used set_password or password_set
            try:
                conn.execute(text("ALTER TABLE doctors ADD COLUMN set_password_status VARCHAR(50) DEFAULT 'password not set'"))
            except Exception: pass
            
            # Migration: if set_password exists, copy its data then drop it if possible (or just keep it)
            try:
                conn.execute(text("UPDATE doctors SET set_password_status = set_password WHERE set_password IS NOT NULL"))
            except Exception: pass
            
            # Legacy cleanup: if anyone was using the old boolean column
            try:
                conn.execute(text("UPDATE doctors SET set_password_status = 'password set successfully' WHERE password_set = 1"))
            except Exception: pass
            
            conn.commit()
    except Exception:
        pass

    _ensure_default_admin()

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "1") == "1"
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=debug_mode, host="0.0.0.0", port=port)
