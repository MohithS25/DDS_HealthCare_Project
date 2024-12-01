from django.db import models

# Create your models here.
class Users(models.Model):
    user_id = models.AutoField(primary_key=True)  # The composite primary key (user_id, location) found, that is not supported. The first column is selected.
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.CharField(max_length=150)
    location = models.CharField(max_length=50)
    password = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'
        unique_together = (('user_id', 'location'),)

class Hospitals(models.Model):
    hospital_id = models.AutoField(primary_key=True)
    name = models.TextField()
    location = models.TextField()
    address = models.TextField()

    class Meta:
        db_table = 'hospitals'
        unique_together = (('hospital_id', 'location'),)

    def __str__(self):
        return self.name

class Departments(models.Model):
    department_id = models.AutoField(primary_key=True)  # Unique identifier for the department
    department_name = models.TextField()  # Name of the department
    hospital = models.ForeignKey('Hospitals', on_delete=models.DO_NOTHING)  # Links to the Hospitals table

    class Meta:
        db_table = 'departments'
        unique_together = (('department_id', 'hospital'),)  # Ensure unique department per hospital

    def __str__(self):
        return self.department_name



class DoctorAvailability(models.Model):
    doctor = models.ForeignKey('Doctors', on_delete=models.CASCADE)
    available_date = models.DateField()
    available_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'available_date', 'available_time'],
                name='unique_doctor_slot'
            )
        ]

class Doctors(models.Model):
    doctor_id = models.AutoField(primary_key=True)
    doctor_name = models.TextField()
    department = models.ForeignKey('Departments', on_delete=models.DO_NOTHING)  # Link to Departments
    hospital = models.ForeignKey('Hospitals', on_delete=models.DO_NOTHING)  # Link to Hospitals
    location = models.TextField()  # Location is derived from the hospital
    department_name = models.TextField()  # Redundant; can be replaced by `department.department_name`
    hospital_name = models.TextField()  # Redundant; can be replaced by `hospital.name`

    class Meta:
        db_table = 'doctors'

    def __str__(self):
        return self.doctor_name

