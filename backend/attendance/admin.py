from django.contrib import admin
from .models import Session, AttendanceRecord, TimeTable, SystemConfiguration
from face_recognition_app.views import start_live_for_session
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .forms import WeekTimetableForm


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("name", "get_day_name", "start_time", "end_time", "class_room", "is_active", "live_status")
    list_filter = ("is_active", "start_time")
    search_fields = ("name",)
    # actions = ["add_week_timetable_action"] # Removed

    # Use custom changelist template to add an "Add Week Timetable" button
    # change_list_template = "admin/attendance/session/change_list.html" # Removed

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Only show sessions created from TimeTable
        return qs.filter(timetable_entry__isnull=False)

    def live_status(self, obj):
        now = timezone.now()
        # Consider live if active and within 5 minutes of start_time
        if obj.is_active and (now - obj.start_time) <= timedelta(minutes=5):
            return True
        return False
    live_status.boolean = True
    live_status.short_description = "Live Recognition"

    def get_day_name(self, obj):
        return obj.start_time.strftime("%A")
    get_day_name.short_description = "Day"
    get_day_name.admin_order_field = "start_time"

    # Removed custom URLs and views for adding week timetable/start live manually from admin



@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "status", "timestamp")
    list_filter = ("status", "timestamp")
    search_fields = ("student__usn", "session__name")


@admin.register(TimeTable)
class TimeTableAdmin(admin.ModelAdmin):
    list_display = ("get_day_name", "session_name", "start_time", "end_time", "class_room", "is_active")
    list_filter = ("day_of_week", "is_active", "class_room")
    search_fields = ("session_name",)
    ordering = ("day_of_week", "start_time")
    
    def get_day_name(self, obj):
        return obj.get_day_of_week_display()
    get_day_name.short_description = "Day"
    get_day_name.admin_order_field = "day_of_week"

# Register your models here.

@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "description")
    search_fields = ("key", "description")
