import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.conf import settings
from face_recognition_app.encodings import load_encodings
import pickle

ENCODINGS_PATH = os.path.join(settings.BASE_DIR, 'face_recognition_app', 'data', 'encodings.pkl')

print("=" * 60)
print("CHECKING FACE ENCODINGS")
print("=" * 60)

print(f"\nEncodings file path: {ENCODINGS_PATH}")
print(f"File exists: {os.path.exists(ENCODINGS_PATH)}")

if os.path.exists(ENCODINGS_PATH):
    encodings = load_encodings(ENCODINGS_PATH)
    if encodings:
        print(f"\n✓ Encodings loaded successfully!")
        print(f"Number of students with encodings: {len(encodings)}")
        print("\nStudents:")
        for usn, vecs in encodings.items():
            print(f"  - {usn}: {len(vecs)} face encoding(s)")
    else:
        print("\n✗ Encodings file is empty or corrupted")
else:
    print("\n✗ No encodings file found!")
    print("\nYou need to:")
    print("1. Upload student photos via the Admin Dashboard")
    print("2. Click 'Build Encodings' button")
