import smtplib
from email.message import EmailMessage

import threading

def _send_email_sync(msg):
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("hmsproject26@gmail.com", "lfynpsyxnqvjiypd")
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_doctor_password_email(email, token, frontend_base=""):

    link = f"{frontend_base}/doctor-set-password/{token}"

    msg = EmailMessage()
    msg["Subject"] = "Set your Doctor Password"
    msg["From"] = "hmsproject26@gmail.com"
    msg["To"] = email

    msg.set_content(
        f"Welcome to HMS.\n\n"
        f"Click this link to set your password:\n{link}\n\n"
        f"This link expires in 1 hour."
    )

    thread = threading.Thread(target=_send_email_sync, args=(msg,))
    thread.start()

