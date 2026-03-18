import re
from datetime import datetime
from flask import Blueprint, jsonify, request, g

from extensions import db
from models.appointment import Appointment, AppointmentStatus
from models.models import Department, Doctor
from models.patient import Patient
from utils.token_utils import generate_doctor_password_token
from utils.email_utils import send_doctor_password_email
from werkzeug.security import generate_password_hash, check_password_hash
from utils.network_utils import get_actual_frontend_url

# ==========================================
# Admin Routes Blueprint
# ==========================================
# This module contains the administrative functions for the HMS,
# including managing departments, doctors, patients, and appointments.

admin_bp = Blueprint("admin_bp", __name__)



@admin_bp.before_request
def require_admin():
    """
    Verification middleware: Ensures that any request hitting this blueprint
    is authenticated and belongs to an 'admin' user.
    """
    if not g.user:
        msg = getattr(g, "auth_error", "Authentication required")
        return jsonify({"message": msg}), 401

    role = (getattr(g.user, "role", "") or "").strip().lower()
    if role != "admin":
        return jsonify({"error": "Admins only"}), 403

    return None


@admin_bp.route("/api/admin/dashboard", methods=["GET"])
def admin_dashboard():
    """
    Returns high-level statistics (totals) for the admin dashboard overview.
    """
    
    return jsonify({
        "total_doctors": Doctor.query.count(),
        "total_departments": Department.query.count(),
        "total_patients": Patient.query.filter_by(role="patient").count(),
        "total_appointments": Appointment.query.count(),
    })


@admin_bp.route("/api/departments", methods=["GET"])
def get_departments():
    """
    Lists all hospital departments, including metadata like doctor count.
    """
    departments = Department.query.order_by(Department.id.desc()).all()
    departments = Department.query.order_by(Department.id.desc()).all()
    return jsonify([
        {
            "id": d.id,
            "name": d.name,
            "description": d.description or "",
            "head": d.head or "",
            "status": d.status or "Active",
            "doctors_count": len(d.doctors),
        }
        for d in departments
    ])


@admin_bp.route("/api/add_department", methods=["POST"])
def add_department():
    """
    Creates a new hospital department. Validates the name for duplicates and characters.
    """
    data = request.get_json() or {}
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    head = (data.get("head") or "").strip()
    status = (data.get("status") or "Active").strip()

    if not name:
        return jsonify({"error": "Department name required"}), 400

    if not re.match(r"^[A-Za-z\s]+$", name):
        return jsonify({"error": "Department name must contain only letters"}), 400

    existing = Department.query.filter(db.func.lower(Department.name) == name.lower()).first()
    if existing:
        return jsonify({"error": "Department already exists"}), 400

    new_department = Department(name=name, description=description, head=head, status=status)
    db.session.add(new_department)
    db.session.commit()

    return jsonify({"message": "Department added successfully"}), 201


@admin_bp.route("/api/update_department/<int:department_id>", methods=["PUT"])
def update_department(department_id):
    """
    Updates details of an existing department.
    """
    department = db.session.get(Department, department_id)
    department = db.session.get(Department, department_id)
    if not department:
        return jsonify({"error": "Department not found"}), 404

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    head = (data.get("head") or "").strip()
    status = (data.get("status") or "Active").strip()

    if not name:
        return jsonify({"error": "Department name required"}), 400

    if not re.match(r"^[A-Za-z\s]+$", name):
        return jsonify({"error": "Department name must contain only letters"}), 400

    existing = Department.query.filter(
        db.func.lower(Department.name) == name.lower(),
        Department.id != department_id
    ).first()
    if existing:
        return jsonify({"error": "Department already exists"}), 400

    department.name = name
    department.description = description
    department.head = head
    department.status = status
    db.session.commit()
    return jsonify({"message": "Department updated successfully"})


@admin_bp.route("/api/delete_department/<int:department_id>", methods=["DELETE"])
def delete_department(department_id):
    """
    Removes a department from the database. 
    Prevents deletion if doctors are still assigned to the department.
    """
    department = db.session.get(Department, department_id)
    department = db.session.get(Department, department_id)
    if not department:
        return jsonify({"error": "Department not found"}), 404

    if department.doctors:
        return jsonify({"error": "Cannot delete department. Doctors are assigned to it."}), 400

    db.session.delete(department)
    db.session.commit()
    return jsonify({"message": "Department deleted successfully"})


@admin_bp.route("/api/admin/doctors", methods=["GET"])
def get_admin_doctors():
    """
    Returns a comprehensive list of all doctors for the admin view.
    """
    doctors = Doctor.query.order_by(Doctor.id.desc()).all()
    doctors = Doctor.query.order_by(Doctor.id.desc()).all()
    return jsonify([
        {
            "id": doc.id,
            "name": doc.name,
            "specialization": doc.specialization,
            "email": doc.email,
            "phone": doc.phone,
            "status": doc.status,
            "department_name": doc.department.name if doc.department else "No Department",
            "department_id": doc.department_id,
            "set_password_status": doc.set_password_status,
        }
        for doc in doctors
    ])


