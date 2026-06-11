import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.conf import settings
from face_recognition_app.encodings import build_encodings, save_encodings

ENCODINGS_PATH = os.path.join(settings.BASE_DIR, 'face_recognition_app', 'data', 'encodings.pkl')

print("=" * 60)
print("BUILDING FACE ENCODINGS")
print("=" * 60)

print(f"\nMedia root: {settings.MEDIA_ROOT}")
print(f"Looking for photos in: {os.path.join(settings.MEDIA_ROOT, 'student_photos')}")

# Check if directory exists
student_photos_dir = os.path.join(settings.MEDIA_ROOT, 'student_photos')
if not os.path.exists(student_photos_dir):
    print(f"\n✗ ERROR: Directory does not exist!")
    print(f"\nCreating directory: {student_photos_dir}")
    os.makedirs(student_photos_dir, exist_ok=True)
    print("✓ Directory created")
    print("\nPlease upload student photos to this directory:")
    print(f"  {student_photos_dir}\\<USN>\\photo.jpg")
    print("\nExample:")
    print(f"  {student_photos_dir}\\1ks23cm006\\photo1.jpg")
    print(f"  {student_photos_dir}\\1ks23cm006\\photo2.jpg")
else:
    print(f"\n✓ Directory exists")
    
    # List what's in the directory
    print("\nContents:")
    for item in os.listdir(student_photos_dir):
        item_path = os.path.join(student_photos_dir, item)
        if os.path.isdir(item_path):
            photos = [f for f in os.listdir(item_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            print(f"  {item}/: {len(photos)} photo(s)")
    
    # Try to build encodings
    print("\n" + "=" * 60)
    print("Building encodings...")
    print("=" * 60)
    
    try:
        enc_map, processed = build_encodings(settings.MEDIA_ROOT)
        print(f"\n✓ Processed {processed} images")
        print(f"✓ Created encodings for {len(enc_map)} students")
        
        if enc_map:
            save_encodings(ENCODINGS_PATH, enc_map)
            print(f"✓ Saved encodings to: {ENCODINGS_PATH}")
            
            print("\nEncodings created for:")
            for usn, vecs in enc_map.items():
                print(f"  - {usn}: {len(vecs)} encoding(s)")
        else:
            print("\n✗ No encodings created - no photos found or all photos failed")
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
