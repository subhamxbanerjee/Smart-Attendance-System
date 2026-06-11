# Student Attendance System – Project Notes

## Overview
- **Purpose**: End-to-end system to manage student attendance with live face recognition, session management, and notifications.
- **Stack**: Django + Django REST Framework (backend), React + Vite (frontend), DeepFace + OpenCV (face recognition).
- **Key Features**:
  - Admin portal to manage students, photos, sessions, and attendance.
  - Live face recognition from camera to mark attendance automatically.
  - 5-minute attendance window per session (auto-stop).
  - Dev option for student USN-only login; production-ready OTP/password flows.
  - Student portal to view personal attendance analytics.

## Architecture
- **Backend** (`backend/`)
  - Django project: `attendance_system/`
  - Apps: `accounts/`, `attendance/`, `face_recognition_app/`
  - REST API via DRF; JWT via SimpleJWT.
  - Media storage under `MEDIA_ROOT` for student photos and session frames.
- **Frontend** (`frontend/`)
  - React (Vite) SPA.
  - Pages: `AdminLogin.jsx`, `AdminDashboard.jsx`, `StudentLogin.jsx`, `StudentPortal.jsx`, `SetupPassword.jsx`.
  - API client sets Authorization header with JWT.

## Backend Modules
- `accounts/`
  - Models: `Student`, `Notification`, OTP models (admin, student).
    - `Student` fields: `usn`, `name`, `email`, `student_phone`, `parent_phone`, `photo_folder`, `user`, `can_login`, timestamps.
  - Views:
    - Admin: `admin_setup`, `admin_exists`, `admin_login`, `create_admin`, OTP request/verify for admin invite and password reset.
    - Student login flows:
      - `student_login_usn_nopass` (dev-only; requires `DEBUG=True` and `ALLOW_USN_ONLY_LOGIN=True`).
      - `student_request_login_otp`, `student_verify_login_otp` (email OTP login; no password).
      - `student_setup_password`, `student_login` (username/password), `student_login_usn` (USN/password).
      - All login flows enforce `Student.can_login == True` and student must be registered.
    - Student data access:
      - `StudentViewSet`: non-admins can only read their own record; admins can CRUD.
      - `student_attendance_history`: admins may query any USN; students always see only their own.
    - Photo management (admin-only): `upload_student_photo`, `list_student_photos`, `delete_student_photo`.
  - Serializers: `StudentSerializer` exposes `can_login`, `photo_latest_url`.
  - URLs: registered under `/api/accounts/`.

- `attendance/`
  - Models: `Session`, `AttendanceRecord` (referenced in code).
  - The live flow uses `Session.is_active`, `Session.start_time`, and creates/updates `AttendanceRecord`.

- `face_recognition_app/`
  - Encodings: `encodings.py` with `build_encodings`, `save_encodings`, `load_encodings`.
  - Views: `build_encodings_api`, `start`, `stop`, `capture`.
  - Live loop: `_live_loop(session_id)` in `face_recognition_app/views.py`.
    - Auto-stops after 5 minutes from `Session.start_time` or if session becomes inactive.
    - Processes recognition every 3rd frame.
    - Saves recognition frames to `MEDIA_ROOT/session_frames/session_<session_id>/` as JPEGs.
    - Takes 10 recognition frames per session start:
      - Marks recognized USNs present via `_recognize_and_mark()`.
      - After 10 recognition frames, marks all remaining registered students as absent and stops.
  - Recognition: `_recognize_and_mark(session_id, frame)`
    - Computes DeepFace embedding (enforce_detection=False).
    - Compares to known encodings via cosine distance (threshold ~0.3) and marks present within the active 5-minute window.

## Frontend Modules
- `AdminLogin.jsx` – Admin JWT login (and OTP password reset support).
- `AdminDashboard.jsx` – Students management, sessions control, attendance view, photo manager.
  - Add student form.
  - Edit student details inline (Edit/Save/Cancel) – PATCH via `/api/accounts/students/:id/`.
  - Toggle `Can Login` per student.
  - Upload/list/delete student photos.
  - Start session → requests camera permission, builds encodings, starts live recognition.
  - Auto-refresh attendance while live recognition runs.
