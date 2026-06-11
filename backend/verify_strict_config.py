
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from attendance.models import SystemConfiguration
from face_recognition_app.views import get_camera_source
from django.conf import settings

def test_strict_config():
    print("--- Testing Strict Camera Configuration (No Fallback) ---")
    
    # 1. Clear DB Config
    SystemConfiguration.objects.filter(key="camera_source").delete()
    
    # 2. Check .env (should be commented out now, so empty or not set)
    env_source = getattr(settings, 'CAMERA_SOURCE', '')
    print(f"Settings CAMERA_SOURCE: '{env_source}'")
    
    # 3. Resolve
    resolved = get_camera_source()
    print(f"Resolved Source: {resolved}")
    
    if resolved is None:
        print("PASS: System strictly returns None when no DB config exists.")
    else:
        print(f"FAIL: System fell back to '{resolved}' (Should be None)")

    print("\n--- Testing DB Config Still Works ---")
    config, _ = SystemConfiguration.objects.get_or_create(key="camera_source")
    config.value = "rtsp://test/stream"
    config.save()
    
    resolved = get_camera_source()
    print(f"DB Value: {config.value}")
    print(f"Resolved Source: {resolved}")
    
    if resolved == "rtsp://test/stream":
         print("PASS: DB Config is respected.")
    else:
         print("FAIL: DB Config ignored.")

    # Cleanup
    SystemConfiguration.objects.filter(key="camera_source").delete()
    print("\nTest Complete.")

if __name__ == "__main__":
    test_strict_config()
