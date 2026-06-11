# Student Attendance System

A professional full-stack attendance application that uses face recognition to automate student presence tracking.

## Overview

This system combines a Django backend and a React frontend to deliver a reliable student attendance workflow with:
- Admin management
- Student self-service portal
- Real-time face recognition
- SMS and email notifications
- Session and attendance history tracking

## Key Features

### Admin Portal
- Create and manage students
- Upload student photo datasets for recognition
- Start and stop live attendance sessions
- Build face encodings from uploaded images
- Auto-mark absentees after the attendance window
- Send absence notifications via Twilio
- View attendance records by session

### Student Portal
- Login with USN
- Email OTP password setup
- View attendance history
- Access attendance reports for current and past sessions

### Face Recognition
- Live video capture via OpenCV
- DeepFace embedding generation
- Cosine similarity matching for face recognition
- Secure recognition pipeline with delayed heavy imports
- Attendance window enforcement for accurate marking

## Tech Stack

- **Backend**: Django 4.2.7, Django REST Framework 3.14.0
- **Authentication**: djangorestframework-simplejwt
- **Frontend**: React 18.3.1, Vite 5.4.8, React Router DOM 6.26.2, Bootstrap 5.3.3
- **Database**: SQLite (default), compatible with PostgreSQL
- **Face Recognition**: OpenCV 4.8.1.78, DeepFace 0.0.93, TensorFlow 2.13.1, NumPy 1.24.3
- **SMS**: Twilio 8.10.0
- **Email & Configuration**: python-decouple
- **Utilities**: django-cors-headers, Pillow, django-extensions, requests

## Repository Structure

- `backend/` – Django project and core APIs
  - `accounts/` – student and admin authentication
  - `attendance/` – session and attendance models
  - `face_recognition_app/` – camera, embedding, and recognition logic
- `frontend/` – React interface for admin and student portals
- `media/` – uploaded photos and captured attendance assets
- `requirements.txt` – Python dependencies

## Setup Instructions

### 1. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with values like:

```env
SECRET_KEY=your-secret-key
DEBUG=True

# Optional database override
# DATABASE_URL=postgres://user:pass@localhost:5432/attendance

# Twilio settings
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Attendance System <your_email@example.com>
```

### 3. Run Django Migrations

```bash
cd backend
python manage.py migrate
```

### 4. Start the Backend Server

```bash
python manage.py runserver 0.0.0.0:8000
```

### 5. Start the Frontend

```bash
cd ../frontend
npm install
npm run dev
```

## Usage

- Access the backend admin: `http://127.0.0.1:8000/admin/`
- Access the frontend app: `http://localhost:5173/`
- Upload student photos and build encodings before running live attendance
- Use the student portal to login with USN and review attendance

## Help

If you need help, use the project admin interface and API documentation to verify configuration. For local development issues, check:
- Backend logs for Django server errors
- Frontend console for React warnings
- `media/` directory for saved student assets

If you want help with setup or debugging, review the environment configuration and ensure the backend and frontend are both running.

# Student Attendance System

A comprehensive full-stack web application for managing student attendance using face recognition technology.

## Features

### Admin Portal
- Admin authentication with email verification
- Student management (Add/Update student details)
- Photo database management for face recognition
- Live attendance system with camera integration
- SMS alerts for absent students
- Attendance reports and analytics

### Student Portal
- Student login with USN and password
- Password setup via email verification
- View attendance history
- View notifications from admin

### Face Recognition System
- Real-time face detection and recognition
- Automatic attendance marking
- 5-minute timeout for absent marking
- Photo comparison using OpenCV and face_recognition

## Tech Stack

- **Backend**: Django REST Framework
- **Frontend**: React.js
- **Database**: PostgreSQL
- **Face Recognition**: OpenCV + face_recognition library
- **SMS Integration**: Twilio API
- **Authentication**: JWT tokens

## Installation

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up PostgreSQL database
4. Configure environment variables in `.env` file
5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Environment Variables

Create a `.env` file in the root directory with:

```
SECRET_KEY=your_django_secret_key
DEBUG=True
DATABASE_URL=postgresql://username:password@localhost:5432/attendance_db
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_phone
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_email_password
```

## Usage

1. Start the application
2. If no students exist, admin login will be available
3. Create admin credentials via email if not exists
4. Add student details and photos
5. Start live attendance sessions
6. Students can login to view their attendance

## API Endpoints

- `/api/admin/login/` - Admin authentication
- `/api/admin/students/` - Student management
- `/api/attendance/start/` - Start attendance session
- `/api/attendance/capture/` - Capture and process attendance
- `/api/student/login/` - Student authentication
- `/api/student/attendance/` - View attendance history

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
"# smart-attendance" 
"# smart-attendance" 
