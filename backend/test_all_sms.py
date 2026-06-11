import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from accounts.models import Student
from attendance.utils import send_sms

print("=" * 60)
print("TESTING SMS TO ALL STUDENTS")
print("=" * 60)

students = Student.objects.all()
test_message = "Test: Your child is absent for today's class. This is a test message from the attendance system."

for student in students:
    print(f"\n{'='*60}")
    print(f"Student: {student.name} ({student.usn})")
    print(f"{'='*60}")
    
    # Send to student phone
    if student.student_phone:
        print(f"\nSending to STUDENT phone: {student.student_phone}")
        result = send_sms(student.student_phone, test_message)
        if result and result != "MOCK_SID":
            print(f"  ✓ SUCCESS - SID: {result}")
        elif result == "MOCK_SID":
            print(f"  ⚠ MOCK MODE - Twilio not configured")
        else:
            print(f"  ✗ FAILED")
    
    # Send to parent phone
    if student.parent_phone:
        print(f"\nSending to PARENT phone: {student.parent_phone}")
        result = send_sms(student.parent_phone, test_message)
        if result and result != "MOCK_SID":
            print(f"  ✓ SUCCESS - SID: {result}")
        elif result == "MOCK_SID":
            print(f"  ⚠ MOCK MODE - Twilio not configured")
        else:
            print(f"  ✗ FAILED")

print(f"\n{'='*60}")
print("TEST COMPLETE")
print(f"{'='*60}")
print("\nCheck your phones for the test messages!")