@admin_bp.route("/api/add_doctor", methods=["POST"])
def add_doctor():
    """
    Onboards a new doctor. Validates all inputs and sends an automated
    email to the doctor to set their login password.
    """
    data = request.get_json() or {}
    data = request.get_json() or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    specialization = (data.get("specialization") or "").strip()
    status = (data.get("status") or "active").strip()
    department_id = data.get("department_id")
    

    if not all([name, email, phone, specialization, department_id, status]):
        return jsonify({"error": "All fields are required"}), 400

    if not re.match(r"^Dr\.?\s[A-Za-z\s]+$", name):
        return jsonify({"error": "Name must contain only letters"}), 400

    if not re.match(r"^[A-Za-z\s]+$", specialization):
        return jsonify({"error": "Specialization must contain only letters"}), 400

    if not re.match(r"^\d{10}$", phone):
        return jsonify({"error": "Phone number must be exactly 10 digits"}), 400

    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return jsonify({"error": "Invalid email format"}), 400

    department = db.session.get(Department, (department_id))
    if not department:
        return jsonify({"error": "Department not found"}), 404

    email_exists = Doctor.query.filter(db.func.lower(Doctor.email) == email).first()
    if email_exists:
        return jsonify({"error": "Email already exists"}), 400

    phone_exists = Doctor.query.filter_by(phone=phone).first()
    if phone_exists:
        return jsonify({"error": "Phone number already exists"}), 400

    new_doc = Doctor(
        name=name,
        email=email,
        phone=phone,
        department_id=department.id,
        specialization=specialization,
        status=status,
    )
    db.session.add(new_doc)
    db.session.commit()

    token = generate_doctor_password_token(new_doc.id)

    origin = request.headers.get("Origin", "")
    frontend_base = get_actual_frontend_url(origin)
    send_doctor_password_email(new_doc.email, token, frontend_base)

    return jsonify({"message": "Doctor added successfully"}), 201


@admin_bp.route("/api/update_doctor/<int:doctor_id>", methods=["PUT"])
def update_doctor(doctor_id):
    """
    Updates a doctor's profile information and assignment.
    """
    data = request.get_json() or {}
    data = request.get_json() or {}

    if not all([
        data.get("name"), data.get("email"), data.get("phone"),
        data.get("specialization"), data.get("department_id"), data.get("status")
    ]):
        return jsonify({"error": "All fields are required"}), 400

    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    specialization = (data.get("specialization") or "").strip()
    status = (data.get("status") or "").strip()
    department_id = data.get("department_id")

    if not re.match(r"^Dr\.?\s[A-Za-z\s]+$", name):
        return jsonify({"error": "Name must contain only letters"}), 400

    if not re.match(r"^[A-Za-z\s]+$", specialization):
        return jsonify({"error": "Specialization must contain only letters"}), 400

    if not re.match(r"^\d{10}$", phone):
        return jsonify({"error": "Phone number must be exactly 10 digits"}), 400

    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return jsonify({"error": "Invalid email format"}), 400

    department = db.session.get(Department, (department_id))
    if not department:
        return jsonify({"error": "Department not found"}), 404

    email_exists = Doctor.query.filter(
        db.func.lower(Doctor.email) == email,
        Doctor.id != doctor_id
    ).first()
    if email_exists:
        return jsonify({"error": "Email already exists"}), 400

    phone_exists = Doctor.query.filter(
        Doctor.phone == phone,
        Doctor.id != doctor_id
    ).first()
    if phone_exists:
        return jsonify({"error": "Phone number already exists"}), 400

    doctor.name = name
    doctor.specialization = specialization
    doctor.email = email
    doctor.phone = phone
    doctor.department_id = department.id
    doctor.status = status
    db.session.commit()
    return jsonify({"message": "Doctor updated successfully"})


@admin_bp.route("/api/delete_doctor/<int:doctor_id>", methods=["DELETE"])
def delete_doctor(doctor_id):
    """
    Removes a doctor record from the system.
    """
    doctor = db.session.get(Doctor, doctor_id)
    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    db.session.delete(doctor)
    db.session.commit()
    return jsonify({"message": "Doctor deleted successfully"})


