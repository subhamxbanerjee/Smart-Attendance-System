from django import template
from django.utils import timezone
from attendance.models import Session
from datetime import timedelta

register = template.Library()

@register.inclusion_tag('admin/attendance/dashboard_sessions.html')
def show_live_sessions():
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Get all active sessions for today
    sessions = Session.objects.filter(start_time__range=(today_start, today_end)).order_by('start_time')
    
    session_data = []
    for s in sessions:
        # Determine live status matching admin logic
        is_live = False
        if s.is_active and (now - s.start_time) <= timedelta(minutes=5) and (now >= s.start_time):
             is_live = True
        
        session_data.append({
            'obj': s,
            'name': s.name,
            'class_room': s.class_room,
            'start_time': s.start_time,
            'end_time': s.end_time,
            'is_active': s.is_active,
            'is_live': is_live,
            'id': s.id
        })
        
    return {'sessions': session_data}
