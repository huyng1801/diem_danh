#!/usr/bin/env python
"""
Seed Data Script for THCS Nguyễn Đình Chiểu - Face-ID Attendance System

This script initializes the database with real student data for academic year 2025-2026:
- Admin and Teacher users
- Academic years
- Classrooms from Grade 6-9
- All students from the official school records
- Sample attendance records

Usage:
    python seed_data.py
"""

import os
import sys
from datetime import datetime, timedelta, date
from random import randint, choice

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.academic_year import AcademicYear
from app.models.class_room import ClassRoom
from app.models.student import Student
from app.models.attendance import Attendance
from app.models.attendance_log import AttendanceLog

# Import real student data
try:
    from student_data_2025_2026 import STUDENTS_DATA
except ImportError:
    # Fallback data if the file doesn't exist
    STUDENTS_DATA = {
        "6A1": [("080214005381", "Đặng Hồ Quốc An", "08/07/2014", "Nam")],
        "6A2": [("080214005143", "Dương Nguyễn Tấn An", "02/05/2014", "Nam")],
    }


# ============================================================================
# THCS NGUYỄN ĐÌNH CHIỂU - ACADEMIC YEAR 2025-2026 DATA
# ============================================================================

# Teacher names at the school
TEACHERS = [
    {"name": "Nguyễn Thị Huế", "email": "hue.nguyen@thcs.edu.vn"},
    {"name": "Trần Văn Tùng", "email": "tung.tran@thcs.edu.vn"},
    {"name": "Phạm Thị Hoa", "email": "hoa.pham@thcs.edu.vn"},
    {"name": "Hoàng Văn Minh", "email": "minh.hoang@thcs.edu.vn"},
    {"name": "Lê Thị Mai", "email": "mai.le@thcs.edu.vn"},
    {"name": "Vũ Văn Toàn", "email": "toan.vu@thcs.edu.vn"},
    {"name": "Đỗ Thị Linh", "email": "linh.do@thcs.edu.vn"},
    {"name": "Bùi Văn Nam", "email": "nam.bui@thcs.edu.vn"},
    {"name": "Cao Thị Ngọc", "email": "ngoc.cao@thcs.edu.vn"},
    {"name": "Đinh Văn Hùng", "email": "hung.dinh@thcs.edu.vn"},
    {"name": "Ngô Thị Lan", "email": "lan.ngo@thcs.edu.vn"},
    {"name": "Phan Văn Dũng", "email": "dung.phan@thcs.edu.vn"},
    {"name": "Lưu Thị Hồng", "email": "hong.luu@thcs.edu.vn"},
    {"name": "Trịnh Văn Sơn", "email": "son.trinh@thcs.edu.vn"},
    {"name": "Đặng Thị Thu", "email": "thu.dang@thcs.edu.vn"},
]

# Academic years
ACADEMIC_YEARS = [
    {"year": "2023-2024", "start": date(2023, 9, 1), "end": date(2024, 5, 31), "active": False},
    {"year": "2024-2025", "start": date(2024, 9, 1), "end": date(2025, 5, 31), "active": False},
    {"year": "2025-2026", "start": date(2025, 9, 1), "end": date(2026, 5, 31), "active": True},
]