@admin_bp.route("/api/admin/resend-doctor-password/<int:id>", methods=["POST"])
def resend_doctor_password(id):
    """
    Triggers a fresh password setup email to the doctor.
    """
    doctor = Doctor.query.get(id)

    doctor = Doctor.query.get(id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    token = generate_doctor_password_token(doctor.id)

    origin = request.headers.get("Origin", "")
    frontend_base = get_actual_frontend_url(origin)
    send_doctor_password_email(doctor.email, token, frontend_base)

    return jsonify({"message": "Password email sent again"})


@admin_bp.route("/api/admin/doctor-password-link/<int:doctor_id>", methods=["GET"])
def get_doctor_password_link(doctor_id):
    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    token = generate_doctor_password_token(doctor.id)
    return jsonify({
        "token": token,
        "path": f"/doctor-set-password/{token}",
    })


@admin_bp.route("/api/admin/patients", methods=["GET"])
def get_admin_patients():
    """
    Lists all registered patients for administrative management.
    """
    patients = Patient.query.filter_by(role="patient").order_by(Patient.id.desc()).all()
    patients = Patient.query.filter_by(role="patient").order_by(Patient.id.desc()).all()
    return jsonify([
        {
            "id": p.id,
            "patient_uid": p.patient_uid,
            "name": p.name,
            "email": p.email,
            "phone": p.phone,
            "age": p.age,
            "gender": p.gender,
            "created_at": p.created_at.isoformat() if getattr(p, 'created_at', None) else None,
        }
        for p in patients
    ])


@admin_bp.route("/api/admin/patients", methods=["POST"])
def add_patient_admin():
    """
    Allows admin to manually register a patient. Generates a unique Patient UID.
    """
    from werkzeug.security import generate_password_hash
    from werkzeug.security import generate_password_hash
    import uuid

    data = request.get_json() or {}
    name   = (data.get("name")   or "").strip()
    email  = (data.get("email")  or "").strip().lower()
    phone  = (data.get("phone")  or "").strip()
    gender = (data.get("gender") or "").strip()
    age    = data.get("age")

    if not all([name, email, phone, gender, age]):
        return jsonify({"error": "All fields are required"}), 400

    import re
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return jsonify({"error": "Invalid email format"}), 400

    existing = Patient.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "Email already exists"}), 400

    # Auto-generate a patient UID like P001, P002 …
    last = Patient.query.filter(Patient.patient_uid.isnot(None)).order_by(Patient.id.desc()).first()
    try:
        last_num = int((last.patient_uid or "P000")[1:]) if last else 0
    except ValueError:
        last_num = Patient.query.count()
    uid = f"P{str(last_num + 1).zfill(3)}"

    p = Patient(
        name=name,
        email=email,
        phone=phone,
        age=age,
        gender=gender,
        role="patient",
        patient_uid=uid,
        password=generate_password_hash(str(uuid.uuid4())),  # random password; patient resets via email
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"message": "Patient added successfully", "id": p.id}), 201


@admin_bp.route("/api/admin/patients/<int:patient_id>", methods=["PUT"])
def update_patient(patient_id):
    patient = db.session.get(Patient, patient_id)
    if not patient or patient.role != "patient":
        return jsonify({"error": "Patient not found"}), 404

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    age = data.get("age")
    gender = (data.get("gender") or "").strip()

    if not all([name, email, phone, age, gender]):
        return jsonify({"error": "All fields are required"}), 400

    import re
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return jsonify({"error": "Invalid email format"}), 400

    existing = Patient.query.filter(Patient.email == email, Patient.id != patient_id).first()
    if existing:
        return jsonify({"error": "Email already exists"}), 400

    patient.name = name
    patient.email = email
    patient.phone = phone
    patient.age = age
    patient.gender = gender
    db.session.commit()
    return jsonify({"message": "Patient updated successfully"})


@admin_bp.route("/api/admin/patients/<int:patient_id>", methods=["DELETE"])
def delete_patient(patient_id):
    patient = db.session.get(Patient, patient_id)
    if not patient or patient.role != "patient":
        return jsonify({"error": "Patient not found"}), 404

    db.session.delete(patient)
    db.session.commit()
    return jsonify({"message": "Patient deleted successfully"})


@admin_bp.route("/api/admin/appointments", methods=["GET"])
def get_admin_appointments():
    """
    Fetches all appointments across the entire system.
    """
    appointments = Appointment.query.order_by(Appointment.id.desc()).all()
    appointments = Appointment.query.order_by(Appointment.id.desc()).all()
    return jsonify([
        {
            "id": a.id,
            "doctor_id": a.doctor_id,
            "patient_id": a.patient_id,
            "doctor_name": a.doctor.name if a.doctor else "",
            "patient_name": a.patient.name if a.patient else "",
            "appointment_date": a.appointment_datetime.strftime("%Y-%m-%d") if a.appointment_datetime else "",
            "appointment_time": a.appointment_datetime.strftime("%I:%M %p").lstrip("0") if a.appointment_datetime else "",
            "status": a.get_derived_status(),
        }
        for a in appointments
    ])




@admin_bp.route("/api/admin/appointments/<int:appointment_id>", methods=["DELETE"])
def delete_admin_appointment(appointment_id):
    appointment = db.session.get(Appointment, appointment_id)
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    db.session.delete(appointment)
    db.session.commit()
    return jsonify({"message": "Appointment deleted successfully"})
