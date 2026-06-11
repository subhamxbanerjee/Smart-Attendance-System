from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Student, Notification, PasswordOTP, AdminPasswordOTP, AdminInviteOTP
from .serializers import StudentSerializer, NotificationSerializer, UserSerializer
from attendance.models import AttendanceRecord
from attendance.serializers import AttendanceRecordSerializer
from django.conf import settings
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
import os, random, string


def health(request):
    return JsonResponse({"status": "ok", "app": "accounts"})


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all().order_by('usn')
    serializer_class = StudentSerializer
    # Require auth for all; restrict non-admins to only their own student profile
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user and user.is_authenticated:
            if user.is_staff:
                return qs
            # Non-admins only see their own linked student record
            return qs.filter(user=user)
        # Unauthenticated should see nothing
        return qs.none()

    def perform_update(self, serializer):
        # Only admins may modify student records
        if not (self.request.user and self.request.user.is_staff):
            raise PermissionDenied("Only admins can edit student details")
        serializer.save()


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        student_usn = self.request.query_params.get('usn')
        if student_usn:
            qs = qs.filter(student__usn=student_usn)
        return qs


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def admin_setup(request):
    """Create initial admin if none exists. Accepts username, email, password."""
    if User.objects.filter(is_staff=True).exists():
        return Response({"detail": "Admin already exists"}, status=status.HTTP_400_BAD_REQUEST)
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    if not all([username, email, password]):
        return Response({"detail": "username, email, password required"}, status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.create_superuser(username=username, email=email, password=password)
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def admin_exists(request):
    """Return whether any admin/staff user exists."""
    exists = User.objects.filter(is_staff=True).exists()
    return Response({"exists": exists})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def admin_login(request):
    """Basic admin login placeholder (session auth). For production, switch to JWT."""
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user and user.is_staff:
        return Response({"detail": "login ok", "user": UserSerializer(user).data})


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def create_admin(request):
    """Create an additional admin (staff) account. Body: { username, email, password }"""
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    if not all([username, email, password]):
        return Response({"detail": "username, email, password required"}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=username).exists():
        return Response({"detail": "username already exists"}, status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.create_user(username=username, email=email)
    user.set_password(password)
    user.is_staff = True
    user.save()
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def admin_request_password_otp(request):
    """Request OTP for admin password reset. Body: { email }"""
    email = request.data.get('email')
    if not email:
        return Response({"detail": "email required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(email=email, is_staff=True)
    except User.DoesNotExist:
        # Do not reveal existence
        return Response({"detail": "otp sent"})
    code = ''.join(random.choices(string.digits, k=6))
    AdminPasswordOTP.objects.create(user=user, code=code)
    _send_email(email, "Admin Password Reset OTP", f"Your OTP code is: {code}. It expires in 10 minutes.")
    return Response({"detail": "otp sent"})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def admin_verify_otp_set_password(request):
    """Verify admin OTP and set new password. Body: { email, code, password }"""
    email = request.data.get('email')
    code = request.data.get('code')
    password = request.data.get('password')
    if not all([email, code, password]):
        return Response({"detail": "email, code, password required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(email=email, is_staff=True)
    except User.DoesNotExist:
        return Response({"detail": "invalid request"}, status=status.HTTP_400_BAD_REQUEST)
    otp = AdminPasswordOTP.objects.filter(user=user, code=code, is_used=False).order_by('-created_at').first()
    if not otp:
        return Response({"detail": "invalid otp"}, status=status.HTTP_400_BAD_REQUEST)
    if otp.is_expired():
        return Response({"detail": "otp expired"}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(password)
    user.save()
    otp.is_used = True
    otp.save()
    return Response({"detail": "password set"})
    return Response({"detail": "invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def student_setup_password(request):
    """Create or link a Django user to a student by USN and set password."""
    usn = request.data.get('usn')
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    if not all([usn, username, password]):
        return Response({"detail": "usn, username, password required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        student = Student.objects.get(usn=usn)
    except Student.DoesNotExist:
        return Response({"detail": "student not found"}, status=status.HTTP_404_NOT_FOUND)
    # Create or update user
    user, created = User.objects.get_or_create(username=username, defaults={"email": email or ""})
    user.set_password(password)
    if email:
        user.email = email
    user.save()
    student.user = user
    student.email = email or student.email
    student.save()
    return Response({"detail": "password set", "student": StudentSerializer(student).data})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def student_request_login_otp(request):
    """
    Request an email OTP for login (no password). Body: { usn }
    Sends a 6-digit code to the student's registered email.
    """
    usn = request.data.get('usn')
    if not usn:
        return Response({"detail": "usn required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        student = Student.objects.select_related('user').get(usn=usn)
    except Student.DoesNotExist:
        return Response({"detail": "student not found"}, status=status.HTTP_404_NOT_FOUND)
    if not student.can_login:
        return Response({"detail": "login not permitted for this student"}, status=status.HTTP_403_FORBIDDEN)
    if not student.can_login:
        return Response({"detail": "login not permitted for this student"}, status=status.HTTP_403_FORBIDDEN)
    if not student.can_login:
        return Response({"detail": "login not permitted for this student"}, status=status.HTTP_403_FORBIDDEN)
    if not student.email:
        return Response({"detail": "no email on file for this student"}, status=status.HTTP_400_BAD_REQUEST)
    code = ''.join(random.choices(string.digits, k=6))
    PasswordOTP.objects.create(student=student, code=code)
    _send_email(student.email, "Your Login OTP", f"Your OTP code is: {code}. It expires in 10 minutes.")
    return Response({"detail": "otp sent"})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def student_verify_login_otp(request):
    """
    Verify login OTP and return JWT tokens. Body: { usn, code }
    If the student lacks a linked user, one is created and linked.
    """
    usn = request.data.get('usn')
    code = request.data.get('code')
    if not all([usn, code]):
        return Response({"detail": "usn and code required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        student = Student.objects.select_related('user').get(usn=usn)
    except Student.DoesNotExist:
        return Response({"detail": "student not found"}, status=status.HTTP_404_NOT_FOUND)
    if not student.can_login:
        return Response({"detail": "login not permitted for this student"}, status=status.HTTP_403_FORBIDDEN)
    otp = PasswordOTP.objects.filter(student=student, code=code, is_used=False).order_by('-created_at').first()
    if not otp:
        return Response({"detail": "invalid otp"}, status=status.HTTP_400_BAD_REQUEST)
    if otp.is_expired():
        return Response({"detail": "otp expired"}, status=status.HTTP_400_BAD_REQUEST)
    # Ensure a linked user exists
    if student.user:
        user = student.user
    else:
        base_username = usn.lower()
        username = base_username
        idx = 1
        while User.objects.filter(username=username).exists():
            idx += 1
            username = f"{base_username}{idx}"
        user = User.objects.create(username=username, email=student.email or '')
        student.user = user
        student.save()
    # Mark OTP used and issue tokens
    otp.is_used = True
    otp.save()
    refresh = RefreshToken.for_user(user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "student": StudentSerializer(student).data,
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def student_login_usn_nopass(request):
    """
    Development-only login with USN only (no password/OTP).
    Returns JWT tokens if DEBUG and ALLOW_USN_ONLY_LOGIN are enabled.
    Body: { usn }
    """
    if not (getattr(settings, 'DEBUG', False) and getattr(settings, 'ALLOW_USN_ONLY_LOGIN', False)):
        return Response({"detail": "usn-only login disabled"}, status=status.HTTP_403_FORBIDDEN)
    usn = request.data.get('usn')
    if not usn:
        return Response({"detail": "usn required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        student = Student.objects.select_related('user').get(usn=usn)
    except Student.DoesNotExist:
        return Response({"detail": "student not found"}, status=status.HTTP_404_NOT_FOUND)
    # Ensure a linked user exists
    if not student.can_login:
        return Response({"detail": "login not permitted for this student"}, status=status.HTTP_403_FORBIDDEN)
    if student.user:
        user = student.user
    else:
        base_username = usn.lower()
        username = base_username
        idx = 1
        while User.objects.filter(username=username).exists():
            idx += 1
            username = f"{base_username}{idx}"
        user = User.objects.create(username=username, email=student.email or '')
        student.user = user
        student.save()
    refresh = RefreshToken.for_user(user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "student": StudentSerializer(student).data,
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def student_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if not user:
        return Response({"detail": "invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
    # Verify linked to student
    try:
        student = user.student_profile
    except Exception:
        return Response({"detail": "no linked student"}, status=status.HTTP_400_BAD_REQUEST)
    if not student.can_login:
        return Response({"detail": "login not permitted for this student"}, status=status.HTTP_403_FORBIDDEN)
    return Response({"detail": "login ok", "student": StudentSerializer(student).data})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def student_login_usn(request):
    """
    Login using USN and password. Returns JWT access/refresh tokens.
    Body: { usn, password }
    """
    usn = request.data.get('usn')
    password = request.data.get('password')
    if not usn or not password:
        return Response({"detail": "usn and password required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        student = Student.objects.select_related('user').get(usn=usn)
    except Student.DoesNotExist:
        return Response({"detail": "student not found"}, status=status.HTTP_404_NOT_FOUND)
    if not student.user:
        return Response({"detail": "no account found; please set password via OTP"}, status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(username=student.user.username, password=password)
    if not user:
        return Response({"detail": "invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
    refresh = RefreshToken.for_user(user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "student": StudentSerializer(student).data,
    })


def _send_email(to_email: str, subject: str, message: str) -> bool:
    """Send email with Django or fall back to console print if not configured."""
    if not to_email:
        return False
    try:
        sent = send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'), [to_email])
        if sent:
            return True
    except Exception:
        pass
    # Fallback
    print(f"[EMAIL MOCK] To: {to_email}\nSubject: {subject}\n{message}")
    return True


def _allowed_admin_emails() -> set:
    raw = getattr(settings, 'ALLOWED_ADMIN_EMAILS', None) or os.getenv('ALLOWED_ADMIN_EMAILS', '')
    return set([e.strip().lower() for e in raw.split(',') if e.strip()])


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def admin_invite_request(request):
    """
    Request an OTP to create an admin account if the email is in the allowed list.
    Body: { email }
    """
    email = (request.data.get('email') or '').strip().lower()
    if not email:
        return Response({"detail": "email required"}, status=status.HTTP_400_BAD_REQUEST)
    allowed = _allowed_admin_emails()
    if allowed and email not in allowed:
        return Response({"detail": "email not allowed"}, status=status.HTTP_403_FORBIDDEN)
    code = ''.join(random.choices(string.digits, k=6))
    AdminInviteOTP.objects.create(email=email, code=code)
    _send_email(email, "Admin Invite OTP", f"Your code is: {code}. It expires in 15 minutes.")
    return Response({"detail": "otp sent"})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def admin_invite_verify_create(request):
    """
    Verify the OTP and create an admin (staff) account.
    Body: { email, code, username?, password }
    If username is omitted, it's generated from email local part.
    """
    email = (request.data.get('email') or '').strip().lower()
    code = (request.data.get('code') or '').strip()
    password = request.data.get('password')
    username = (request.data.get('username') or '').strip()
    if not all([email, code, password]):
        return Response({"detail": "email, code, password required"}, status=status.HTTP_400_BAD_REQUEST)
    # Enforce whitelist again
    allowed = _allowed_admin_emails()
    if allowed and email not in allowed:
        return Response({"detail": "email not allowed"}, status=status.HTTP_403_FORBIDDEN)
    otp = AdminInviteOTP.objects.filter(email=email, code=code, is_used=False).order_by('-created_at').first()
    if not otp:
        return Response({"detail": "invalid otp"}, status=status.HTTP_400_BAD_REQUEST)
    if otp.is_expired():
        return Response({"detail": "otp expired"}, status=status.HTTP_400_BAD_REQUEST)
    if not username:
        base = email.split('@')[0]
        candidate = base
        i = 1
        while User.objects.filter(username=candidate).exists():
            i += 1
            candidate = f"{base}{i}"
        username = candidate
    if User.objects.filter(username=username).exists():
        return Response({"detail": "username already exists"}, status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.create_user(username=username, email=email)
    user.set_password(password)
    user.is_staff = True
    user.save()
    otp.is_used = True
    otp.save()
    return Response({"detail": "admin created", "user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def student_request_password_otp(request):
    """
    Request an email OTP for password setup. Body: { usn }
    Generates a 6-digit code, stores it, and emails to student's email.
    """
    usn = request.data.get('usn')
    if not usn:
        return Response({"detail": "usn required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        student = Student.objects.get(usn=usn)
    except Student.DoesNotExist:
        return Response({"detail": "student not found"}, status=status.HTTP_404_NOT_FOUND)
    if not student.email:
        return Response({"detail": "no email on file for this student"}, status=status.HTTP_400_BAD_REQUEST)
    code = ''.join(random.choices(string.digits, k=6))
    PasswordOTP.objects.create(student=student, code=code)
    _send_email(student.email, "Your OTP Code", f"Your OTP code is: {code}. It expires in 10 minutes.")
    return Response({"detail": "otp sent"})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def student_verify_otp_set_password(request):
    """
    Verify OTP and set password. Body: { usn, code, password }
    If student has no linked user, creates one and links.
    """
    usn = request.data.get('usn')
    code = request.data.get('code')
    password = request.data.get('password')
    if not all([usn, code, password]):
        return Response({"detail": "usn, code, password required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        student = Student.objects.select_related('user').get(usn=usn)
    except Student.DoesNotExist:
        return Response({"detail": "student not found"}, status=status.HTTP_404_NOT_FOUND)
    otp = PasswordOTP.objects.filter(student=student, code=code, is_used=False).order_by('-created_at').first()
    if not otp:
        return Response({"detail": "invalid otp"}, status=status.HTTP_400_BAD_REQUEST)
    if otp.is_expired():
        return Response({"detail": "otp expired"}, status=status.HTTP_400_BAD_REQUEST)
    # Ensure user exists
    if student.user:
        user = student.user
    else:
        # Use USN as base username
        base_username = usn.lower()
        username = base_username
        idx = 1
        while User.objects.filter(username=username).exists():
            idx += 1
            username = f"{base_username}{idx}"
        user = User.objects.create(username=username, email=student.email or '')
        student.user = user
        student.save()
    user.set_password(password)
    user.save()
    otp.is_used = True
    otp.save()
    return Response({"detail": "password set", "student": StudentSerializer(student).data})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def student_attendance_history(request):
    """Return attendance for the requesting student, or for any USN if admin.
    Non-admin users cannot request other students' data.
    """
    requested_usn = request.query_params.get('usn')
    user = request.user
    # Admins may specify any USN
    if user.is_staff:
        usn = requested_usn
    else:
        # For students, always force to their own USN
        if hasattr(user, 'student_profile'):
            usn = user.student_profile.usn
        else:
            return Response({"detail": "no linked student profile"}, status=status.HTTP_400_BAD_REQUEST)
    if not usn:
        return Response({"detail": "usn required"}, status=status.HTTP_400_BAD_REQUEST)
    records = AttendanceRecord.objects.select_related('student', 'session').filter(student__usn=usn).order_by('-timestamp')
    return Response(AttendanceRecordSerializer(records, many=True).data)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def upload_student_photo(request):
    """Upload a photo or video for a student. Videos are processed into frames."""
    print(f"[UPLOAD] Received upload request. Data keys: {request.data.keys()}, Files keys: {request.FILES.keys()}")
    usn = request.POST.get('usn') or request.data.get('usn')
    file = request.FILES.get('photo')
    
    if file:
        print(f"[UPLOAD] File name: {file.name}, Size: {file.size}, ContentType: {file.content_type}")

    if not usn or not file:
        print("[UPLOAD] Missing USN or file")
        return Response({"detail": "usn and photo/video file are required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        student = Student.objects.get(usn=usn)
    except Student.DoesNotExist:
        return Response({"detail": "student not found"}, status=status.HTTP_404_NOT_FOUND)
    
    base_dir = os.path.join(settings.MEDIA_ROOT, 'student_photos', usn)
    os.makedirs(base_dir, exist_ok=True)

    # Check if video
    filename = file.name.lower()
    is_video = filename.endswith(('.mp4', '.avi', '.mov', '.mkv'))

    if not is_video:
        return Response({"detail": "Only video files (mp4, avi, mov, mkv) are allowed."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        import cv2
        import tempfile
        import shutil
        import time
    except ImportError:
        return Response({"detail": "OpenCV not installed. Cannot process video."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    # Clear existing photos for this student to avoid mixing old and new data
    try:
        # Delete old frame records from database
        from .models import StudentFrame
        StudentFrame.objects.filter(student=student).delete()
        
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)
        os.makedirs(base_dir, exist_ok=True)
        
        # Save video temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            for chunk in file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        
        cap = cv2.VideoCapture(tmp_path)
        try:
            if not cap.isOpened():
                raise Exception("Could not open video file")

            count = 0
            saved_count = 0
            print(f"[UPLOAD] Starting frame extraction from {tmp_path}")
            while True:
                ret, frame = cap.read()
                if not ret:
                    print(f"[UPLOAD] End of video reached. Total frames read: {count}")
                    break
                # Save every 5th frame, up to 20 frames
                if count % 5 == 0 and saved_count < 20:
                    frame_name = f"frame_{int(time.time())}_{saved_count}.jpg"
                    frame_path = os.path.join(base_dir, frame_name)
                    cv2.imwrite(frame_path, frame)
                    
                    # Save frame record to database
                    StudentFrame.objects.create(
                        student=student,
                        image_path=f'student_photos/{usn}/{frame_name}',
                        frame_number=saved_count
                    )
                    saved_count += 1
                count += 1
                if saved_count >= 20:
                    print("[UPLOAD] Reached max 20 frames limit")
                    break
            print(f"[UPLOAD] Extraction complete. Saved {saved_count} frames.")
        finally:
            cap.release()
            print("[UPLOAD] Video capture released")
        
        # Update student photo folder if not set
        rel_folder = f'student_photos/{usn}'
        student.photo_folder = rel_folder
        student.save()

        # AUTOMATICALLY BUILD ENCODINGS So the system learns the new face immediately
        try:
            print("[UPLOAD] Triggering automatic encoding rebuild...")
            from face_recognition_app.encodings import build_encodings, save_encodings
            encodings_path = os.path.join(settings.BASE_DIR, 'face_recognition_app', 'data', 'encodings.pkl')
            enc_map, processed = build_encodings(settings.MEDIA_ROOT)
            save_encodings(encodings_path, enc_map)
            print(f"[UPLOAD] Encodings rebuilt. Processed {processed} images. Map size: {len(enc_map)}")
        except Exception as enc_err:
            print(f"[UPLOAD WARNING] Failed to rebuild encodings: {enc_err}")
        
        return Response({"detail": f"Processed video: extracted {saved_count} frames. Face scanning complete.", "path": rel_folder})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[UPLOAD ERROR] {str(e)}")
        return Response({"detail": f"Error processing video: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            print(f"[UPLOAD] Attempting to delete temp file: {tmp_path}")
            # Robust deletion for Windows
            for i in range(10): # Increased retries
                try:
                    os.remove(tmp_path)
                    print("[UPLOAD] Temp file deleted successfully")
                    break
                except PermissionError:
                    print(f"[UPLOAD] File locked, retrying deletion ({i+1}/10)...")
                    time.sleep(0.5)
                except Exception as e:
                    print(f"[CLEANUP ERROR] Failed to delete temp file: {e}")
                    break


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def list_student_photos(request):
    """List uploaded photos for a student. Query: ?usn=USN"""
    usn = request.query_params.get('usn')
    if not usn:
        return Response({"detail": "usn required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        _ = Student.objects.get(usn=usn)
    except Student.DoesNotExist:
        return Response({"detail": "student not found"}, status=status.HTTP_404_NOT_FOUND)
    base_dir = os.path.join(settings.MEDIA_ROOT, 'student_photos', usn)
    if not os.path.isdir(base_dir):
        return Response([])
    items = []
    for name in os.listdir(base_dir):
        fp = os.path.join(base_dir, name)
        if os.path.isfile(fp):
            items.append({
                "filename": name,
                "url": settings.MEDIA_URL + f"student_photos/{usn}/" + name,
                "size": os.path.getsize(fp)
            })
    return Response(items)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def delete_student_photo(request):
    """Delete a specific student photo. Body: { usn, filename }"""
    usn = request.data.get('usn')
    filename = request.data.get('filename')
    if not usn or not filename:
        return Response({"detail": "usn and filename required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        _ = Student.objects.get(usn=usn)
    except Student.DoesNotExist:
        return Response({"detail": "student not found"}, status=status.HTTP_404_NOT_FOUND)
    base_dir = os.path.join(settings.MEDIA_ROOT, 'student_photos', usn)
    target_path = os.path.normpath(os.path.join(base_dir, filename))
    # Ensure target_path is under base_dir to avoid path traversal
    if not target_path.startswith(os.path.abspath(base_dir)):
        return Response({"detail": "invalid path"}, status=status.HTTP_400_BAD_REQUEST)
    if not os.path.isfile(target_path):
        return Response({"detail": "file not found"}, status=status.HTTP_404_NOT_FOUND)
    try:
        os.remove(target_path)
        # Also remove from in-memory encodings if present (requires rebuild usually, but good practice)
    except Exception as e:
        return Response({"detail": f"failed to delete: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response({"detail": "deleted"})
