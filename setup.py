"""
Setup script for Sport Prediction System
Run: python setup.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'football_prediction_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import execute_from_command_line

User = get_user_model()

def setup():
    print("Setting up Sport Prediction System...")
    
    # Run migrations
    print("\n1. Running migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Create superuser if needed
    print("\n2. Checking for superuser...")
    if not User.objects.filter(is_superuser=True).exists():
        print("No superuser found. Creating one...")
        print("Please run: python manage.py createsuperuser")
    else:
        print("Superuser already exists.")
    
    print("\n3. Setup complete!")
    print("\nNext steps:")
    print("  - Create a superuser: python manage.py createsuperuser")
    print("  - Run the server: python manage.py runserver")
    print("  - Access admin: http://127.0.0.1:8000/admin/")
    print("  - View site: http://127.0.0.1:8000/")

if __name__ == '__main__':
    setup()

