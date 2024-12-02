from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from .models import Users, Departments, DoctorAvailability, Hospitals, Doctors  # Import the User model
import json
from django.db import transaction
from django.db.utils import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from datetime import date
from django.db import connection
from django.db import transaction
from .helpers.doctor_availability import get_doctor_availability



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
                    department_doctors = []

                    for doctor in doctors:
                        # Call the helper function to get doctor availability
                        doctor_availability = get_doctor_availability(
                            doctor.doctor_name,
                            department.department_name,
                            hospital.name
                        )

                        department_doctors.append({
                            'doctor_id': doctor.doctor_id,
                            'doctor_name': doctor.doctor_name,
                            'available_slots': doctor_availability.get('available_slots', [])
                        })

                    department_data.append({
                        'department_id': department.department_id,
                        'department_name': department.department_name,
                        'doctors': department_doctors
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
            # Parse the array of appointment data from the request body
            data = json.loads(request.body)  # This is now a list of appointment objects

            if not isinstance(data, list):  # Check if the data is a list
                return JsonResponse({"status": "failed", "message": "Invalid data format. Expected an array."}, status=400)

            # List to collect errors (if any) for each appointment slot
            errors = []

            # Iterate through each appointment slot
            for appointment in data:
                doctor_id = appointment.get('doctor_id')
                date = appointment.get('date')
                time = appointment.get('time')

                if not (doctor_id and date and time):
                    errors.append(f"Missing parameters for doctor {doctor_id} on {date} at {time}")
                    continue  # Skip this slot and move to the next one

                # Handle the slot booking logic
                try:
                    with transaction.atomic():
                        with connection.cursor() as cursor:
                            cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;")

                        # Lock the row for update
                        slot = DoctorAvailability.objects.select_for_update().get(
                            doctor_id=doctor_id,
                            available_date=date,
                            available_time=time
                        )

                        if slot.is_booked:
                            errors.append(f"Slot already booked for doctor {doctor_id} on {date} at {time}")
                            continue  # Skip this slot and move to the next one

                        # Mark the slot as booked
                        slot.is_booked = True
                        slot.save()

                except DoctorAvailability.DoesNotExist:
                    errors.append(f"Slot does not exist for doctor {doctor_id} on {date} at {time}")
                except IntegrityError:
                    errors.append(f"Concurrency error for doctor {doctor_id} on {date} at {time}. Please try again.")
                except Exception as e:
                    errors.append(f"Error booking slot for doctor {doctor_id} on {date} at {time}: {str(e)}")

            if errors:
                return JsonResponse({"status": "failed", "message": "Some appointments could not be booked.", "errors": errors}, status=400)

            return JsonResponse({
                "status": "success",
                "message": "Appointments booked successfully"
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"status": "failed", "message": "Invalid JSON format in the request body"}, status=400)

        except Exception as e:
            return JsonResponse({"status": "failed", "message": str(e)}, status=500)

    return JsonResponse({"status": "failed", "message": "Invalid request method"}, status=405)
