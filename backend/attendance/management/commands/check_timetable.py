"""
Django management command to check timetable and auto-create sessions.
Run this command every 5 minutes via Windows Task Scheduler.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from attendance.models import TimeTable, Session
import requests
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check timetable and auto-create sessions with live recognition'

    def handle(self, *args, **options):
        now = timezone.now()
        current_day = now.weekday()  # 0=Monday, 6=Sunday
        current_time = now.time()
        
        # Cleanup: Deactivate sessions that have passed their end time
        expired = Session.objects.filter(is_active=True, end_time__lt=now)
        if expired.count() > 0:
            count = expired.update(is_active=False)
            self.stdout.write(self.style.SUCCESS(f"Auto-expired {count} sessions that passed their end time."))
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Checking timetable at {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"Day: {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][current_day]}")
        self.stdout.write(f"{'='*60}\n")
        
        # Get today's active timetable entries
        today_schedule = TimeTable.objects.filter(
            day_of_week=current_day,
            is_active=True
        ).order_by('start_time')
        
        if not today_schedule.exists():
            self.stdout.write(self.style.WARNING(f"No timetable entries found for today."))
            return
        
        self.stdout.write(f"Found {today_schedule.count()} timetable entries for today:")
        for entry in today_schedule:
            self.stdout.write(f"  - {entry}")
        
        sessions_created = 0
        sessions_started = 0
        
        for entry in today_schedule:
            # Create datetime for session start
            start_datetime = datetime.combine(now.date(), entry.start_time)
            start_datetime = timezone.make_aware(start_datetime, timezone.get_current_timezone())
            
            end_datetime = datetime.combine(now.date(), entry.end_time)
            end_datetime = timezone.make_aware(end_datetime, timezone.get_current_timezone())
            
            # Calculate time difference in minutes
            time_diff = (start_datetime - now).total_seconds() / 60
            
            # Check if session should start (within 5-minute window before start time)
            # This allows the command to catch sessions even if it runs a bit late
            if -5 <= time_diff <= 5:
                self.stdout.write(f"\n⏰ Session '{entry.session_name}' should start now!")
                self.stdout.write(f"   Scheduled: {entry.start_time} - {entry.end_time}")
                self.stdout.write(f"   Time difference: {time_diff:.1f} minutes")
                
                # Check if session already created today
                session_name = f"{entry.session_name} - {now.strftime('%a %d %b')}"
                existing = Session.objects.filter(
                    name=session_name,
                    start_time__date=now.date()
                ).first()
                
                if existing:
                    self.stdout.write(self.style.WARNING(f"   ⚠️  Session already exists: {existing.name}"))
                    
                    # Check if we should start live recognition
                    if existing.is_active and time_diff >= -5 and time_diff <= 0:
                        # Session is active and we're at or just past start time
                        success = self.start_live_recognition(existing)
                        if success:
                            sessions_started += 1
                else:
                    # Create new session
                    session = Session.objects.create(
                        name=session_name,
                        start_time=start_datetime,
                        end_time=end_datetime,
                        class_room=entry.class_room,
                        is_active=True
                    )
                    sessions_created += 1
                    self.stdout.write(self.style.SUCCESS(f"   ✅ Created session: {session.name}"))
                    self.stdout.write(f"      ID: {session.id}")
                    self.stdout.write(f"      Start: {session.start_time}")
                    self.stdout.write(f"      End: {session.end_time}")
                    
                    # Auto-start live recognition
                    success = self.start_live_recognition(session)
                    if success:
                        sessions_started += 1
        
        # Summary
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS(f"✅ Sessions created: {sessions_created}"))
        self.stdout.write(self.style.SUCCESS(f"🎥 Live recognition started: {sessions_started}"))
        self.stdout.write(f"{'='*60}\n")
    
    def start_live_recognition(self, session):
        """
        Trigger live face recognition for the given session.
        Makes API call to the face recognition start endpoint.
        """
        try:
            self.stdout.write(f"\n   🎥 Starting live recognition for session {session.id}...")
            
            # Make API call to start live recognition
            # Note: This requires an admin JWT token or session authentication
            url = 'http://127.0.0.1:8000/api/face/start/'
            data = {'session_id': session.id}
            
            # For now, we'll import and call the function directly
            # In production, you might use a service account with JWT token
            from face_recognition_app.views import start as start_view
            from rest_framework.request import Request
            from django.test.client import RequestFactory
            from django.contrib.auth import get_user_model
            
            # Create a fake request
            factory = RequestFactory()
            request = factory.post('/api/face/start/', data)
            
            # Get admin user (or create service account)
            User = get_user_model()
            admin_user = User.objects.filter(is_superuser=True).first()
            
            if not admin_user:
                self.stdout.write(self.style.ERROR(f"   ❌ No admin user found to start live recognition"))
                return False
            
            request.user = admin_user
            
            # Convert to DRF Request
            from rest_framework.request import Request as DRFRequest
            drf_request = DRFRequest(request)
            drf_request._full_data = data
            
            # Call the view
            response = start_view(drf_request)
            
            if response.status_code in [200, 201]:
                self.stdout.write(self.style.SUCCESS(f"   ✅ Live recognition started successfully"))
                return True
            else:
                self.stdout.write(self.style.ERROR(f"   ❌ Failed to start live recognition: {response.data}"))
                return False
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error starting live recognition: {str(e)}"))
            logger.error(f"Error starting live recognition for session {session.id}: {str(e)}")
            return False
