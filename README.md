# 📸 Smart Attendance System
### AI-powered student attendance tracking using real-time face recognition

[![Django](https://img.shields.io/badge/Django-4.2.7-green?logo=django)](https://djangoproject.com)
[![React](https://img.shields.io/badge/React-18.3.1-blue?logo=react)](https://react.dev)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8.1-red?logo=opencv)](https://opencv.org)
[![DeepFace](https://img.shields.io/badge/DeepFace-0.0.93-purple)](https://github.com/serengil/deepface)
[![Twilio](https://img.shields.io/badge/SMS-Twilio-red?logo=twilio)](https://twilio.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A full-stack web application that automates student attendance using **live face recognition** — no roll calls, no manual entry. Tested live in a real classroom environment with **~50 students using CCTV footage**, with automatic SMS alerts sent to absentees.

> _"Tested in a real classroom. It works."_

---

## 🏆 Real-World Results

| Test Environment | Result |
|-----------------|--------|
| 🏫 Live classroom with CCTV footage | ✅ Successfully tested |
| 👥 Number of students | ~50 students |
| 📱 SMS alerts for absentees | ✅ Working |
| ⚡ Real-time recognition | ✅ Working |

This system was tested in a real college classroom using CCTV footage to track attendance across ~50 students simultaneously. Absentee SMS notifications were successfully delivered via Twilio.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [API Endpoints](#-api-endpoints)
- [Usage Guide](#-usage-guide)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🛠️ Admin Portal
- Secure admin login with email verification
- Add, update, and manage student records
- Upload student photo datasets for face recognition training
- Build and rebuild face encodings from uploaded images
- Start and stop live attendance sessions (supports CCTV / webcam)
- Auto-mark absentees after the attendance window closes
- Send SMS alerts to absent students via Twilio
- View attendance records and reports by session

### 🎓 Student Portal
- Login with USN credentials
- Set up password via email OTP verification
- View personal attendance history
- Access session-wise attendance reports
- Receive SMS notifications for absences

### 🤖 Face Recognition Engine
- Live video capture via OpenCV (webcam or CCTV)
- DeepFace embedding generation with cosine similarity matching
- Handles simultaneous recognition of large groups (tested with ~50 students)
- Attendance window enforcement to prevent late marking
- Secure recognition pipeline with optimized heavy imports
- Automatic fallback and error handling for low-confidence matches

---

## 🛠️ Tech Stack

| Layer              | Technology                                              |
|--------------------|---------------------------------------------------------|
| **Backend**        | Django 4.2.7, Django REST Framework 3.14.0             |
| **Authentication** | djangorestframework-simplejwt, Email OTP               |
| **Frontend**       | React 18.3.1, Vite 5.4.8, React Router DOM 6.26.2     |
| **UI**             | Bootstrap 5.3.3                                        |
| **Database**       | SQLite (dev) / PostgreSQL (production)                 |
| **Face Recognition** | OpenCV 4.8.1, DeepFace 0.0.93, TensorFlow 2.13.1   |
| **SMS**            | Twilio 8.10.0                                          |
| **Email**          | Gmail SMTP via python-decouple                         |
| **Utilities**      | django-cors-headers, Pillow, django-extensions         |

---

## 📂 Project Structure

```
Smart-Attendance-System/
│
├── backend/
│   ├── accounts/              # Student & admin authentication
│   ├── attendance/            # Session and attendance models & APIs
│   ├── face_recognition_app/  # Camera, embedding & recognition logic
│   ├── attendance_system/     # Django project settings & URLs
│   ├── templates/             # Django HTML templates
│   └── manage.py
│
├── frontend/
│   ├── src/
│   │   ├── pages/             # AdminDashboard, StudentPortal, Login pages
│   │   ├── api/               # API client config
│   │   └── App.jsx
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── media/                     # Uploaded photos & captured assets
├── docs/                      # Project notes & documentation
├── requirements.txt           # Python dependencies
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- Node.js 18 or higher
- A webcam or CCTV feed
- Twilio account (for SMS alerts)
- Gmail account (for email OTP)

### 1. Clone the Repository

```bash
git clone https://github.com/subhamxbanerjee/Smart-Attendance-System.git
cd Smart-Attendance-System
```

### 2. Set Up Python Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True

# Database (leave blank to use SQLite)
# DATABASE_URL=postgresql://user:password@localhost:5432/attendance_db

# Twilio SMS
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Gmail SMTP
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
DEFAULT_FROM_EMAIL=Smart Attendance <your_email@gmail.com>
```

> **Gmail tip:** Use an [App Password](https://myaccount.google.com/apppasswords) instead of your regular Gmail password.

### 5. Run Migrations

```bash
cd backend
python manage.py migrate
```

### 6. Start the Backend Server

```bash
python manage.py runserver 0.0.0.0:8000
```

### 7. Start the Frontend

```bash
cd ../frontend
npm install
npm run dev
```

| Service  | URL                           |
|----------|-------------------------------|
| Frontend | http://localhost:5173/         |
| Backend  | http://127.0.0.1:8000/         |
| Admin UI | http://127.0.0.1:8000/admin/   |

---

## 🔐 Environment Variables

| Variable               | Description                               |
|------------------------|-------------------------------------------|
| `SECRET_KEY`           | Django secret key                         |
| `DEBUG`                | `True` for development, `False` for prod  |
| `DATABASE_URL`         | PostgreSQL URL (optional, defaults SQLite)|
| `TWILIO_ACCOUNT_SID`   | Twilio account SID                        |
| `TWILIO_AUTH_TOKEN`    | Twilio auth token                         |
| `TWILIO_PHONE_NUMBER`  | Your Twilio phone number                  |
| `EMAIL_HOST_USER`      | Gmail address for sending OTPs            |
| `EMAIL_HOST_PASSWORD`  | Gmail app password                        |

---

## 🔌 API Endpoints

| Method | Endpoint                      | Description                       |
|--------|-------------------------------|-----------------------------------|
| POST   | `/api/admin/login/`           | Admin authentication              |
| GET    | `/api/admin/students/`        | List all students                 |
| POST   | `/api/admin/students/`        | Add a new student                 |
| POST   | `/api/attendance/start/`      | Start an attendance session       |
| POST   | `/api/attendance/capture/`    | Capture and process a face frame  |
| GET    | `/api/attendance/session/`    | View session attendance records   |
| POST   | `/api/student/login/`         | Student authentication            |
| GET    | `/api/student/attendance/`    | View student attendance history   |

---

## 💡 Usage Guide

### First-Time Setup
1. Start both backend and frontend servers
2. Visit `http://localhost:5173/` and log in as admin (set up via email OTP)
3. Add student records with name, USN, and contact details
4. Upload photos for each student (multiple angles recommended for accuracy)
5. Click **Build Encodings** to train the face recognition model

### Running a Live Attendance Session
1. Connect your webcam or CCTV feed
2. Go to Admin Portal → **Start Attendance Session**
3. The system activates and begins recognizing faces in real time
4. Recognized students are marked **Present** automatically
5. After the attendance window closes, remaining students are marked **Absent**
6. SMS alerts are dispatched to absent students via Twilio instantly

### Student Login
1. Student visits the portal and enters their USN
2. On first login, an OTP is sent to their registered email to set a password
3. After login, they can view full attendance history and session reports

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add: your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

Ideas for contributions:
- Multi-camera / multi-classroom support
- PostgreSQL production deployment guide
- Mobile-responsive frontend improvements
- Attendance analytics and charts dashboard
- Export attendance reports to Excel / PDF

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 👨‍💻 Author

Built by [Subham Banerjee](https://github.com/subhamxbanerjee)

---

> ⭐ Star this repo if it saved your class from manual attendance forever!