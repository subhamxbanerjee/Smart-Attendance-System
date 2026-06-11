from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import health, SessionViewSet, AttendanceRecordViewSet, ClassRoomViewSet

router = DefaultRouter()
router.register(r'sessions', SessionViewSet, basename='session')
router.register(r'records', AttendanceRecordViewSet, basename='attendance-record')
router.register(r'classes', ClassRoomViewSet, basename='class-room')

urlpatterns = [
    path("health/", health, name="attendance-health"),
    path('', include(router.urls)),
]