# Real classroom data from THCS Nguyễn Đình Chiểu
CLASSROOMS = {
    "6": ["6A1", "6A2", "6A3", "6A4", "6A5", "6A6", "6A7", "6A8", "6A9"],
    "7": ["7A1", "7A2", "7A3", "7A4", "7A5", "7A6", "7A7", "7A8", "7A9"],
    "8": ["8A1", "8A2", "8A3", "8A4", "8A5", "8A6", "8A7", "8A8", "8A9"],
    "9": ["9A1", "9A2", "9A3", "9A4", "9A5", "9A6", "9A7"],
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_student_code(grade: str, class_index: int, student_index: int) -> str:
    """Generate unique student code: e.g., 6A1001, 7B2015"""
    return f"{grade}{chr(65 + (class_index // 3))}{(class_index % 3) + 1}{1000 + student_index}"


def create_users(app):
    """Create admin and teacher users"""
    print("\n📝 Creating Users...")
    
    # Create admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User()
        admin.username = 'admin'
        admin.email = 'admin@thcs.edu.vn'
        admin.full_name = 'Quản Trị Viên'
        admin.role = 'admin'
        admin.phone = '0903000000'
        admin.set_password('Admin@12345')
        admin.is_active = True
        db.session.add(admin)
        print("  ✓ Admin user created")
    
    # Create teacher users
    for i, teacher_data in enumerate(TEACHERS):
        teacher = User.query.filter_by(username=teacher_data['email'].split('@')[0]).first()
        if not teacher:
            teacher = User()
            teacher.username = teacher_data['email'].split('@')[0]
            teacher.email = teacher_data['email']
            teacher.full_name = teacher_data['name']
            teacher.role = 'teacher'
            teacher.phone = f"090{i:07d}"
            teacher.set_password('Teacher@12345')
            teacher.is_active = True
            db.session.add(teacher)
    
    db.session.commit()
    print(f"  ✓ {len(TEACHERS)} teacher users created")


def create_academic_years(app):
    """Create academic years"""
    print("\n📚 Creating Academic Years...")
    
    for year_data in ACADEMIC_YEARS:
        year = AcademicYear.query.filter_by(year=year_data['year']).first()
        if not year:
            year = AcademicYear()
            year.year = year_data['year']
            year.start_date = year_data['start']
            year.end_date = year_data['end']
            year.is_active = year_data['active']
            db.session.add(year)
            print(f"  ✓ Academic year {year_data['year']} created")
    
    db.session.commit()


def create_classrooms(app):
    """Create classrooms for the active academic year"""
    print("\n🏫 Creating Classrooms...")
    
    # Get the active academic year
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    if not active_year:
        print("  ⚠ No active academic year found!")
        return
    
    teachers = User.query.filter_by(role='teacher').all()
    teacher_index = 0
    
    for grade, class_names in CLASSROOMS.items():
        for class_name in class_names:
            classroom = ClassRoom.query.filter_by(
                class_name=class_name,
                academic_year_id=active_year.id
            ).first()
            
            if not classroom:
                classroom = ClassRoom()
                classroom.class_name = class_name
                classroom.grade = grade
                classroom.room_number = f"Phòng {randint(101, 209)}"
                classroom.academic_year_id = active_year.id
                
                # Assign head teacher
                if teacher_index < len(teachers):
                    classroom.head_teacher_id = teachers[teacher_index].id
                    classroom.head_teacher = teachers[teacher_index].full_name
                    teacher_index += 1
                
                classroom.max_student = 45
                db.session.add(classroom)
                print(f"  ✓ Classroom {class_name} created (Room {classroom.room_number})")
    
    db.session.commit()


def create_students(app):
    """Create students for all classrooms using real data"""
    print("\n👨‍🎓 Creating Students...")
    
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    if not active_year:
        print("  ⚠ No active academic year found!")
        return
    
    total_students = 0
    
    for class_name, student_list in STUDENTS_DATA.items():
        classroom = ClassRoom.query.filter_by(
            class_name=class_name,
            academic_year_id=active_year.id
        ).first()
        
        if not classroom:
            print(f"  ⚠ Classroom {class_name} not found, skipping students")
            continue
            
        for student_code, full_name, birth_date_str, gender in student_list:
            # Check if student already exists
            if not Student.query.filter_by(student_code=student_code).first():
                student = Student()
                student.student_code = student_code
                student.full_name = full_name
                student.gender = gender
                
                # Parse birth date
                try:
                    day, month, year = birth_date_str.split('/')
                    student.date_of_birth = date(int(year), int(month), int(day))
                except:
                    # Default birth date if parsing fails
                    student.date_of_birth = date(2014, 1, 1)
                
                student.address = f"Số {randint(1, 999)}, Phường ..., Quận ..., TP HCM"
                student.phone = f"090{randint(1000000, 9999999)}"
                student.parent_name = f"Phụ huynh {full_name.split()[-1]}"
                student.parent_phone = f"098{randint(1000000, 9999999)}"
                
                student.classroom_id = classroom.id
                student.academic_year_id = active_year.id
                student.is_active = True
                student.face_recognition_enabled = choice([True, True, True, False])  # 75% enabled
                student.face_images_count = randint(0, 5) if student.face_recognition_enabled else 0
                
                db.session.add(student)
                total_students += 1
        
        # Update classroom student count
        classroom.update_student_count()
        print(f"  ✓ {len(student_list)} students added to {class_name}")
    
    db.session.commit()
    print(f"  ✓ Total {total_students} students created from real data")


def create_attendance_records(app):
    """Create sample attendance records for the last 30 days"""
    print("\n✅ Creating Attendance Records...")
    
    active_year = AcademicYear.query.filter_by(is_active=True).first()
    classrooms = ClassRoom.query.filter_by(academic_year_id=active_year.id).all()
    
    today = datetime.now().date()
    start_date = today - timedelta(days=30)
    
    total_records = 0
    
    # Create attendance records for last 30 days (weekdays only)
    current_date = start_date
    
    while current_date <= today:
        # Skip weekends (Saturday=5, Sunday=6)
        if current_date.weekday() < 5:
            
            for classroom in classrooms:
                students = Student.query.filter_by(classroom_id=classroom.id).all()
                
                # Create 2 sessions per day (morning and afternoon)
                for session_type in ['morning', 'afternoon']:
                    # Create AttendanceLog entry
                    log = AttendanceLog()
                    log.classroom_id = classroom.id
                    log.session_date = current_date
                    log.session_type = session_type
                    log.start_time = datetime.combine(current_date, 
                        choice([datetime.strptime("07:00", "%H:%M").time(),
                                datetime.strptime("13:00", "%H:%M").time()]))
                    log.end_time = log.start_time.replace(hour=log.start_time.hour + 1)
                    
                    db.session.add(log)
                    db.session.flush()
                    
                    # Create attendance records for each student
                    for student in students:
                        # 90% attendance rate (realistic)
                        if randint(1, 100) <= 90:
                            attendance = Attendance()
                            attendance.student_id = student.id
                            attendance.classroom_id = classroom.id
                            attendance.attendance_log_id = log.id
                            attendance.status = 'present'
                            
                            # Set check-in time
                            check_in_hour = 7 if session_type == 'morning' else 13
                            check_in_minute = randint(0, 20)
                            attendance.check_in_time = datetime.combine(
                                current_date,
                                datetime.strptime(f"{check_in_hour:02d}:{check_in_minute:02d}", "%H:%M").time()
                            )
                            
                            # Late if after 10 minutes
                            if check_in_minute > 10:
                                attendance.is_late = True
                            
                            attendance.confidence_score = round(randint(85, 100) / 100, 2)
                            attendance.recognition_method = choice(['face_recognition', 'manual'])
                            
                            db.session.add(attendance)
                            total_records += 1
                        else:
                            # Absent - set check_in_time to session start time
                            attendance = Attendance()
                            attendance.student_id = student.id
                            attendance.classroom_id = classroom.id
                            attendance.attendance_log_id = log.id
                            attendance.status = 'absent'
                            attendance.check_in_time = datetime.combine(
                                current_date,
                                datetime.strptime(f"{check_in_hour:02d}:00", "%H:%M").time()
                            )
                            attendance.recognition_method = 'system'
                            db.session.add(attendance)
                            total_records += 1
        
        current_date += timedelta(days=1)
    
    db.session.commit()
    print(f"  ✓ {total_records} attendance records created")




# ============================================================================
# MAIN EXECUTION
# ============================================================================

def seed_database():
    """Main function to seed the database"""
    
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*70)
        print("🌱 SEEDING DATABASE FOR THCS NGUYỄN ĐÌNH CHIỂU - FACE-ID SYSTEM")
        print("="*70)
        
        try:
            # Drop all tables (CAUTION: Only for development!)
            # Uncomment only if you want to reset the database
            # db.drop_all()
            # print("\n🗑️  Database tables dropped")
            
            # Create all tables
            db.create_all()
            print("\n📊 Database tables created/verified")
            
            # Seed data in order
            create_users(app)
            create_academic_years(app)
            create_classrooms(app)
            create_students(app)
            # create_attendance_records(app)  # Không seed lịch sử điểm danh
            
            # Summary statistics
            print("\n" + "="*70)
            print("📈 DATABASE SEEDING COMPLETE!")
            print("="*70)
            
            admin_count = User.query.filter_by(role='admin').count()
            teacher_count = User.query.filter_by(role='teacher').count()
            year_count = AcademicYear.query.count()
            classroom_count = ClassRoom.query.count()
            student_count = Student.query.count()
            attendance_count = Attendance.query.count()
            
            print(f"\n📊 Summary Statistics:")
            print(f"  👤 Admin users: {admin_count}")
            print(f"  🏫 Teachers: {teacher_count}")
            print(f"  📚 Academic years: {year_count}")
            print(f"  🎓 Classrooms: {classroom_count}")
            print(f"  👨‍🎓 Students: {student_count}")
            print(f"  ✅ Attendance records: {attendance_count}")
            
            print(f"\n🔐 Default Credentials:")
            print(f"  Admin Username: admin")
            print(f"  Admin Password: Admin@12345")
            print(f"  Teacher Password: Teacher@12345 (for all teachers)")
            
            print("\n✨ Database ready for testing!")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
