from app import app
from models.appointment import Appointment
with app.app_context():
    print(f'Appts: {Appointment.query.count()}')
    appointments = Appointment.query.order_by(Appointment.updated_at.desc()).limit(5).all()
    for appointment in appointments:
        print(
            f'Appt: {appointment.id} - {appointment.status} - '
            f'{appointment.reminder_email_status} - {appointment.reminder_email_message}'
        )
