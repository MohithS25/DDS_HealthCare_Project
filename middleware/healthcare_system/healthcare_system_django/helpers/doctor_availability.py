# my_app/helpers/doctor_availability.py

# Instead of importing from .models, import directly from the main app models
from ..models import DoctorAvailability, Doctors

from datetime import date

def get_doctor_availability(doctor_name, department_name, hospital_name):
    try:
        # Fetch the doctor based on the provided details
        doctor = Doctors.objects.filter(
            doctor_name=doctor_name,
            department__department_name=department_name,
            hospital__name=hospital_name
        ).first()

        if not doctor:
            return {'status': 'failed', 'message': 'Doctor not found'}

        # Fetch availability for the doctor starting from today
        availability = DoctorAvailability.objects.filter(
            doctor=doctor,
            available_date__gte=date.today(),
            is_booked=False
        ).order_by('available_date', 'available_time')

        if not availability.exists():
            return {'status': 'failed', 'message': 'No available time slots found for this doctor'}

        # Prepare response data
        available_slots = [
            {
                'available_date': slot.available_date.strftime('%Y-%m-%d'),
                'available_time': slot.available_time.strftime('%H:%M:%S')
            }
            for slot in availability
        ]

        return {'status': 'success', 'available_slots': available_slots}

    except Exception as e:
        return {'status': 'failed', 'message': str(e)}
