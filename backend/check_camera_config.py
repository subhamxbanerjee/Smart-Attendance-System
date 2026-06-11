"""
Check what CAMERA_SOURCE Django is actually using
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.conf import settings

print("=" * 60)
print("Current Django Configuration:")
print("=" * 60)
print(f"CAMERA_SOURCE: {settings.CAMERA_SOURCE}")
print("=" * 60)

if settings.CAMERA_SOURCE == "http://10.145.76.160:8080/video":
    print("✅ Correct! Using the new IP address.")
else:
    print(f"❌ Wrong! Should be: http://10.145.76.160:8080/video")
    print(f"   But is: {settings.CAMERA_SOURCE}")
