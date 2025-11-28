# Routes package
# Import and expose all blueprints

from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.classroom import classroom_bp
from app.routes.student import student_bp
from app.routes.attendance import attendance_bp
from app.routes.api import api_bp
from app.routes.academic_year import academic_year_bp
from app.routes.user import user_bp

# Expose as simple names for app registration
class auth:
    bp = auth_bp

class admin:
    bp = admin_bp

class classroom:
    bp = classroom_bp

class student:
    bp = student_bp

class attendance:
    bp = attendance_bp
    
class api:
    bp = api_bp

class academic_year:
    bp = academic_year_bp

class user:
    bp = user_bp
