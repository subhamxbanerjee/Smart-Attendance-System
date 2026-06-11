import os
import django
from datetime import date, time, datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

# Imports AFTER setup
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from attendance.models import Session
from attendance.admin import SessionAdmin
from django.contrib.messages.storage.fallback import FallbackStorage

try:
    site = AdminSite()
    admin_instance = SessionAdmin(Session, site)
    factory = RequestFactory()
    
    data = {
        'week_start_date': '2023-11-27',
        'days_to_create': ['0', '1'],
        'daily_session_names': "Math | 09:00 | 10:00\nPhysics",
        'first_session_start_time': '09:00',
        'session_duration_minutes': 60,
        'break_minutes_between_sessions': 10,
        'is_active': True,
        '_save': 'Create Sessions'
    }
    
    request = factory.post('/admin/attendance/session/add-week-timetable/', data)
    
    # Mock messages
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)

    print("Simulating POST request...")
    response = admin_instance.add_week_timetable_view(request)
    print(f"Response Status Code: {response.status_code}")
    if response.status_code == 302:
        print("Success: Redirected")
    else:
        print("Response content (if not redirect):")
        # print(response.content.decode()) 

except Exception as e:
    import traceback
    traceback.print_exc()
