import jwt
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

# ==========================================================
# Token & Security Utilities
# ==========================================================
# Handles generation and validation of JWT tokens for auth
# and URL-safe serializers for password resets.

def get_serializer():
    """
    Returns a serializer used for securely signing and timestamping data 
    (like password reset tokens).
    """
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="hms-password-reset")

def generate_doctor_password_token(doctor_id):
    serializer = get_serializer()
    return serializer.dumps({
        "doctor_id": doctor_id,
        "type": "doctor_password"
    })

def create_jwt_token(user_id, email, role):
    """
    Creates a JSON Web Token (JWT) for user authentication.
    Contains user ID, email, role, and an expiration timestamp.
    """
    # Short expiry for patient to test session expiry, long for others
    if role == "patient" or role is None:
        expiry = timedelta(hours=24)
    else:
        expiry = timedelta(hours=24)
        
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + expiry
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

def decode_jwt_token(token):
    """
    Decodes and validates a JWT token.
    Returns the decoded payload if valid, or an error message if expired/invalid.
    """
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "session_expired"
    except jwt.InvalidTokenError:
        return None, "invalid_token"
