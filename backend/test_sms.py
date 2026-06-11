import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from attendance.utils import send_sms
from accounts.models import Student

print("=" * 50)
print("SMS CONFIGURATION TEST")
print("=" * 50)

# Check environment variables
print(f"\nTWILIO_ACCOUNT_SID: {os.getenv('TWILIO_ACCOUNT_SID')}")
print(f"TWILIO_AUTH_TOKEN: {'*' * 20 if os.getenv('TWILIO_AUTH_TOKEN') else 'NOT SET'}")
print(f"TWILIO_PHONE_NUMBER: {os.getenv('TWILIO_PHONE_NUMBER')}")

# Check student phone numbers
print("\n" + "=" * 50)
print("STUDENT PHONE NUMBERS")
print("=" * 50)

students = Student.objects.all()[:5]  # First 5 students
for student in students:
    print(f"\nStudent: {student.name} ({student.usn})")
    print(f"  Student Phone: {student.student_phone}")
    print(f"  Parent Phone: {student.parent_phone}")

# Test sending SMS
print("\n" + "=" * 50)
print("TESTING SMS SEND")
print("=" * 50)

test_number = "+919964534677"  # Your number
test_message = "Test message from attendance system"

print(f"\nSending test SMS to {test_number}...")
result = send_sms(test_number, test_message)
print(f"Result: {result}")
