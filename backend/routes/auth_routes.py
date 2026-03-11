from itsdangerous import BadSignature, SignatureExpired
from utils.token_utils import get_serializer
from models.models import Doctor
from flask import request, jsonify
from extensions import db
from flask import Blueprint

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/api/doctor/set-password", methods=["POST"])
def doctor_set_password():

    data = request.get_json() or {}

    token = data.get("token")
    password = data.get("password")

    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    
    try:
        payload = get_serializer().loads(token, max_age=3600)

        doctor_id = payload["doctor_id"]

    except Exception:
        return jsonify({"error": "Invalid or expired link"}), 400

    doctor = db.session.get(Doctor, doctor_id)

    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    doctor.set_password(password)

    db.session.commit()

    return jsonify({"message": "Password set successfully"})


