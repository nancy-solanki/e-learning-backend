#!/usr/bin/env python
"""
scripts/seed_data.py

Populates the database with initial seed data (superuser, instructors, and students).
Idempotent execution ensuring existing data is preserved or updated safely.
"""

import os
import sys

import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

User = get_user_model()


def seed_superusers():
    """Seed initial superuser / admin user."""
    admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com").lower()
    admin_username = os.getenv("SEED_ADMIN_USERNAME", "admin").lower()
    admin_password = os.getenv("SEED_ADMIN_PASSWORD", "AdminPassword123!")

    user, created = User.objects.get_or_create(
        email=admin_email,
        defaults={
            "username": admin_username,
            "first_name": "System",
            "last_name": "Admin",
            "status": User.Status.ACTIVE,
            "gender": User.Gender.MALE,
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )

    if created:
        user.set_password(admin_password)
        user.save()
        print(f"  [+] Superuser created: {admin_email} (username: {admin_username})")
    else:
        print(f"  [-] Superuser already exists: {admin_email}")

    return user


def seed_instructors():
    """Seed initial instructor / staff users."""
    instructors_data = [
        {
            "email": "instructor@example.com",
            "username": "instructor",
            "first_name": "Jane",
            "last_name": "Teacher",
            "gender": User.Gender.FEMALE,
        },
        {
            "email": "john.instructor@example.com",
            "username": "john_instructor",
            "first_name": "John",
            "last_name": "Doe",
            "gender": User.Gender.MALE,
        },
    ]

    count = 0
    for data in instructors_data:
        email = data["email"].lower()
        username = data["username"].lower()
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username,
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "status": User.Status.ACTIVE,
                "gender": data["gender"],
                "is_staff": True,
                "is_superuser": False,
                "is_active": True,
            },
        )
        if created:
            user.set_password("InstructorPassword123!")
            user.save()
            print(f"  [+] Instructor created: {email} (username: {username})")
            count += 1
        else:
            print(f"  [-] Instructor already exists: {email}")

    return count


def seed_students():
    """Seed initial student users."""
    students_data = [
        {
            "email": "student1@example.com",
            "username": "student1",
            "first_name": "Alice",
            "last_name": "Smith",
            "gender": User.Gender.FEMALE,
            "status": User.Status.ACTIVE,
        },
        {
            "email": "student2@example.com",
            "username": "student2",
            "first_name": "Bob",
            "last_name": "Johnson",
            "gender": User.Gender.MALE,
            "status": User.Status.ACTIVE,
        },
        {
            "email": "student3@example.com",
            "username": "student3",
            "first_name": "Charlie",
            "last_name": "Brown",
            "gender": User.Gender.MALE,
            "status": User.Status.ACTIVE,
        },
        {
            "email": "pending.student@example.com",
            "username": "pending_student",
            "first_name": "David",
            "last_name": "Pending",
            "gender": User.Gender.MALE,
            "status": User.Status.PENDING,
        },
    ]

    count = 0
    for data in students_data:
        email = data["email"].lower()
        username = data["username"].lower()
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username,
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "status": data["status"],
                "gender": data["gender"],
                "is_staff": False,
                "is_superuser": False,
                "is_active": True,
            },
        )
        if created:
            user.set_password("StudentPassword123!")
            user.save()
            print(f"  [+] Student created: {email} (username: {username})")
            count += 1
        else:
            print(f"  [-] Student already exists: {email}")

    return count


def run_seed():
    """Execute all seed data routines."""
    header = "=" * 50
    print(header)
    print("Seeding database initial data...")
    print(header)

    print("\n1. Seeding Superuser...")
    seed_superusers()

    print("\n2. Seeding Instructors...")
    seed_instructors()

    print("\n3. Seeding Students...")
    seed_students()

    print("\n" + header)
    print("Database seeding completed successfully!")
    print(header)


if __name__ == "__main__":
    run_seed()
