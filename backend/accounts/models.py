from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Student(models.Model):
    usn = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    student_phone = models.CharField(max_length=15)
    parent_phone = models.CharField(max_length=15)
    photo_folder = models.CharField(max_length=255, help_text="Relative path under media/student_photos/<USN>/", blank=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_profile')
    can_login = models.BooleanField(default=False, help_text="Admin-granted permission. If true, student can log in.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.usn} - {self.name}"


class StudentFrame(models.Model):
    """Tracks individual frames extracted from student videos"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='frames')
    image_path = models.CharField(max_length=500, help_text="Relative path from MEDIA_ROOT")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    frame_number = models.IntegerField(help_text="Frame sequence number from video")
    
    class Meta:
        ordering = ['student', 'frame_number']
    
    def __str__(self):
        return f"{self.student.usn} - Frame {self.frame_number}"


class Notification(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} -> {self.student.usn}"

class PasswordOTP(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='password_otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self) -> bool:
        return (timezone.now() - self.created_at).total_seconds() > 600  # 10 minutes

    def __str__(self):
        return f"OTP for {self.student.usn} at {self.created_at} ({'used' if self.is_used else 'active'})"

class AdminPasswordOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_password_otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self) -> bool:
        return (timezone.now() - self.created_at).total_seconds() > 600  # 10 minutes

    def __str__(self):
        return f"Admin OTP for {self.user.username} at {self.created_at} ({'used' if self.is_used else 'active'})"

class AdminInviteOTP(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self) -> bool:
        return (timezone.now() - self.created_at).total_seconds() > 900  # 15 minutes

    def __str__(self):
        return f"Admin Invite OTP for {self.email} at {self.created_at} ({'used' if self.is_used else 'active'})"

# Create your models here.
