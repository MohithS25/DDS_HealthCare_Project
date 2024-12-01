from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from .models import Users, Departments, DoctorAvailability, Hospitals, Doctors  # Import the User model
import json
from django.db import transaction
from django.db.utils import IntegrityError
from django.views.decorators.csrf import csrf_exempt


# Create your views here.
@csrf_exempt
def signup(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body)
            email = data.get('email')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            location = data.get('location')
            password = data.get('password')
            phone = data.get('phone')

            # Check if the email already exists in the database
            if Users.objects.filter(email=email).exists():
                return JsonResponse({'message': 'User already exists. Please log in.'}, status=400)

            # Create a new user
            user = Users.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                location=location,
                password=password,
                phone=phone,
            )

            # Return a success response with user details
            return JsonResponse({
                'message': 'Signup successful!',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'location': user.location
            }, status=201)

        except Exception as e:
            # Handle unexpected errors
            return JsonResponse({'error': str(e)}, status=500)

    # If the method is not POST, return a 405 Method Not Allowed response
    return JsonResponse({'message': 'Method not allowed'}, status=405)



@csrf_exempt  # Disable CSRF for testing
def login(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            # Check if the user exists and the password matches
            try:
                user = Users.objects.get(email=email)  # Find user by email
                if user.password == password:  # Verify password
                    # Return success response with user details
                    return JsonResponse({
                        'message': 'Login successful!',
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email,
                        'location': user.location
                    }, status=200)
                else:
                    return JsonResponse({'message': 'Invalid password.'}, status=400)
            except Users.DoesNotExist:
                return JsonResponse({'message': 'User does not exist. Please sign up.'}, status=404)

        except Exception as e:
            # Handle unexpected errors
            return JsonResponse({'error': str(e)}, status=500)

    # If the method is not POST, return a 405 Method Not Allowed response
    return JsonResponse({'message': 'Method not allowed'}, status=405)

@csrf_exempt  # Disable CSRF for testing purposes (optional in production)
def get_hospital_details(request):
    if request.method == 'POST':
        try:
            # Parse the JSON body
            body = json.loads(request.body)
            location = body.get('location')

            # Validate location parameter
            if not location:
                return JsonResponse({'status': 'failed', 'message': 'Location parameter is required'}, status=400)

            # Fetch hospitals in the specified location
            hospitals = Hospitals.objects.filter(location=location)

            if not hospitals.exists():
                return JsonResponse({'status': 'failed', 'message': 'No hospitals found for the given location'}, status=404)

            # Structure the response data
            response_data = []
            for hospital in hospitals:
                # Fetch departments for the current hospital
                departments = Departments.objects.filter(hospital=hospital)

                # Fetch doctors for each department
                department_data = []
                for department in departments:
                    doctors = Doctors.objects.filter(department=department)
                    department_data.append({
                        'department_id': department.department_id,
                        'department_name': department.department_name,
                        'doctors': [
                            {
                                'doctor_id': doctor.doctor_id,
                                'doctor_name': doctor.doctor_name,
                            }
                            for doctor in doctors
                        ]
                    })

                # Add hospital and its associated data to the response
                response_data.append({
                    'hospital_id': hospital.hospital_id,
                    'name': hospital.name,
                    'location': hospital.location,
                    'address': hospital.address,
                    'departments': department_data
                })

            return JsonResponse({'status': 'success', 'data': response_data}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'failed', 'message': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'failed', 'message': 'Invalid request method'}, status=405)


@csrf_exempt  # Disable CSRF for testing
def book_appointment(request):
    if request.method == 'POST':
        try:
            # Parse parameters from the request body
            data = json.loads(request.body)
            doctor_id = data.get('doctor_id')
            date = data.get('date')
            time = data.get('time')

            if not (doctor_id and date and time):
                return JsonResponse({"status": "failed", "message": "Missing parameters"}, status=400)

            with transaction.atomic(using='default', savepoint=True):
                # Set the isolation level to SERIALIZABLE
                transaction.set_autocommit(False)
                transaction.set_isolation_level('serializable')

                # Check if the slot is already booked
                slot = DoctorAvailability.objects.select_for_update().get(
                    doctor_id=doctor_id,
                    available_date=date,
                    available_time=time
                )

                if slot.is_booked:
                    return JsonResponse({"status": "failed", "message": "Slot already booked"}, status=400)

                # Mark the slot as booked
                slot.is_booked = True
                slot.save()

                return JsonResponse({
                    "status": "success",
                    "message": "Appointment booked successfully",
                    "doctor_id": doctor_id,
                    "date": date,
                    "time": time
                }, status=201)

        except DoctorAvailability.DoesNotExist:
            return JsonResponse({"status": "failed", "message": "Slot does not exist"}, status=404)

        except IntegrityError:
            return JsonResponse({"status": "failed", "message": "Concurrency error. Please try again."}, status=409)

        except Exception as e:
            return JsonResponse({"status": "failed", "message": str(e)}, status=500)

        finally:
            transaction.set_autocommit(True)

    return JsonResponse({"status": "failed", "message": "Invalid request method"}, status=405)


@csrf_exempt  # Disable CSRF for testing purposes (optional in production)
def get_doctor_availability(request):
    if request.method == 'POST':
        try:
            # Parse the JSON body
            body = json.loads(request.body)
            doctor_name = body.get('doctor_name')
            department_name = body.get('department_name')
            hospital_name = body.get('hospital_name')

            # Validate input parameters
            if not (doctor_name and department_name and hospital_name):
                return JsonResponse({'status': 'failed', 'message': 'All parameters (doctor_name, department_name, hospital_name) are required'}, status=400)

            # Fetch the doctor based on the provided details
            doctor = Doctors.objects.filter(
                doctor_name=doctor_name,
                department_name=department_name,
                hospital_name=hospital_name
            ).first()

            if not doctor:
                return JsonResponse({'status': 'failed', 'message': 'Doctor not found'}, status=404)

            # Fetch the availability of the doctor
            availability = DoctorAvailability.objects.filter(doctor=doctor, is_booked=False)

            if not availability.exists():
                return JsonResponse({'status': 'failed', 'message': 'No available time slots found for this doctor'}, status=404)

            # Prepare response data
            available_slots = [
                {
                    'available_date': slot.available_date,
                    'available_time': slot.available_time
                }
                for slot in availability
            ]

            return JsonResponse({
                'status': 'success',
                'doctor_name': doctor.doctor_name,
                'department_name': doctor.department_name,
                'hospital_name': doctor.hospital_name,
                'available_slots': available_slots
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'failed', 'message': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'failed', 'message': 'Invalid request method'}, status=405)