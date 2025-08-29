import os

import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth.models import User

username = "admin"
password = "admin@123"
email = "admin@example.com"

if not User.objects.filter(username=username).exists():
    user = User.objects.create_superuser(
        username=username, email=email, password=password
    )
    print(f"Superuser '{username}' created successfully.")
else:
    print(f"User '{username}' already exists.")

username = "staff"
password = "staff@123"
email = "staff@example.com"

if not User.objects.filter(username=username).exists():
    user = User.objects.create_user(username=username, email=email, password=password)
    print(f"User '{username}' created successfully (staff user).")
else:
    print(f"User '{username}' already exists.")
