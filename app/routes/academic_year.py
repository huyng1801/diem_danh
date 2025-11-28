"""
Academic Year Routes
Các endpoint quản lý năm học
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from app import db
from app.services.academic_year_service import AcademicYearService
from app.utils.decorators import login_required, role_required
from app.utils.validators import is_valid_academic_year
from app.utils.constants import (
    ERROR_MESSAGES, API_SUCCESS_CODE, API_BAD_REQUEST_CODE,
    API_UNAUTHORIZED_CODE, API_CREATED_CODE
)
import logging

logger = logging.getLogger(__name__)

# Create blueprint
academic_year_bp = Blueprint('academic_year', __name__, url_prefix='/academic-year')

# ============================================================================
# PAGE ROUTES (Template Rendering)
# ============================================================================

@academic_year_bp.route('/list', methods=['GET'])
@login_required
@role_required('admin')
def list_academic_years():
    """
    Display academic years list page (HTML template)
    GET /academic-year/list
    """
    try:
        return render_template('academic_year/list.html')
    except Exception as e:
        logger.error(f'Error rendering academic years page: {str(e)}')
        flash('Lỗi khi tải trang quản lý niên khóa', 'danger')
        return redirect(url_for('admin.dashboard'))


@academic_year_bp.route('/create', methods=['GET'])
@login_required
@role_required('admin')
def create_academic_year_page():
    """
    Create academic year page
    GET /academic-year/create
    """
    return render_template('academic_year/form.html', year=None)


@academic_year_bp.route('/<int:year_id>/edit', methods=['GET'])
@login_required
@role_required('admin')
def edit_academic_year_page(year_id):
    """
    Edit academic year page
    GET /academic-year/<year_id>/edit
    """
    from app.models.academic_year import AcademicYear
    year = AcademicYear.query.get_or_404(year_id)
    return render_template('academic_year/form.html', year=year)

@academic_year_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_academic_year():
    """
    Add new academic year (GET form, POST data)
    GET /academic-year/add - Show form
    POST /academic-year/add - Process form
    """
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            # Build year string from start_year and end_year
            start_year = data.get('start_year')
            end_year = data.get('end_year')
            
            if not start_year or not end_year:
                return jsonify({
                    'success': False,
                    'message': 'Missing start_year or end_year field',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
            
            year_string = f"{start_year}-{end_year}"
            
            # Validate academic year format
            if not is_valid_academic_year(year_string):
                return jsonify({
                    'success': False,
                    'message': 'Invalid academic year format (use YYYY-YYYY)',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
            
            # Prepare data for service
            year_data = {
                'year': year_string,
                'start_date': data.get('start_date'),
                'end_date': data.get('end_date'),
                'description': data.get('description', ''),
                'is_active': bool(data.get('is_active'))
            }
            
            # Create academic year
            year = AcademicYearService.create_academic_year(
                year_string, 
                year_data['start_date'], 
                year_data['end_date']
            )
            
            # Set as active if requested
            if year_data.get('is_active'):
                AcademicYearService.activate_academic_year(year.id)
            
            logger.info(f'Academic year created: {year.year}')
            
            return jsonify({
                'success': True,
                'message': 'Academic year created successfully',
                'data': year.to_dict(),
                'status_code': API_CREATED_CODE
            }), API_CREATED_CODE
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e),
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        except Exception as e:
            logger.error(f'Error creating academic year: {str(e)}')
            return jsonify({
                'success': False,
                'message': 'Failed to create academic year',
                'status_code': 500
            }), 500
    
    # GET request - could return form or JSON response
    return jsonify({'message': 'GET method not implemented for form'}), 405

@academic_year_bp.route('/<int:year_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_academic_year(year_id):
    """
    Edit academic year (GET form, POST data)
    GET /academic-year/<id>/edit - Show form with data
    POST /academic-year/<id>/edit - Process form
    """
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            year = AcademicYearService.get_academic_year_by_id(year_id)
            
            if not year:
                return jsonify({
                    'success': False,
                    'message': 'Academic year not found',
                    'status_code': 404
                }), 404
            
            # Build year string from start_year and end_year if provided
            start_year = data.get('start_year')
            end_year = data.get('end_year')
            
            update_data = {}
            
            if start_year and end_year:
                year_string = f"{start_year}-{end_year}"
                
                # Validate academic year format
                if not is_valid_academic_year(year_string):
                    return jsonify({
                        'success': False,
                        'message': 'Invalid academic year format (use YYYY-YYYY)',
                        'status_code': API_BAD_REQUEST_CODE
                    }), API_BAD_REQUEST_CODE
                
                update_data['year'] = year_string
            
            # Add other fields
            if 'start_date' in data:
                update_data['start_date'] = data['start_date']
            if 'end_date' in data:
                update_data['end_date'] = data['end_date']
            
            # Update academic year
            year = AcademicYearService.update_academic_year(year_id, **update_data)
            
            logger.info(f'Academic year updated: {year.year}')
            
            return jsonify({
                'success': True,
                'message': 'Academic year updated successfully',
                'data': year.to_dict(),
                'status_code': API_SUCCESS_CODE
            }), API_SUCCESS_CODE
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e),
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        except Exception as e:
            logger.error(f'Error updating academic year: {str(e)}')
            return jsonify({
                'success': False,
                'message': 'Failed to update academic year',
                'status_code': 500
            }), 500
    
    # GET request - return academic year data
    try:
        year = AcademicYearService.get_academic_year_by_id(year_id)
        if not year:
            return jsonify({
                'success': False,
                'message': 'Academic year not found',
                'status_code': 404
            }), 404
        
        return jsonify({
            'success': True,
            'data': year.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
    except Exception as e:
        logger.error(f'Error retrieving academic year: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve academic year',
            'status_code': 500
        }), 500

# ============================================================================
# API ROUTES (JSON Data)
# ============================================================================

@academic_year_bp.route('/api/list', methods=['GET'])
@login_required
@role_required('admin')
def api_list_academic_years():
    """
    Get all academic years (API endpoint)
    GET /academic-year/api/list
    Query params: page (optional), limit (optional), search (optional)
    """
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '')
        
        years = AcademicYearService.get_all_academic_years()
        
        # Search filter if provided
        if search:
            years = [y for y in years if search.lower() in y.year.lower()]
        
        # Pagination
        start = (page - 1) * limit
        end = start + limit
        paginated = years[start:end]
        total = len(years)
        
        return jsonify({
            'success': True,
            'message': 'Academic years retrieved',
            'data': {
                'academic_years': [year.to_dict() for year in paginated],
                'total': total,
                'page': page,
                'limit': limit,
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': limit,
                    'pages': (total + limit - 1) // limit
                }
            },
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error retrieving academic years: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve academic years',
            'status_code': 500
        }), 500

@academic_year_bp.route('/api/create', methods=['POST'])
@login_required
@role_required('admin')
def api_create_academic_year():
    """
    Create new academic year (API endpoint)
    POST /academic-year/api/create
    Body: {
        "year": "2024-2025",
        "start_date": "2024-09-01",
        "end_date": "2025-05-31",
        "is_active": false
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('year'):
            return jsonify({
                'success': False,
                'message': 'Missing year field',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        if not data.get('start_date'):
            return jsonify({
                'success': False,
                'message': 'Missing start_date field',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        if not data.get('end_date'):
            return jsonify({
                'success': False,
                'message': 'Missing end_date field',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Validate academic year format
        if not is_valid_academic_year(data['year']):
            return jsonify({
                'success': False,
                'message': 'Invalid academic year format (use YYYY-YYYY)',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Convert string dates to datetime.date objects
        from datetime import datetime
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': f'Invalid date format: {str(e)}',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Validate date range
        if end_date <= start_date:
            return jsonify({
                'success': False,
                'message': 'End date must be after start date',
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Create academic year
        year = AcademicYearService.create_academic_year(
            data['year'], 
            start_date, 
            end_date
        )
        
        # Set as active if requested
        if data.get('is_active'):
            AcademicYearService.activate_academic_year(year.id)
        
        logger.info(f'Academic year created: {year.year}')
        
        return jsonify({
            'success': True,
            'message': 'Academic year created successfully',
            'data': year.to_dict(),
            'status_code': API_CREATED_CODE
        }), API_CREATED_CODE
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'status_code': API_BAD_REQUEST_CODE
        }), API_BAD_REQUEST_CODE
    except Exception as e:
        logger.error(f'Error creating academic year: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to create academic year',
            'status_code': 500
        }), 500

@academic_year_bp.route('/api/<int:year_id>/activate', methods=['PUT', 'POST'])
@login_required
@role_required('admin')
def api_activate_academic_year(year_id):
    """
    Activate academic year (API endpoint)
    PUT/POST /academic-year/api/<id>/activate
    """
    try:
        year = AcademicYearService.get_academic_year_by_id(year_id)
        
        if not year:
            return jsonify({
                'success': False,
                'message': 'Academic year not found',
                'status_code': 404
            }), 404
        
        # Activate year
        year = AcademicYearService.activate_academic_year(year_id)
        
        logger.info(f'Academic year activated: {year.year}')
        
        return jsonify({
            'success': True,
            'message': 'Academic year activated',
            'data': year.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error activating academic year: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to activate academic year',
            'status_code': 500
        }), 500

@academic_year_bp.route('/api/active', methods=['GET'])
@login_required
def api_get_active_academic_year():
    """
    Get currently active academic year (API endpoint)
    GET /academic-year/api/active
    """
    try:
        year = AcademicYearService.get_active_academic_year()
        
        if not year:
            return jsonify({
                'success': False,
                'message': 'No active academic year found',
                'status_code': 404
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Active academic year retrieved',
            'data': year.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error retrieving active academic year: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve active academic year',
            'status_code': 500
        }), 500

@academic_year_bp.route('/api/<int:year_id>', methods=['GET', 'PUT'])
@login_required
@role_required('admin')
def api_get_academic_year(year_id):
    """
    Get or update academic year by ID (API endpoint)
    GET /academic-year/api/<id> - Get academic year
    PUT /academic-year/api/<id> - Update academic year
    """
    # Handle PUT request - Update academic year
    if request.method == 'PUT':
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'No data provided',
                    'status_code': API_BAD_REQUEST_CODE
                }), API_BAD_REQUEST_CODE
            
            # Prepare update data
            update_data = {}
            if 'year' in data:
                update_data['year'] = data['year']
            if 'start_date' in data:
                update_data['start_date'] = data['start_date']
            if 'end_date' in data:
                update_data['end_date'] = data['end_date']
            if 'is_active' in data:
                update_data['is_active'] = data['is_active']
            
            # Update academic year
            year = AcademicYearService.update_academic_year(year_id, **update_data)
            
            logger.info(f'Academic year updated: {year.year}')
            
            return jsonify({
                'success': True,
                'message': 'Academic year updated successfully',
                'data': year.to_dict(),
                'status_code': API_SUCCESS_CODE
            }), API_SUCCESS_CODE
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e),
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        except Exception as e:
            logger.error(f'Error updating academic year: {str(e)}')
            return jsonify({
                'success': False,
                'message': 'Failed to update academic year',
                'status_code': 500
            }), 500
    
    # Handle GET request - Retrieve academic year
    try:
        year = AcademicYearService.get_academic_year_by_id(year_id)
        
        if not year:
            return jsonify({
                'success': False,
                'message': 'Academic year not found',
                'status_code': 404
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Academic year retrieved',
            'data': year.to_dict(),
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error retrieving academic year: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve academic year',
            'status_code': 500
        }), 500

@academic_year_bp.route('/api/<int:year_id>/delete', methods=['DELETE', 'POST'])
@login_required
@role_required('admin')
def api_delete_academic_year(year_id):
    """
    Delete academic year (API endpoint)
    DELETE/POST /academic-year/api/<id>/delete
    """
    try:
        year = AcademicYearService.get_academic_year_by_id(year_id)
        
        if not year:
            return jsonify({
                'success': False,
                'message': 'Academic year not found',
                'status_code': 404
            }), 404
        
        # Check if can delete
        can_delete, message = AcademicYearService.can_delete_academic_year(year_id)
        if not can_delete:
            return jsonify({
                'success': False,
                'message': message,
                'status_code': API_BAD_REQUEST_CODE
            }), API_BAD_REQUEST_CODE
        
        # Delete
        AcademicYearService.delete_academic_year(year_id)
        
        logger.info(f'Academic year deleted: {year.year}')
        
        return jsonify({
            'success': True,
            'message': 'Academic year deleted',
            'status_code': API_SUCCESS_CODE
        }), API_SUCCESS_CODE
        
    except Exception as e:
        logger.error(f'Error deleting academic year: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to delete academic year',
            'status_code': 500
        }), 500


