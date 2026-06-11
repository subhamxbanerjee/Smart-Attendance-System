from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    health,
    StudentViewSet,
    NotificationViewSet,
    admin_setup,
    admin_login,
    create_admin,
    student_setup_password,
    student_login,
    student_login_usn,
    student_login_usn_nopass,
    student_attendance_history,
    upload_student_photo,
    list_student_photos,
    delete_student_photo,
    admin_exists,
    student_request_password_otp,
    student_verify_otp_set_password,
    student_request_login_otp,
    student_verify_login_otp,
    admin_request_password_otp,
    admin_verify_otp_set_password,
    admin_invite_request,
    admin_invite_verify_create,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path("health/", health, name="accounts-health"),
    path('admin/setup/', admin_setup, name='admin-setup'),
    path('admin/exists/', admin_exists, name='admin-exists'),
    path('admin/login/', admin_login, name='admin-login'),
    path('admin/create/', create_admin, name='admin-create'),
    path('admin/request-otp/', admin_request_password_otp, name='admin-request-otp'),
    path('admin/verify-otp/', admin_verify_otp_set_password, name='admin-verify-otp'),
    path('admin/invite-request/', admin_invite_request, name='admin-invite-request'),
    path('admin/invite-verify/', admin_invite_verify_create, name='admin-invite-verify'),
    path('student/setup-password/', student_setup_password, name='student-setup-password'),
    path('student/login/', student_login, name='student-login'),
    path('student/login-usn/', student_login_usn, name='student-login-usn'),
    path('student/login-usn-nopass/', student_login_usn_nopass, name='student-login-usn-nopass'),
    path('student/attendance-history/', student_attendance_history, name='student-attendance-history'),
    path('student/upload-photo/', upload_student_photo, name='student-upload-photo'),
    path('student/photos/', list_student_photos, name='student-list-photos'),
    path('student/delete-photo/', delete_student_photo, name='student-delete-photo'),
    path('student/request-otp/', student_request_password_otp, name='student-request-otp'),
    path('student/verify-otp/', student_verify_otp_set_password, name='student-verify-otp'),
    path('student/login/request-otp/', student_request_login_otp, name='student-login-request-otp'),
    path('student/login/verify-otp/', student_verify_login_otp, name='student-login-verify-otp'),
    # JWT auth
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
