from rest_framework import serializers
from accounts.serializers import StudentSerializer
from .models import Session, AttendanceRecord, ClassRoom


class ClassRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassRoom
        fields = ["id", "name", "section"]


class SessionSerializer(serializers.ModelSerializer):
    class_room = ClassRoomSerializer(read_only=True)
    class_room_id = serializers.PrimaryKeyRelatedField(
        queryset=ClassRoom.objects.all(), source="class_room", write_only=True, required=False, allow_null=True
    )
    class Meta:
        model = Session
        fields = ["id", "name", "start_time", "end_time", "is_active", "class_room", "class_room_id"]


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_detail = StudentSerializer(source="student", read_only=True)
    session_name = serializers.CharField(source="session.name", read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = [
            "id",
            "student",
            "student_detail",
            "session",
            "session_name",
            "status",
            "timestamp",
            "recognized_image_path",
        ]
        read_only_fields = ["timestamp"]
