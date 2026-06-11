from django.db import models
from django.utils import timezone
from accounts.models import Student


class ClassRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    section = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.name}{(' - ' + self.section) if self.section else ''}"


class TimeTable(models.Model):
    """Defines recurring class schedule for each day of the week"""
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    day_of_week = models.IntegerField(choices=DAY_CHOICES, help_text="Day of the week")
    session_name = models.CharField(max_length=100, help_text="Subject or session name (e.g., Math, Physics)")
    start_time = models.TimeField(help_text="Session start time (e.g., 09:00)")
    end_time = models.TimeField(help_text="Session end time (e.g., 10:00)")
    class_room = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='timetable_entries')
    is_active = models.BooleanField(default=True, help_text="Enable/disable this timetable entry")
    
    class Meta:
        ordering = ['day_of_week', 'start_time']
        verbose_name = 'TimeTable Entry'
        verbose_name_plural = 'TimeTable'
    
    def __str__(self):
        day_name = self.get_day_of_week_display()
        cls = f" [{self.class_room}]" if self.class_room else ""
        return f"{day_name}: {self.session_name} ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}){cls}"


class Session(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    class_room = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    timetable_entry = models.ForeignKey(TimeTable, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_sessions')

    def __str__(self):
        cls = f" [{self.class_room}]" if self.class_room else ""
        return f"{self.name}{cls} ({'Active' if self.is_active else 'Ended'})"


class AttendanceRecord(models.Model):
    STATUS_CHOICES = (
        ("present", "Present"),
        ("absent", "Absent"),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    recognized_image_path = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('student', 'session')

    def __str__(self):
        return f"{self.student.usn} - {self.session.name} - {self.status}"


class SessionFrame(models.Model):
    """Tracks frames captured during live attendance sessions"""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='captured_frames')
    image_path = models.CharField(max_length=500, help_text="Relative path from MEDIA_ROOT")
    captured_at = models.DateTimeField(auto_now_add=True)
    frame_number = models.IntegerField(help_text="Frame sequence during session")
    recognized_students = models.ManyToManyField(Student, blank=True, related_name='recognized_in_frames')
    
    class Meta:
        ordering = ['session', 'frame_number']
    
    def __str__(self):
        return f"Session {self.session.id} - Frame {self.frame_number}"

# Create your models here.

class SystemConfiguration(models.Model):
    """
    Store system-wide keys and values (e.g., camera source url).
    """
    key = models.CharField(max_length=50, unique=True, help_text="Configuration key (e.g., camera_source)")
    value = models.TextField(help_text="Configuration value")
    description = models.TextField(blank=True, help_text="Description of what this setting does")

    def __str__(self):
        return f"{self.key}: {self.value}"
