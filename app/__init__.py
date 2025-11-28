from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from config import config

db = SQLAlchemy()

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from app.routes import (
        auth, classroom, student, attendance, admin, api, academic_year, user
    )
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(classroom.bp)
    app.register_blueprint(student.bp)
    app.register_blueprint(attendance.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(academic_year.bp)
    app.register_blueprint(user.bp)
    
    # Register Jinja2 filters
    from app.utils.helpers import (
        format_date, format_datetime, format_time,
        get_status_badge_class, get_status_display,
        get_confidence_badge_class, get_confidence_progress_class
    )
    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['format_time'] = format_time
    
    # Register context processor with helper functions
    @app.context_processor
    def inject_helpers():
        """Inject helper functions into template context"""
        return {
            'get_status_badge_class': get_status_badge_class,
            'get_status_display': get_status_display,
            'get_confidence_badge_class': get_confidence_badge_class,
            'get_confidence_progress_class': get_confidence_progress_class
        }
    
    # Register context processors
    @app.context_processor
    def inject_user():
        """Inject current user into template context"""
        from app.models.user import User
        
        current_user = None
        if 'user_id' in session:
            current_user = User.query.get(session['user_id'])
        
        return {
            'current_user': current_user
        }
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app
