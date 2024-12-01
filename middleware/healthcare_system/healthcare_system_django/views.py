from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from .models import Users  # Import the User model
import json
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