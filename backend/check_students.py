import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from accounts.models import Student

print("=" * 60)
print("ALL STUDENT PHONE NUMBERS")
print("=" * 60)

students = Student.objects.all()
print(f"\nTotal students: {students.count()}\n")

for student in students:
    print(f"USN: {student.usn}")
    print(f"  Name: {student.name}")
    print(f"  Student Phone: {student.student_phone}")
    print(f"  Parent Phone: {student.parent_phone}")
    print()
