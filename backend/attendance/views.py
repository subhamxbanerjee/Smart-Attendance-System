from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Session, AttendanceRecord, ClassRoom
from accounts.models import Student
from .serializers import SessionSerializer, AttendanceRecordSerializer, ClassRoomSerializer
from .utils import send_sms
from datetime import datetime

def health(request):
    return JsonResponse({"status": "ok", "app": "attendance"})


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all().order_by('-start_time')
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Auto-expire sessions that have passed their end time
        now = timezone.now()
        # Filter for active sessions with an end_time in the past
        expired_sessions = Session.objects.filter(is_active=True, end_time__lt=now)
        if expired_sessions.exists():
            expired_sessions.update(is_active=False)
        
        # Stick to TimeTable-only sessions as requested
        return super().get_queryset().filter(timetable_entry__isnull=False)

    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def start(self, request):
        name = request.data.get('name') or f"Session {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        session = Session.objects.create(name=name, start_time=timezone.now(), is_active=True)
        return Response(SessionSerializer(session).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def stop(self, request, pk=None):
        try:
            session = self.get_object()
        except Exception:
            return Response({"detail": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
        session.is_active = False
        session.end_time = timezone.now()
        session.save()
        return Response(SessionSerializer(session).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def mark_absent(self, request, pk=None):
        """Mark all students not marked present in this session as absent."""
        session = self.get_object()
        students_present_ids = AttendanceRecord.objects.filter(session=session, status='present').values_list('student_id', flat=True)
        missing = Student.objects.exclude(id__in=students_present_ids)
        created = 0
        for student in missing:
            obj, was_created = AttendanceRecord.objects.get_or_create(
                student=student,
                session=session,
                defaults={"status": "absent"}
            )
            if was_created:
                created += 1
                # Send SMS alerts to student and parent
                timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
                message = f"Your child is absent for today’s class at {timestamp} in {session.name}."
                try:
                    if student.student_phone:
                        send_sms(student.student_phone, message)
                    if student.parent_phone:
                        send_sms(student.parent_phone, message)
                except Exception:
                    # Fail silently if SMS fails; production could log this
                    pass
        return Response({"marked_absent": created, "session": SessionSerializer(session).data})

    @action(detail=False, methods=['post'], permission_classes=[IsAdmin], url_path='bulk_create_week')
    def bulk_create_week(self, request):
        """
        Create a week's timetable of sessions.
        Expected JSON body:
        {
          "week_start_date": "2025-09-29",       # ISO date (local)
          "days_to_create": [0,1,2,3,4],         # 0..6 offsets from start date
          "session_name_prefix": "Class",
          "sessions_per_day": 6,
          "first_session_start_time": "09:00",  # HH:MM 24h
          "session_duration_minutes": 60,
          "break_minutes_between_sessions": 10,
          "is_active": true
        }
        """
        data = request.data
        try:
            week_start_date_str = data.get('week_start_date')
            if not week_start_date_str:
                return Response({"detail": "week_start_date is required (YYYY-MM-DD)"}, status=status.HTTP_400_BAD_REQUEST)
            week_start_date = datetime.strptime(week_start_date_str, "%Y-%m-%d").date()

            days_to_create = data.get('days_to_create', [0,1,2,3,4])
            days_to_create = [int(d) for d in days_to_create]

            session_name_prefix = data.get('session_name_prefix', 'Class')
            sessions_per_day = int(data.get('sessions_per_day', 6))

            t_str = data.get('first_session_start_time', '09:00')
            try:
                t_hour, t_min = [int(x) for x in t_str.split(':', 1)]
            except Exception:
                return Response({"detail": "first_session_start_time must be HH:MM"}, status=status.HTTP_400_BAD_REQUEST)
            first_session_time = datetime(2000,1,1, t_hour, t_min).time()

            session_duration_minutes = int(data.get('session_duration_minutes', 60))
            break_minutes_between_sessions = int(data.get('break_minutes_between_sessions', 10))
            is_active = bool(data.get('is_active', True))
            class_room_id = data.get('class_room_id')
            class_room = None
            if class_room_id is not None:
                try:
                    class_room = ClassRoom.objects.get(pk=class_room_id)
                except ClassRoom.DoesNotExist:
                    return Response({"detail": "class_room not found"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Invalid input: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        created = 0
        tz = timezone.get_current_timezone()
        for weekday_index in days_to_create:
            day_date = week_start_date + timedelta(days=weekday_index)
            start_dt = datetime.combine(day_date, first_session_time)
            start_dt = timezone.make_aware(start_dt, tz)
            for i in range(max(0, sessions_per_day)):
                end_dt = start_dt + timedelta(minutes=session_duration_minutes)
                name = f"{session_name_prefix} - {day_date.strftime('%a %d %b')} - Slot {i+1}"
                Session.objects.create(
                    name=name,
                    start_time=start_dt,
                    end_time=end_dt,
                    is_active=is_active,
                    class_room=class_room,
                )
                created += 1
                start_dt = end_dt + timedelta(minutes=break_minutes_between_sessions)

        return Response({"created": created}, status=status.HTTP_201_CREATED)


class ClassRoomViewSet(viewsets.ModelViewSet):
    queryset = ClassRoom.objects.all().order_by('name', 'section')
    serializer_class = ClassRoomSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.select_related('student', 'session').all().order_by('-timestamp')
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        session_id = self.request.query_params.get('session')
        usn = self.request.query_params.get('usn')
        if session_id:
            qs = qs.filter(session_id=session_id)
        if usn:
            qs = qs.filter(student__usn=usn)
        return qs

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_present(self, request):
        """Mark a student present for a session. Body: {usn, session_id, recognized_image_path?}"""
        usn = request.data.get('usn')
        session_id = request.data.get('session_id')
        img_path = request.data.get('recognized_image_path', '')
        if not usn or not session_id:
            return Response({"detail": "usn and session_id required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            student = Student.objects.get(usn=usn)
            session = Session.objects.get(id=session_id)
        except (Student.DoesNotExist, Session.DoesNotExist):
            return Response({"detail": "student or session not found"}, status=status.HTTP_404_NOT_FOUND)
        # Enforce 5-minute window from session start
        now = timezone.now()
        if (now - session.start_time) > timedelta(minutes=5):
            return Response({"detail": "attendance window closed (5 minutes passed)"}, status=status.HTTP_400_BAD_REQUEST)
        record, _ = AttendanceRecord.objects.update_or_create(
            student=student,
            session=session,
            defaults={"status": "present", "recognized_image_path": img_path}
        )
        return Response(AttendanceRecordSerializer(record).data)
