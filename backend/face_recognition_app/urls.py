from django.urls import path
from . import views
from . import debug_views

urlpatterns = [
    path("health/", views.health, name="face-health"),
    path("build-encodings/", views.build_encodings_api, name="face-build-encodings"),
    path("start/", views.start, name="face-start"),
    path("stop/", views.stop, name="face-stop"),
    path("capture/", views.capture, name="face-capture"),
    path("test-camera/", views.test_camera, name="face-test-camera"),
    path("video_feed/", views.video_feed, name="face-video-feed"),
    path("debug/build-encodings/", debug_views.debug_build_encodings, name="face-debug-build"),
]
