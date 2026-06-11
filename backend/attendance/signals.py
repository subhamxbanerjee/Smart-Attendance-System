from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import TimeTable, Session
from datetime import datetime, timedelta

@receiver(post_save, sender=TimeTable)
def sync_timetable_sessions(sender, instance, **kwargs):
    """
    Update future sessions when a TimeTable entry is modified.
    Only updates sessions that are directly linked to this TimeTable entry
    via the 'timetable_entry' field and haven't started yet.
    """
    now = timezone.now()
    
    # Find all future sessions linked to this timetable entry
    # A session is considered "future" if its start_time is greater than or equal to now.
    # However, to avoid disrupting ongoing sessions, we might checking is_active or stricter time.
    # Let's target sessions starting in the future.
    
    future_sessions = Session.objects.filter(
        timetable_entry=instance,
        start_time__gt=now
    )
    
    for session in future_sessions:
        # Update fields to match TimeTable
        # Note: We preserve the date of the session, but update the time
        
        # Calculate new start/end datetimes based on session's existing date
        # and TimeTable's new start/end times
        
        current_date = session.start_time.date()
        
        # Combine date with new times
        # Make them timezone aware
        tz = timezone.get_current_timezone()
        
        new_start_dt = datetime.combine(current_date, instance.start_time)
        new_start_dt = timezone.make_aware(new_start_dt, tz)
        
        new_end_dt = datetime.combine(current_date, instance.end_time)
        new_end_dt = timezone.make_aware(new_end_dt, tz)
        
        # Check if basic info changed
        updated = False
        
        if session.class_room != instance.class_room:
            session.class_room = instance.class_room
            updated = True
            
        if session.start_time != new_start_dt:
            session.start_time = new_start_dt
            updated = True
            
        if session.end_time != new_end_dt:
            session.end_time = new_end_dt
            updated = True
            
        # Optional: Sync name too?
        # Maybe append date like we do in creation? 
        # "Subject - Date"
        # If we change Subject, we should probably update it.
        # Let's try to reconstruct the name format.
        expected_name_base = f"{instance.session_name} - {current_date.strftime('%a %d %b')}"
        # Only update if it looks like an auto-generated name or simply overwrite it
        if session.name != expected_name_base:
            session.name = expected_name_base
            updated = True
            
        if updated:
            session.save()
            print(f"[SYNC] Updated session {session.id} from TimeTable {instance.id}")

    # --- AUTO CREATE FOR TODAY ---
    # If the timetable entry is for TODAY, and no session exists yet, create it.
    current_weekday = now.weekday() # 0=Mon, 6=Sun
    
    if instance.day_of_week == current_weekday:
        # Check if session already exists for today linked to this TT
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        exists = Session.objects.filter(
            timetable_entry=instance,
            start_time__range=(today_start, today_end)
        ).exists()
        
        if not exists:
            # Create it
            tz = timezone.get_current_timezone()
            current_date = now.date()
            
            start_dt = datetime.combine(current_date, instance.start_time)
            start_dt = timezone.make_aware(start_dt, tz)
            
            end_dt = datetime.combine(current_date, instance.end_time)
            end_dt = timezone.make_aware(end_dt, tz)
            
            # Format name
            full_name = f"{instance.session_name} - {current_date.strftime('%a %d %b')}"
            
            new_session = Session.objects.create(
                name=full_name,
                start_time=start_dt,
                end_time=end_dt,
                class_room=instance.class_room,
                is_active=instance.is_active,
                timetable_entry=instance
            )
            print(f"[SYNC] Auto-created session {new_session.id} for today based on TimeTable {instance.id}")
