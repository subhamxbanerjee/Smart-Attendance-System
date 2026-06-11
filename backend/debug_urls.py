import os
import django
from django.template.loader import render_to_string

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

try:
    # We need a request context for some admin templates, but let's try basic rendering first
    # admin/change_list.html usually requires 'cl' (ChangeList) in context.
    # This might be hard to mock fully, but let's see if it fails on inheritance first.
    
    # We can try to render it with minimal context
    rendered = render_to_string('admin/attendance/session/change_list.html', {'cl': None, 'media': None})
    print("Successfully rendered template (partial)")
except Exception as e:
    print(f"Error rendering template: {e}")