- `StudentLogin.jsx` – Student USN-only dev login (calls `/student/login-usn-nopass/`).
- `StudentPortal.jsx` – Loads own attendance automatically on mount and shows analytics (Total, Present, Absent, %), grouped by session.

## Authentication & Permissions
- **Admin**: JWT via `/api/accounts/token/`. Backend uses `IsAdminUser` for privileged endpoints.
- **Student**:
  - Dev: USN-only login (must have `can_login=True`, `DEBUG=True`, `ALLOW_USN_ONLY_LOGIN=True`).
  - OTP login (email): request/verify endpoints issue JWT; still requires `can_login=True`.
  - Password-based flows available if needed (setup via OTP or admin-assisted), but currently the UI favors USN-only for dev.
- **Data protection**:
  - Students can only read their own profile and attendance.
  - Admins can manage all students and sessions.

## Face Recognition Flow
1. Admin clicks Start session in `AdminDashboard.jsx`.
2. Frontend requests camera permission, calls `build_encodings_api`, then `start` live.
3. Backend live loop reads frames from camera, runs recognition every 3rd frame.
4. Up to 10 recognition frames are processed; present students are marked.
5. After 10 frames, all remaining students are marked absent; loop stops.
6. Hard cutoff at 5 minutes from session start enforces the attendance window.

## Media Storage
- Student photos: `MEDIA_ROOT/student_photos/<USN>/...`
- Session frames: `MEDIA_ROOT/session_frames/session_<session_id>/frame_XX_<ts>.jpg`

## Environment & Settings
- File: `.env`
  - `DEBUG=True`
  - `SECRET_KEY=...`
  - `ALLOW_USN_ONLY_LOGIN=True` (dev-only USN login)
  - `ALLOWED_ADMIN_EMAILS=...` (admin invite whitelist)
  - Twilio placeholders present for SMS integration.
- `backend/attendance_system/settings.py` reads the above and sets `MEDIA_ROOT`, etc.

## Notable Endpoints (selection)
- Accounts
  - `POST /api/accounts/token/` – Admin JWT login
  - `GET /api/accounts/students/` – List students (admin), self-only for students
  - `PATCH /api/accounts/students/:id/` – Edit student (admin)
  - `POST /api/accounts/student/upload-photo/` – Upload photo (admin)
  - `GET /api/accounts/student/photos/?usn=...` – List photos (admin)
  - `POST /api/accounts/student/delete-photo/` – Delete photo (admin)
  - `POST /api/accounts/student/login-usn-nopass/` – Dev-only USN login (requires `can_login=True`)
  - `GET /api/accounts/student/attendance-history/` – Self-only records for students; any USN for admin
- Face Recognition
  - `POST /api/face/build_encodings/`
  - `POST /api/face/start/` – Start live loop (admin)
  - `POST /api/face/stop/` – Stop live loop (admin)
  - `POST /api/face/capture/` – Single-shot recognition via image upload

## Dependencies (key)
- Backend
  - Django
  - djangorestframework
  - djangorestframework-simplejwt
  - deepface
  - opencv-python (cv2)
  - numpy
  - Twilio (planned/optional; based on `.env` placeholders)
- Frontend
  - React
  - Vite
  - Bootstrap (via CSS classes)

## Development Notes
- Start backend: `python manage.py runserver 0.0.0.0:8001`
- Start frontend: `npm run dev` (default http://localhost:5175)
- Ensure encodings are rebuilt after photo changes.
- In development, USN-only login requires backend restart after changing `.env`.

## Security Considerations
- USN-only login is gated by `DEBUG` and `ALLOW_USN_ONLY_LOGIN` and `can_login=True` per student.
- Production should use OTP or password-based flows only.
- Admin-only endpoints are protected by `IsAdminUser`.

## How to Export This to PDF
- Option 1: Open this file in the IDE preview and use “Print to PDF”.
- Option 2: Copy to a Markdown viewer that supports export (e.g., VSCode Markdown: Ctrl+Shift+V → print).
- Option 3: I can generate an HTML version for cleaner print styles on request.
