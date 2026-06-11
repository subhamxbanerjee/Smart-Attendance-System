#!/usr/bin/env python
"""Setup test data for the Student Face Recognition System."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Student
from attendance.models import ClassRoom, Session, TimeTable
from datetime import timedelta
from django.utils import timezone

# Create superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
    print('[OK] Admin user created: admin / admin123')
else:
    print('[OK] Admin user already exists')

# Create test students
students_data = [
    {'usn': 'USN001', 'name': 'Alice Johnson', 'email': 'alice@test.com', 'student_phone': '9876543210', 'parent_phone': '9876543211'},
    {'usn': 'USN002', 'name': 'Bob Smith', 'email': 'bob@test.com', 'student_phone': '9876543212', 'parent_phone': '9876543213'},
    {'usn': 'USN003', 'name': 'Charlie Brown', 'email': 'charlie@test.com', 'student_phone': '9876543214', 'parent_phone': '9876543215'},
]

for data in students_data:
    student, created = Student.objects.get_or_create(
        usn=data['usn'],
        defaults={
            'name': data['name'],
            'email': data['email'],
            'student_phone': data['student_phone'],
            'parent_phone': data['parent_phone'],
            'can_login': True
        }
    )
    if created:
        print(f'[OK] Student created: {data["usn"]} - {data["name"]}')
    else:
        print(f'[OK] Student already exists: {data["usn"]}')

# Create classroom
classroom, created = ClassRoom.objects.get_or_create(
    name='Class A',
    defaults={'section': 'A1'}
)
if created:
    print(f'[OK] Classroom created: Class A')
else:
    print(f'[OK] Classroom already exists: Class A')

# Create session
now = timezone.now()
session, created = Session.objects.get_or_create(
    name='Morning Session',
    class_room=classroom,
    start_time=now,
    defaults={
        'end_time': now + timedelta(hours=2),
        'is_active': True
    }
)
if created:
    print(f'[OK] Session created: Morning Session')
else:
    print(f'[OK] Session already exists: Morning Session')

# Create timetable
timetable, created = TimeTable.objects.get_or_create(
    day_of_week=0,
    session_name='Python Programming',
    start_time='09:00',
    end_time='11:00',
    defaults={
        'class_room': classroom,
        'is_active': True
    }
)
if created:
    print(f'[OK] TimeTable created: MON 09:00-11:00')
else:
    print(f'[OK] TimeTable already exists')

print('\n[SUCCESS] Test data setup complete!')
print('\nAccess Django admin at: http://127.0.0.1:8000/admin')
print('Username: admin')
print('Password: admin123')
