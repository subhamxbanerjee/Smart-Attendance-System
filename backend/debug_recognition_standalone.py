
import os
import django
import cv2
import numpy as np

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.conf import settings
from face_recognition_app.views import _recognize_and_mark, ensure_encodings_loaded, KNOWN_ENCODINGS
from face_recognition_app.views import KNOWN_ENCODINGS as VIEW_ENCODINGS

def test_recognition():
    print("--- DEBUGGING RECOGNITION LOGIC ---")
    
    # 1. Load Encodings
    ensure_encodings_loaded()
    
    # Check if encodings loaded
    from face_recognition_app import views
    encs = views.KNOWN_ENCODINGS
    print(f"Loaded Encodings for {len(encs)} students: {list(encs.keys())}")
    
    if not encs:
        print("❌ CRITICAL: No encodings loaded. Test cannot proceed.")
        return

    # 2. Load Test Image (One of the uploaded frames)
    # Using 1ks23cm006 (from previous ls output)
    test_img_path = os.path.join(settings.MEDIA_ROOT, 'student_photos', '1ks23cm006', 'frame_1764049619_0.jpg')
    print(f"Testing with image: {test_img_path}")
    
    if not os.path.exists(test_img_path):
        print(f"❌ File not found: {test_img_path}")
        return

    frame = cv2.imread(test_img_path)
    if frame is None:
        print("❌ Failed to load image with cv2")
        return

    print("Image loaded. Running recognition...")
    
    # 3. Run Recognition (mark_db=False to avoid database writes)
    recognized = _recognize_and_mark(session_id=0, frame_bgr=frame, mark_db=False)
    
    print(f"\nResult: Recognized USNs: {recognized}")
    
    if '1ks23cm006' in recognized:
        print("✅ SUCCESS: Self-match confirmed.")
    else:
        print("❌ FAILURE: Could not match image to its own encoding.")

if __name__ == "__main__":
    test_recognition()
