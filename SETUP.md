# HƯỚNG DẪN TRIỂN KHAI HỆ THỐNG ĐIỂM DANH HỌC SINH - FACE-ID

## 📌 CÔNG NGHỆ SỬ DỤNG

| Thành phần          | Công nghệ                                   | Phiên bản |
|----------------------|---------------------------------------------|------------|
| Backend              | Python Flask                               | 3.x        |
| Database             | PostgreSQL                                 | 13+        |
| ORM                  | SQLAlchemy                                 | 2.0+       |
| UI Framework         | Bootstrap + Font Awesome                   | Latest     |
| Face Recognition     | OpenCV + Face_recognition (trained)        | Latest     |
| Image Upload         | Pillow, Werkzeug                           | Latest     |
| Authentication       | PyJWT, bcrypt                              | Latest     |
| Export               | openpyxl (Excel), reportlab (PDF)          | Latest     |


---

## 📁 CẤU TRÚC THƯ MỤC DỰ ÁN

```
diemdanh_hocsinh_thcs/
│
├── README.md
├── SETUP.md
├── requirements.txt
├── config.py
├── run.py
├── .env
├── .gitignore
│
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── academic_year.py
│   │   ├── class_room.py
│   │   ├── student.py
│   │   ├── student_image.py
│   │   ├── attendance.py
│   │   ├── attendance_log.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── academic_year.py
│   │   ├── classroom.py
│   │   ├── student.py
│   │   ├── attendance.py
│   │   ├── report.py
│   │   ├── admin.py
│   │   └── api.py (for face recognition API)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── academic_year_service.py
│   │   ├── classroom_service.py
│   │   ├── student_service.py
│   │   ├── attendance_service.py
│   │   ├── face_recognition_service.py
│   │   ├── report_service.py
│   │   └── excel_export_service.py
│   │
│   ├── templates/
│   │   ├── base.html (Material Design layout)
│   │   ├── layout.html
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   ├── admin/
│   │   │   ├── dashboard.html
│   │   │   ├── user_management.html
│   │   │   ├── academic_year.html
│   │   ├── classroom/
│   │   │   ├── list.html
│   │   │   ├── form.html
│   │   │   └── detail.html
│   │   ├── student/
│   │   │   ├── list.html
│   │   │   ├── form.html
│   │   │   ├── detail.html
│   │   │   ├── image_upload.html
│   │   │   └── image_gallery.html
│   │   ├── attendance/
│   │   │   ├── camera.html (real-time face recognition)
│   │   │   ├── view_result.html
│   │   │   ├── edit_result.html
│   │   │   └── history.html
│   │   └── report/
│   │       ├── attendance_report.html
│   │
│   ├── static/
│   │   ├── css/
│   │   │   ├── style.css
│   │   │   ├
│   │   │   └── 
│   │   ├── js/
│   │   │   ├── main.js
│   │   │   ├── face_recognition.js
│   │   │   ├── chart.js
│   │   │   └── form_validation.js
│   │   └── images/
│   │       └── logo.png
│   │
│   ├── uploads/
│   │   ├── student_faces/ (uploaded face images)
│   │   ├── attendance_snapshots/ (captured during attendance)
│   │   └── trained_models/ (trained face recognition models)
│   │
│   └── utils/
│       ├── __init__.py
│       ├── decorators.py (role-based access control)
│       ├── validators.py
│       ├── helpers.py
│       ├── constants.py
│       └── email_helper.py
│
├── ml_models/
│   ├── __init__.py
│   ├── face_trainer.py (train face recognition model)
│   ├── face_detector.py (detect and recognize faces)
│   └── models/ (stored trained models)
│
├── migrations/ (Alembic for database migrations)
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
└── tests/
    ├── __init__.py
    ├── test_user.py
    ├── test_student.py
    ├── test_attendance.py
        └── test_face_recognition.py

├── seed_data.py (🌱 Seed database with sample data)
├── manage_seed.py (🌱 Advanced seed management CLI tool)
└── SEED_DATA.md (📋 Comprehensive seed data documentation)
```