#!/usr/bin/env python
"""
Advanced Seed Data Manager - THCS Nguyễn Đình Chiểu Face-ID System

Features:
- Seed complete database with realistic data
- Clear/reset database
- Generate reports
- Export sample data
- Manage seed state

Usage:
    python manage_seed.py seed          # Seed database
    python manage_seed.py clear         # Clear all data
    python manage_seed.py report        # Generate seed report
    python manage_seed.py export        # Export seed data to CSV
"""

import os
import sys
import csv
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.academic_year import AcademicYear
from app.models.class_room import ClassRoom
from app.models.student import Student
from app.models.attendance import Attendance
from app.models.attendance_log import AttendanceLog


class SeedManager:
    """Manage database seeding operations"""
    
    def __init__(self):
        self.app = create_app()
        self.export_dir = Path(self.app.root_path) / 'exports'
        self.export_dir.mkdir(exist_ok=True)
    
    def seed(self, verbose=True):
        """Run complete seeding process"""
        with self.app.app_context():
            if verbose:
                print("\n" + "="*70)
                print("🌱 SEEDING DATABASE - THCS NGUYỄN ĐÌNH CHIỂU")
                print("="*70)
            
            try:
                db.create_all()
                
                from seed_data import (
                    create_users, create_academic_years, create_classrooms,
                    create_students, create_attendance_records,
                )
                
                create_users(self.app)
                create_academic_years(self.app)
                create_classrooms(self.app)
                create_students(self.app)
                create_attendance_records(self.app)
                
                if verbose:
                    self._print_summary()
                
                return True
            except Exception as e:
                print(f"\n❌ Seeding failed: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    def clear(self, confirm=True):
        """Clear all data from database"""
        if confirm:
            response = input("\n⚠️  WARNING: This will delete all data! Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Cancelled")
                return False
        
        with self.app.app_context():
            print("\n🗑️  Clearing database...")
            try:
                db.drop_all()
                print("✅ Database cleared successfully")
                return True
            except Exception as e:
                print(f"❌ Clear failed: {e}")
                return False
    
    def reset(self, confirm=True):
        """Reset database (clear + seed)"""
        if self.clear(confirm):
            return self.seed()
        return False
    
    def report(self):
        """Generate database seed report"""
        with self.app.app_context():
            print("\n" + "="*70)
            print("📊 DATABASE SEED REPORT")
            print("="*70)
            
            try:
                self._print_summary()
                self._print_detailed_report()
                return True
            except Exception as e:
                print(f"❌ Report generation failed: {e}")
                return False
    
    def export(self):
        """Export seed data to CSV files"""
        with self.app.app_context():
            print("\n📤 Exporting seed data...")
            
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Export users
                self._export_users(timestamp)
                
                # Export academic years
                self._export_academic_years(timestamp)
                
                # Export classrooms
                self._export_classrooms(timestamp)
                
                # Export students
                self._export_students(timestamp)
                
                # Export attendance
                self._export_attendance(timestamp)
                
                print(f"\n✅ Export complete! Files saved to: {self.export_dir}/")
                return True
            except Exception as e:
                print(f"❌ Export failed: {e}")
                return False
    
    def _print_summary(self):
        """Print database summary statistics"""
        print(f"\n📈 Summary Statistics:")
        
        admin_count = User.query.filter_by(role='admin').count()
        teacher_count = User.query.filter_by(role='teacher').count()
        year_count = AcademicYear.query.count()
        classroom_count = ClassRoom.query.count()
        student_count = Student.query.count()
        log_count = AttendanceLog.query.count()
        attendance_count = Attendance.query.count()
        
        print(f"  👤 Admin users:        {admin_count:6d}")
        print(f"  🏫 Teachers:           {teacher_count:6d}")
        print(f"  📚 Academic years:     {year_count:6d}")
        print(f"  🎓 Classrooms:         {classroom_count:6d}")
        print(f"  👨‍🎓 Students:           {student_count:6d}")
        print(f"  📝 Attendance logs:    {log_count:6d}")
        print(f"  ✅ Attendance records: {attendance_count:6d}")
        
        active_year = AcademicYear.query.filter_by(is_active=True).first()
        if active_year:
            avg_attendance = self._calculate_avg_attendance()
            print(f"  📊 Avg attendance rate: {avg_attendance:.1f}%")
            print(f"  🎓 Active year:        {active_year.year}")
        
        print("\n" + "="*70)
    
    def _print_detailed_report(self):
        """Print detailed breakdown report"""
        print(f"\n📋 Detailed Breakdown:")
        
        # Teachers by classroom
        print(f"\n🏫 Classrooms Distribution:")
        classrooms = ClassRoom.query.order_by(ClassRoom.grade, ClassRoom.class_name).all()
        for classroom in classrooms:
            student_count = Student.query.filter_by(classroom_id=classroom.id).count()
            teacher = User.query.get(classroom.head_teacher_id)
            teacher_name = teacher.full_name if teacher else "N/A"
            print(f"  {classroom.class_name:6s} | Grade {classroom.grade} | "
                  f"Teacher: {teacher_name:20s} | Students: {student_count:2d}")
        
        # Student statistics
        print(f"\n👨‍🎓 Student Statistics:")
        total_male = Student.query.filter_by(gender='Nam').count()
        total_female = Student.query.filter_by(gender='Nữ').count()
        face_enabled = Student.query.filter_by(face_recognition_enabled=True).count()
        print(f"  Male:                 {total_male:6d}")
        print(f"  Female:               {total_female:6d}")
        print(f"  Face recognition:     {face_enabled:6d}")
        
        # Attendance statistics
        print(f"\n✅ Attendance Statistics:")
        present = Attendance.query.filter_by(status='present').count()
        absent = Attendance.query.filter_by(status='absent').count()
        late = Attendance.query.filter_by(is_late=True).count()
        print(f"  Present:              {present:6d}")
        print(f"  Absent:               {absent:6d}")
        print(f"  Late:                 {late:6d}")
    
    def _calculate_avg_attendance(self):
        """Calculate average attendance rate"""
        total = Attendance.query.count()
        if total == 0:
            return 0.0
        present = Attendance.query.filter_by(status='present').count()
        return (present / total) * 100
    
    def _export_users(self, timestamp):
        """Export users to CSV"""
        users = User.query.all()
        filename = self.export_dir / f"users_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Username', 'Email', 'Full Name', 'Role', 'Phone', 'Active', 'Created At'])
            
            for user in users:
                writer.writerow([
                    user.id, user.username, user.email, user.full_name,
                    user.role, user.phone or '', 'Yes' if user.is_active else 'No',
                    user.created_at.strftime("%Y-%m-%d %H:%M:%S")
                ])
        
        print(f"  ✓ Exported {len(users)} users")
    
    def _export_academic_years(self, timestamp):
        """Export academic years to CSV"""
        years = AcademicYear.query.all()
        filename = self.export_dir / f"academic_years_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Year', 'Start Date', 'End Date', 'Active'])
            
            for year in years:
                writer.writerow([
                    year.id, year.year, year.start_date, year.end_date,
                    'Yes' if year.is_active else 'No'
                ])
        
        print(f"  ✓ Exported {len(years)} academic years")
    
    def _export_classrooms(self, timestamp):
        """Export classrooms to CSV"""
        classrooms = ClassRoom.query.all()
        filename = self.export_dir / f"classrooms_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Class Name', 'Grade', 'Room', 'Head Teacher', 'Students', 'Max', 'Active'])
            
            for classroom in classrooms:
                teacher = User.query.get(classroom.head_teacher_id)
                teacher_name = teacher.full_name if teacher else ''
                student_count = Student.query.filter_by(classroom_id=classroom.id).count()
                
                writer.writerow([
                    classroom.id, classroom.class_name, classroom.grade,
                    classroom.room_number or '', teacher_name, student_count,
                    classroom.max_student, 'Yes' if classroom.is_active else 'No'
                ])
        
        print(f"  ✓ Exported {len(classrooms)} classrooms")
    
    def _export_students(self, timestamp):
        """Export students to CSV"""
        students = Student.query.all()
        filename = self.export_dir / f"students_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Student Code', 'Full Name', 'Gender', 'DOB', 
                           'Class', 'Phone', 'Parent Phone', 'Face Enabled', 'Active'])
            
            for student in students:
                classroom = ClassRoom.query.get(student.classroom_id)
                class_name = classroom.class_name if classroom else ''
                
                writer.writerow([
                    student.id, student.student_code, student.full_name,
                    student.gender, student.date_of_birth,
                    class_name, student.phone or '', student.parent_phone or '',
                    'Yes' if student.face_recognition_enabled else 'No',
                    'Yes' if student.is_active else 'No'
                ])
        
        print(f"  ✓ Exported {len(students)} students")
    
    def _export_attendance(self, timestamp):
        """Export attendance records to CSV"""
        records = Attendance.query.all()
        filename = self.export_dir / f"attendance_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Student Code', 'Date', 'Session', 'Status', 
                           'Check-in Time', 'Late', 'Confidence', 'Method'])
            
            for record in records:
                student = Student.query.get(record.student_id)
                log = AttendanceLog.query.get(record.attendance_log_id)
                
                if student and log:
                    writer.writerow([
                        record.id, student.student_code, log.session_date,
                        log.session_type, record.status,
                        record.check_in_time.strftime("%H:%M:%S") if record.check_in_time else '',
                        'Yes' if record.is_late else 'No',
                        record.confidence_score or '',
                        record.recognition_method or ''
                    ])
        
        print(f"  ✓ Exported {len(records)} attendance records")


def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Seed Data Manager - THCS Nguyễn Đình Chiểu Face-ID System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s seed              # Seed database with sample data
  %(prog)s clear             # Clear all database
  %(prog)s reset             # Clear and reseed
  %(prog)s report            # Generate seed report
  %(prog)s export            # Export data to CSV
        """
    )
    
    parser.add_argument(
        'action',
        choices=['seed', 'clear', 'reset', 'report', 'export'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip confirmation prompts (use with caution)'
    )
    
    args = parser.parse_args()
    
    manager = SeedManager()
    
    if args.action == 'seed':
        success = manager.seed()
    elif args.action == 'clear':
        success = manager.clear(confirm=not args.no_confirm)
    elif args.action == 'reset':
        success = manager.reset(confirm=not args.no_confirm)
    elif args.action == 'report':
        success = manager.report()
    elif args.action == 'export':
        success = manager.export()
    else:
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
