"""
Management command to clean up old session frames to save disk space.
Deletes image files older than 30 days but keeps the database records.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import os
from django.conf import settings
from attendance.models import SessionFrame

class Command(BaseCommand):
    help = 'Delete session frame images older than 30 days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to keep images (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f"Cleaning up frames older than {cutoff_date.strftime('%Y-%m-%d')} ({days} days)")
        
        # Find old frames that still have an image path
        old_frames = SessionFrame.objects.filter(
            captured_at__lt=cutoff_date
        ).exclude(image_path='')
        
        count = old_frames.count()
        
        if count == 0:
            self.stdout.write("No old frames found to clean up.")
            return

        self.stdout.write(f"Found {count} frames to clean up.")
        
        deleted_files = 0
        updated_records = 0
        
        for frame in old_frames:
            file_path = os.path.join(settings.MEDIA_ROOT, frame.image_path)
            
            if os.path.exists(file_path):
                if not dry_run:
                    try:
                        os.remove(file_path)
                        deleted_files += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error deleting {file_path}: {e}"))
                else:
                    self.stdout.write(f"[DRY RUN] Would delete: {file_path}")
            
            if not dry_run:
                # Clear the path in DB so we know it's deleted
                frame.image_path = ''
                frame.save(update_fields=['image_path'])
                updated_records += 1
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"[DRY RUN] Would delete {count} images."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted {deleted_files} images and updated {updated_records} records."))
            
            # Optional: Try to remove empty session directories
            self._cleanup_empty_dirs()
    
    def _cleanup_empty_dirs(self):
        """Remove empty session directories"""
        frames_root = os.path.join(settings.MEDIA_ROOT, 'session_frames')
        if not os.path.exists(frames_root):
            return
            
        removed_dirs = 0
        for item in os.listdir(frames_root):
            dir_path = os.path.join(frames_root, item)
            if os.path.isdir(dir_path):
                try:
                    # rmdir only works if directory is empty
                    os.rmdir(dir_path)
                    removed_dirs += 1
                except OSError:
                    pass  # Directory not empty
        
        if removed_dirs > 0:
            self.stdout.write(f"Removed {removed_dirs} empty session directories.")
