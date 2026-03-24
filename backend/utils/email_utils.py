import os
import smtplib
from email.message import EmailMessage

import threading


def _smtp_config():
    # Priority: HMS_ prefixes from environment, then EMAIL_ prefixes, then working defaults
    host = os.getenv("HMS_SMTP_HOST") or os.getenv("EMAIL_HOST") or "smtp.gmail.com"
    port = int(os.getenv("HMS_SMTP_PORT") or os.getenv("EMAIL_PORT") or "587")
    user = os.getenv("HMS_SMTP_USER") or os.getenv("EMAIL_USER") or "hmsproject26@gmail.com"
    # Use the known-good default 'lfynpsyxnqvjiypd' if no env var is set
    password = os.getenv("HMS_SMTP_APP_PASSWORD") or os.getenv("EMAIL_PASS") or "lfynpsyxnqvjiypd"
    
    return host, port, user, password


def _send_email_sync(msg):
    try:
        smtp_host, smtp_port, smtp_user, smtp_password = _smtp_config()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")


def _build_message(subject, recipient_email, body):
    _, _, smtp_user, _ = _smtp_config()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_user or "hmsproject26@gmail.com"
    msg["To"] = recipient_email
    msg.set_content(body)
    return msg


def send_doctor_password_email(email, token, frontend_base="http://localhost:5173"):

    link = f"{frontend_base}/doctor-set-password/{token}"
    msg = _build_message(
        "Set your Doctor Password",
        email,
        f"Welcome to HMS.\n\n"
        f"Click this link to set your password:\n{link}\n\n"
        f"This link expires in 1 hour."
    )

    thread = threading.Thread(target=_send_email_sync, args=(msg,))
    thread.start()


def send_patient_reminder_email(email, subject, message):
    msg = _build_message(subject, email, message)
    thread = threading.Thread(target=_send_email_sync, args=(msg,))
    thread.start()


def send_patient_transfer_email(email, subject, message):
    msg = _build_message(subject, email, message)
    thread = threading.Thread(target=_send_email_sync, args=(msg,))
    thread.start()
