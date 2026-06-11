import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

# Imports MUST happen after setup
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from attendance.models import Session
from attendance.admin import SessionAdmin
from attendance.forms import WeekTimetableForm

print("Checking Form Import...")
try:
    f = WeekTimetableForm()
    print("Form instantiated successfully.")
except Exception as e:
    print(f"Form Error: {e}")

print("Checking Admin View...")
try:
    site = AdminSite()
    admin_instance = SessionAdmin(Session, site)
    factory = RequestFactory()
    request = factory.get('/admin/attendance/session/')
    
    # changelist_view expects an authenticated user, usually.
    # But let's see if it crashes before that.
    response = admin_instance.changelist_view(request)
    print(f"Response Status Code: {response.status_code}")
    print("View executed successfully.")
except Exception as e:
    import traceback
    traceback.print_exc()
