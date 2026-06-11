
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from attendance.models import Session
from face_recognition_app.views import start_live_for_session
import sys

class Command(BaseCommand):
    help = 'Continuous service to auto-start live recognition for scheduled sessions'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("=== Attendance Automation Service Started ==="))
        self.stdout.write("Checking for sessions starting within the last 5 minutes...")

        while True:
            try:
                now = timezone.now()
                # We look for sessions that started recently (within 5 mins) and are active
                # If a session started 6 mins ago, the window is closed, so we ignore it.
                cutoff = now - timezone.timedelta(minutes=5)
                
                # Filter for candidates
                candidates = Session.objects.filter(
                    is_active=True,
                    start_time__lte=now,
                    start_time__gte=cutoff
                )
                
                if candidates.exists():
                   # self.stdout.write(f"[{now.strftime('%H:%M:%S')}] Found {candidates.count()} candidate session(s).")
                   pass

                for session in candidates:
                    # Attempt to start
                    # start_live_for_session handles:
                    # 1. 5-min window check (redundant but safe)
                    # 2. Camera source check
                    # 3. Thread lock (if already running)
                    
                    success, msg, remaining = start_live_for_session(session.id)
                    
                    if success:
                         self.stdout.write(self.style.SUCCESS(f"[{now.strftime('%H:%M:%S')}] AUTO-START: Started live recognition for '{session.name}' (ID: {session.id})"))
                    else:
                        # Log only if it's NOT "live already running" or "window closed" to avoid spam
                        # Actually "live already running" is good to know but maybe verbose if printed every 30s
                        if "already running" not in msg:
                             self.stdout.write(f"[{now.strftime('%H:%M:%S')}] Skipped '{session.name}': {msg}")

                # Sleep interval
                time.sleep(10)
                
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("Service stopped by user."))
                sys.exit(0)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in service loop: {e}"))
                time.sleep(5)
