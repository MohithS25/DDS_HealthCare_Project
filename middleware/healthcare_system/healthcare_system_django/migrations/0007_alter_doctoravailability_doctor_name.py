# Generated by Django 5.1.3 on 2024-12-01 20:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('healthcare_system_django', '0006_alter_doctoravailability_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doctoravailability',
            name='doctor_name',
            field=models.TextField(),
        ),
    ]
