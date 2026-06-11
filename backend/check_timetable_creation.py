
import os
import django
from django.utils import timezone
from datetime import datetime, time, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from attendance.models import TimeTable, Session, ClassRoom

def test_auto_create():
    print("Testing TimeTable -> Session Auto-Creation...")
    
    # 1. Setup
    cr1, _ = ClassRoom.objects.get_or_create(name="Room 101")
    
    # Check what day it is
    now = timezone.now()
    current_weekday = now.weekday()
    print(f"Current Weekday: {current_weekday}")
    
    # Create TimeTable entry for TODAY
    tt = TimeTable.objects.create(
        day_of_week=current_weekday,
        session_name="AutoCreate Test",
        start_time=time(14, 0), # Future time ideally, but logical check handles ranges
        end_time=time(15, 0),
        class_room=cr1,
        is_active=True
    )
    print(f"Created TimeTable: {tt}")
    
    # 2. Check if Session was created
    # Name should be "AutoCreate Test - Date"
    expected_name_base = f"AutoCreate Test - {now.strftime('%a %d %b')}"
    print(f"Looking for session: {expected_name_base}")
    
    exists = Session.objects.filter(name=expected_name_base).exists()
    
    if exists:
        print("SUCCESS: Session was auto-created!")
        # Cleanup
        s = Session.objects.get(name=expected_name_base)
        s.delete()
        tt.delete()
    else:
        print("FAILED: Session was NOT created.")
        tt.delete()
        exit(1)

if __name__ == "__main__":
    test_auto_create()
