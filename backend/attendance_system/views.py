from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from accounts.models import Student


def index(request: HttpRequest) -> HttpResponse:
    has_students = Student.objects.exists()
    context = {"has_students": has_students}
    return render(request, "index.html", context)


def admin_portal(request: HttpRequest) -> HttpResponse:
    return render(request, "admin_dashboard.html")


def student_portal(request: HttpRequest) -> HttpResponse:
    return render(request, "student_portal.html")
