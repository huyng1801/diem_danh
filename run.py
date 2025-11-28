"""
Application Entry Point
Điểm khởi động của ứng dụng Face-ID Attendance System
"""

import os
import logging
from flask import Flask, jsonify
from config import get_config
from app import db  # Import db from app module
from app.utils import ensure_upload_directories

# Configure logging
def setup_logging():
    """Cấu hình logging cho ứng dụng"""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'app.log')),
            logging.StreamHandler()
        ]
    )


def register_context_processors(app):
    """Register context processors to inject variables into all templates"""
    from flask import request, session
    from app.models.user import User
    
    @app.context_processor
    def inject_current_user():
        """Inject current_user into all templates"""
        current_user = None
        
        # Try to get from request context (set by login_required decorator)
        if hasattr(request, 'current_user'):
            current_user = request.current_user
        # Try to get from session
        elif 'user_id' in session:
            current_user = User.query.get(session['user_id'])
        
        return dict(current_user=current_user)
    
    @app.context_processor
    def inject_session_data():
        """Inject session data into templates"""
        return dict(
            session_username=session.get('username'),
            session_role=session.get('role'),
            session_full_name=session.get('full_name')
        )


def create_app(config_name=None):
    """
    Create and configure Flask application
    
    Args:
        config_name: 'development', 'production', 'testing'
    
    Returns:
        Flask application instance
    """
    # Setup logging
    setup_logging()
    
    # Get configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    config = get_config()
    
    # Create Flask app with correct template and static folder paths
    app = Flask(__name__, 
                template_folder='app/templates',
                static_folder='app/static')
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Create database tables
    with app.app_context():
        # Create upload directories
        ensure_upload_directories()
        
        # Create database tables
        db.create_all()
        
        # Note: `SystemConfig` model removed. Any default configuration
        # should be handled via environment variables or a separate
        # migration/seed script if needed.
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Register Jinja2 filters
    from app.utils.helpers import (
        format_date, format_datetime, format_time,
        get_status_badge_class, get_status_display,
        get_confidence_badge_class, get_confidence_progress_class
    )
    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['format_time'] = format_time
    
    # Inject helper functions into template context
    @app.context_processor
    def inject_helpers():
        """Inject helper functions into template context"""
        return {
            'get_status_badge_class': get_status_badge_class,
            'get_status_display': get_status_display,
            'get_confidence_badge_class': get_confidence_badge_class,
            'get_confidence_progress_class': get_confidence_progress_class
        }
    
    app.logger.info(f'Flask app created with config: {config_name}')
    
    return app


def register_blueprints(app):
    """Register Flask blueprints"""
    try:
        # Import routes
        from app.routes.auth import auth_bp
        from app.routes.admin import admin_bp
        from app.routes.academic_year import academic_year_bp
        from app.routes.classroom import classroom_bp
        from app.routes.student import student_bp
        from app.routes.attendance import attendance_bp
        from app.routes.api import api_bp
        from app.routes.user import user_bp
        
        # Register blueprints
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(academic_year_bp, url_prefix='/academic-year')
        app.register_blueprint(classroom_bp, url_prefix='/classroom')
        app.register_blueprint(student_bp, url_prefix='/student')
        app.register_blueprint(attendance_bp, url_prefix='/attendance')
        app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(user_bp, url_prefix='/users')
        
        # Add root route
        from flask import redirect, url_for, send_from_directory
        
        @app.route('/')
        def index():
            """Root route - redirect to login"""
            return redirect(url_for('auth.login_page'))
        
        @app.route('/dashboard')
        def dashboard():
            """Dashboard route - redirect to admin dashboard"""
            return redirect(url_for('admin.dashboard'))
        
        # Serve uploaded files (student faces, exports, etc.)
        @app.route('/uploads/<path:filename>')
        def serve_uploads(filename):
            """Serve files from uploads directory"""
            try:
                upload_dir = os.path.join(os.path.dirname(__file__), 'app', 'uploads')
                
                # Normalize path separators for Windows
                filename = filename.replace('/', os.sep)
                file_path = os.path.join(upload_dir, filename)
                
                # Log the request
                app.logger.info(f'Serving upload: {filename}')
                app.logger.info(f'Upload dir: {upload_dir}')
                app.logger.info(f'Resolved path: {file_path}')
                
                # Security check: ensure the resolved path is within uploads directory
                resolved_path = os.path.abspath(file_path)
                resolved_upload_dir = os.path.abspath(upload_dir)
                if not resolved_path.startswith(resolved_upload_dir):
                    app.logger.warning(f'Path traversal attempt detected: {filename}')
                    return jsonify({
                        'success': False,
                        'message': 'Access denied',
                        'status_code': 403
                    }), 403
                
                # Check if file exists
                if not os.path.exists(file_path):
                    app.logger.warning(f'Upload file not found: {file_path}')
                    return jsonify({
                        'success': False,
                        'message': 'File not found',
                        'status_code': 404
                    }), 404
                
                # Get the directory and filename for send_from_directory
                directory = os.path.dirname(file_path)
                name = os.path.basename(file_path)
                
                app.logger.info(f'Sending file from directory: {directory}, filename: {name}')
                return send_from_directory(directory, name, as_attachment=False)
            except Exception as e:
                app.logger.error(f'Error serving upload file {filename}: {str(e)}', exc_info=True)
                return jsonify({
                    'success': False,
                    'message': 'Error serving file',
                    'status_code': 500
                }), 500
        
        app.logger.info('All blueprints registered successfully')
    except ImportError as e:
        app.logger.warning(f'Some blueprints not yet implemented: {str(e)}')


def register_error_handlers(app):
    """Register error handlers"""
    from flask import jsonify
    
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'success': False,
            'message': 'Trang không tìm thấy',
            'status_code': 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal server error: {str(error)}')
        return jsonify({
            'success': False,
            'message': 'Lỗi server',
            'status_code': 500
        }), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return jsonify({
            'success': False,
            'message': 'Truy cập bị từ chối',
            'status_code': 403
        }), 403
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        return jsonify({
            'success': False,
            'message': 'Không được phép truy cập',
            'status_code': 401
        }), 401


def register_cli_commands(app):
    """Register CLI commands"""
    
    @app.cli.command()
    def init_db():
        """Initialize the database"""
        db.create_all()
        print('Database initialized!')
    
    @app.cli.command()
    def seed_db():
        """Seed the database with initial data"""
        from app.models.user import User

        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@faceid.local',
                full_name='Administrator',
                role='admin',
                is_active=True
            )
            admin.set_password('Admin@123')
            db.session.add(admin)
            db.session.commit()
            print('Admin user created!')
        else:
            print('Admin user already exists!')
    
    @app.cli.command()
    def train_model():
        """Train face recognition model"""
        from ml_models.face_trainer import FaceTrainer
        
        trainer = FaceTrainer()
        stats = trainer.train_all()
        print(f'Model trained successfully!')
        print(f'Total persons: {stats["total_persons"]}')
        print(f'Total face images: {stats["total_images"]}')


if __name__ == '__main__':
    # Create app
    app = create_app()
    
    # Run app - disable debug mode to avoid reloader issues
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=True
    )
