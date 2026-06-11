from rest_framework import serializers
from django.contrib.auth.models import User
from django.conf import settings
from .models import Student, Notification
import os


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff"]


class StudentSerializer(serializers.ModelSerializer):
    photo_latest_url = serializers.SerializerMethodField()
    class Meta:
        model = Student
        fields = [
            "id",
            "usn",
            "name",
            "email",
            "student_phone",
            "parent_phone",
            "photo_folder",
            "photo_latest_url",
            "can_login",
            "user",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_photo_latest_url(self, obj):
        # Returns the most recently modified file's URL under student's photo folder
        try:
            if not obj.photo_folder:
                return None
            base_dir = os.path.join(settings.MEDIA_ROOT, obj.photo_folder)
            if not os.path.isdir(base_dir):
                return None
            files = [f for f in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, f))]
            if not files:
                return None
            files.sort(key=lambda f: os.path.getmtime(os.path.join(base_dir, f)), reverse=True)
            rel_path = f"{obj.photo_folder}/{files[0]}"
            return settings.MEDIA_URL + rel_path
        except Exception:
            return None


class NotificationSerializer(serializers.ModelSerializer):
    student_usn = serializers.CharField(source="student.usn", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "student", "student_usn", "title", "message", "created_at", "is_read"]
        read_only_fields = ["created_at"]
