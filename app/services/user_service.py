from app import db
from app.models.user import User
from app.utils.validators import (
    is_valid_email, is_valid_password, is_valid_username, 
    is_valid_phone, validate_user_data
)
from app.utils.constants import (
    USER_ROLES, DEFAULT_USER_ROLE, ERROR_MESSAGES
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserService:
    
    @staticmethod
    def create_user(username, email, password, full_name, role='teacher', phone=None):
        try:
            # Validate input data
            if not is_valid_username(username):
                raise ValueError(ERROR_MESSAGES['INVALID_USERNAME'])
            
            if not is_valid_email(email):
                raise ValueError(ERROR_MESSAGES['INVALID_EMAIL'])
            
            if not is_valid_password(password):
                raise ValueError(ERROR_MESSAGES['INVALID_PASSWORD'])
            
            if role not in USER_ROLES:
                raise ValueError(f"Role must be one of: {list(USER_ROLES.keys())}")
            
            if phone and not is_valid_phone(phone):
                raise ValueError(ERROR_MESSAGES['INVALID_PHONE'])
            
            # Check duplicates
            if db.session.query(User).filter_by(username=username).first():
                raise ValueError(ERROR_MESSAGES['DUPLICATE_USERNAME'])
            
            if db.session.query(User).filter_by(email=email).first():
                raise ValueError(ERROR_MESSAGES['DUPLICATE_EMAIL'])
            
            # Create user
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                role=role,
                phone=phone
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            logger.info(f'User created successfully: {username}')
            return user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error creating user {username}: {str(e)}')
            raise
    
    @staticmethod
    def get_user_by_id(user_id):
        return db.session.query(User).filter_by(id=user_id).first()
    
    @staticmethod
    def get_user_by_username(username):
        return db.session.query(User).filter_by(username=username).first()
    
    @staticmethod
    def get_user_by_email(email):
        return db.session.query(User).filter_by(email=email).first()
    
    @staticmethod
    def authenticate_user(username, password):
        try:
            user = UserService.get_user_by_username(username)
            if user and user.is_active and user.check_password(password):
                user.last_login = datetime.utcnow()
                db.session.commit()
                logger.info(f'User authenticated successfully: {username}')
                return user
            logger.warning(f'Authentication failed for user: {username}')
            return None
        except Exception as e:
            logger.error(f'Error authenticating user {username}: {str(e)}')
            return None
    
    @staticmethod
    def get_all_users(page=1, per_page=20):
        if page is None:
            # Return all users without pagination
            return db.session.query(User).all()
        return db.session.query(User).paginate(page=page, per_page=per_page)
    
    @staticmethod
    def get_all_active_users():
        return db.session.query(User).filter_by(is_active=True).all()
    
    @staticmethod
    def get_users_by_role(role):
        return db.session.query(User).filter_by(role=role, is_active=True).all()
    
    @staticmethod
    def update_user(user_id, **kwargs):
        try:
            user = UserService.get_user_by_id(user_id)
            if not user:
                raise ValueError(ERROR_MESSAGES['USER_NOT_FOUND'])
            
            # Validate email if provided
            if 'email' in kwargs and not is_valid_email(kwargs['email']):
                raise ValueError(ERROR_MESSAGES['INVALID_EMAIL'])
            
            # Validate phone if provided
            if 'phone' in kwargs and kwargs['phone'] and not is_valid_phone(kwargs['phone']):
                raise ValueError(ERROR_MESSAGES['INVALID_PHONE'])
            
            # Validate role if provided
            if 'role' in kwargs and kwargs['role'] not in USER_ROLES:
                raise ValueError(f"Role must be one of: {list(USER_ROLES.keys())}")
            
            # Check email uniqueness if changed
            if 'email' in kwargs and kwargs['email'] != user.email:
                existing_user = db.session.query(User).filter_by(email=kwargs['email']).first()
                if existing_user and existing_user.id != user_id:
                    raise ValueError(ERROR_MESSAGES['DUPLICATE_EMAIL'])
            
            allowed_fields = ['email', 'full_name', 'phone', 'avatar_url', 'role', 'is_active']
            for key, value in kwargs.items():
                if key in allowed_fields:
                    setattr(user, key, value)
            
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f'User updated successfully: {user.username}')
            return user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error updating user {user_id}: {str(e)}')
            raise
    
    @staticmethod
    def change_password(user_id, old_password, new_password):
        try:
            user = UserService.get_user_by_id(user_id)
            if not user:
                raise ValueError(ERROR_MESSAGES['USER_NOT_FOUND'])
            
            if not user.check_password(old_password):
                raise ValueError("Old password is incorrect")
            
            if not is_valid_password(new_password):
                raise ValueError(ERROR_MESSAGES['INVALID_PASSWORD'])
            
            user.set_password(new_password)
            db.session.commit()
            
            logger.info(f'Password changed successfully for user: {user.username}')
            return user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error changing password for user {user_id}: {str(e)}')
            raise
    
    @staticmethod
    def deactivate_user(user_id):
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.is_active = False
        db.session.commit()
        return user
    
    @staticmethod
    def activate_user(user_id):
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.is_active = True
        db.session.commit()
        return user
    
    @staticmethod
    def delete_user(user_id):
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        db.session.delete(user)
        db.session.commit()
        return True
    
    @staticmethod
    def reset_user_password(user_id):
        """Reset user password to a random password"""
        import random
        import string
        
        try:
            user = UserService.get_user_by_id(user_id)
            if not user:
                return None
            
            # Generate random password
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user.set_password(new_password)
            db.session.commit()
            
            logger.info(f'Password reset successfully for user: {user.username}')
            return new_password
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error resetting password for user {user_id}: {str(e)}')
            raise
