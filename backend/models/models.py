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
    password_set = db.Column(db.Boolean, default=False)
    set_password_token = db.Column(db.String(255), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.password_set = True
        self.set_password_status = "password set successfully"

    def update_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.password_set = True
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


class ReminderSettings(db.Model):
    __tablename__ = "reminder_settings"

    id = db.Column(db.Integer, primary_key=True, default=1)
    daily_enabled = db.Column(db.Boolean, nullable=False, default=False)
    daily_time = db.Column(db.String(5), nullable=False, default="09:00")
    monthly_enabled = db.Column(db.Boolean, nullable=False, default=False)
    monthly_day = db.Column(db.Integer, nullable=False, default=1)
    monthly_time = db.Column(db.String(5), nullable=False, default="09:00")
    last_daily_sent_on = db.Column(db.Date, nullable=True)
    last_monthly_sent_period = db.Column(db.String(7), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ReminderSettings daily={self.daily_enabled} monthly={self.monthly_enabled}>"


class PatientReminder(db.Model):
    __tablename__ = "patient_reminders"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    reminder_type = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    scheduled_for = db.Column(db.DateTime, nullable=False, index=True)
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    related_appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id"), nullable=True)

    patient = db.relationship("Patient", backref="reminder_items")
    appointment = db.relationship("Appointment", backref="patient_reminders")

    def __repr__(self):
        return f"<PatientReminder patient={self.patient_id} type={self.reminder_type}>"


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_role = db.Column(db.String(20), nullable=False)   # 'admin' or 'doctor'
    sender_id = db.Column(db.Integer, nullable=False)       # doctor.id or admin.id (default 1)
    receiver_role = db.Column(db.String(20), nullable=False) # 'admin' or 'doctor'
    receiver_id = db.Column(db.Integer, nullable=False)     # doctor.id or admin.id
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def to_dict(self):
        ts = self.timestamp
        if isinstance(ts, str):
            ts_iso = ts if ts.endswith('Z') else ts + 'Z'
        elif ts:
            ts_iso = ts.isoformat() + 'Z'
        else:
            ts_iso = None

        return {
            "id": self.id,
            "sender_role": self.sender_role,
            "sender_id": self.sender_id,
            "receiver_role": self.receiver_role,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "timestamp": ts_iso,
            "is_read": self.is_read
        }
