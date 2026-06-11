import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from accounts.models import Student

print("=" * 50)
print("FIXING PHONE NUMBER FORMATS")
print("=" * 50)

students = Student.objects.all()
updated_count = 0

for student in students:
    updated = False
    
    # Fix student phone
    if student.student_phone and not student.student_phone.startswith('+'):
        old_phone = student.student_phone
        student.student_phone = f"+91{student.student_phone}"
        print(f"Student {student.usn}: {old_phone} -> {student.student_phone}")
        updated = True
    
    # Fix parent phone
    if student.parent_phone and not student.parent_phone.startswith('+'):
        old_phone = student.parent_phone
        student.parent_phone = f"+91{student.parent_phone}"
        print(f"Parent {student.usn}: {old_phone} -> {student.parent_phone}")
        updated = True
    
    if updated:
        student.save()
        updated_count += 1

print(f"\n✓ Updated {updated_count} student records")
print("\nDone! Phone numbers are now in E.164 format (+91XXXXXXXXXX)")
