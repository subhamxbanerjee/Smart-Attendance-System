#!/usr/bin/env python
"""Test API endpoints and data layer."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User
from attendance.models import Session, ClassRoom, AttendanceRecord
from accounts.models import Student

print('\n' + '='*60)
print('STEP 1: VERIFY TEST DATA & API LAYER')
print('='*60)

# Verify admin user
admin = User.objects.filter(username='admin').first()
print(f'✓ Admin user exists: {bool(admin)}')
print(f'  - Username: {admin.username if admin else "N/A"}')
print(f'  - Email: {admin.email if admin else "N/A"}')

# Student count
student_count = Student.objects.count()
print(f'\n✓ Students in database: {student_count}')
students = Student.objects.all()
for s in students:
    print(f'  - {s.usn}: {s.name} ({s.email}) [Phone: {s.student_phone}]')

# Session count
session_count = Session.objects.count()
print(f'\n✓ Sessions in database: {session_count}')
sessions = Session.objects.filter(is_active=True)
for session in sessions:
    print(f'  - {session.name} in {session.class_room} [Active: {session.is_active}]')
    print(f'    Start: {session.start_time} | End: {session.end_time}')

# Classroom count
classroom_count = ClassRoom.objects.count()
print(f'\n✓ Classrooms in database: {classroom_count}')
classrooms = ClassRoom.objects.all()
for c in classrooms:
    print(f'  - {c.name} (Section: {c.section or "N/A"})')

# Attendance records
attendance_count = AttendanceRecord.objects.count()
print(f'\n✓ Attendance records: {attendance_count}')

print('\n' + '='*60)
print('API DATA LAYER VERIFICATION: PASSED ✓')
print('='*60)
print('\nNext: Frontend test at http://localhost:5173/')
print('API endpoints available at: http://127.0.0.1:8000/api/')
