from django.contrib import admin
from .models import Student, Notification


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("usn", "name", "student_phone", "parent_phone", "email")
    search_fields = ("usn", "name", "student_phone", "parent_phone", "email")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("student", "title", "created_at", "is_read")
    search_fields = ("student__usn", "title", "message")
    list_filter = ("is_read", "created_at")

# Register your models here.
