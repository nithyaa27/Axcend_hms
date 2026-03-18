from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


# Department Table
class Department(db.Model):
    """
    Represents a hospital department (e.g., Cardiology, Neurology).
    Contains basic info and maintains a bidirectional relationship with doctors.
    """
    __tablename__ = "departments"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    head        = db.Column(db.String(100))
    status      = db.Column(db.String(20), default="Active")

    doctors = db.relationship("Doctor", backref="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"


# Doctor Table
class Doctor(db.Model):
    """
    Represents a doctor in the hospital system.
    Stores professional details, login credentials (hashed),
    and their association with a specific department.
    """
    __tablename__ = "doctors"

    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100))
    email          = db.Column(db.String(120))
    phone          = db.Column(db.String(20))
    status         = db.Column(db.String(20), default="available")
    

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id")
    )

    password_hash = db.Column(db.String(255))
    set_password_status = db.Column(db.String(50), default="password not set")

    def update_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.set_password_status = "password set successfully"

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role(self):
        return "doctor"

    # ✅ Alias so old code using Doctor.dept_id still works
    dept_id = db.synonym("department_id")

    schedules = db.relationship("DoctorSchedule", backref="doctor", lazy=True)

    def __repr__(self):
        return f"<Doctor {self.name}>"


# DoctorSchedule Table
class DoctorSchedule(db.Model):
    """
    Weekly schedule for a doctor, defining work hours (shift_start/end)
    and work type (OPD, Emergency, etc.) for each day of the week.
    """
    __tablename__ = "doctor_schedules"

    id        = db.Column(db.Integer, primary_key=True)

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=False
    )

    day_of_week = db.Column(db.String(15), nullable=False)  # "Monday", "Tuesday"...
    shift_start = db.Column(db.String(10), default="09:00")
    shift_end   = db.Column(db.String(10), default="17:00")
    work_type   = db.Column(db.String(20), default="OPD")   # OPD/Emergency/Surgery/Leave

    def __repr__(self):
        return f"<DoctorSchedule doctor={self.doctor_id} {self.day_of_week} {self.work_type}>"


class DoctorAvailability(db.Model):

    __tablename__ = "doctor_availability"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=False,
    )
    date = db.Column(db.Date, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    doctor = db.relationship("Doctor", backref="availability_entries")

    __table_args__ = (
        db.UniqueConstraint("doctor_id", "date", name="uq_doctor_availability_day"),
    )


class Prescription(db.Model):
    """
    Detailed medical prescription issued by a doctor to a patient.
    Links a diagnosis to specific medications and instructions.
    """
    __tablename__ = "prescriptions"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=False
    )
    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey("appointments.id"),
        nullable=True
    )

    diagnosis = db.Column(db.String(255), nullable=False)
    medications_json = db.Column(db.Text, nullable=False, default="[]")
    instructions = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="active")

    prescribed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    follow_up_date = db.Column(db.Date, nullable=True)

    doctor = db.relationship("Doctor", backref="prescriptions")
    appointment = db.relationship("Appointment", backref="prescriptions")

    def __repr__(self):
        return f"<Prescription {self.id} patient={self.patient_id} doctor={self.doctor_id}>"
