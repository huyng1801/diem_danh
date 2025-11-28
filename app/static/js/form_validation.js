/**
 * Form Validation Module for Face-ID Attendance System
 * Bootstrap 5.3 compatible form validation with custom rules
 */

/**
 * Form Validator Class
 */
class FormValidator {
    constructor(formElement, options = {}) {
        this.form = typeof formElement === 'string' ? document.querySelector(formElement) : formElement;
        this.options = {
            submitCallback: options.submitCallback || null,
            validateOnChange: options.validateOnChange !== false,
            validateOnBlur: options.validateOnBlur !== false,
            showToast: options.showToast !== false,
            scrollToError: options.scrollToError !== false,
            ...options
        };
        
        this.rules = new Map();
        this.isValid = false;
        
        if (this.form) {
            this.init();
        }
    }

    init() {
        this.setupEventListeners();
        this.addBootstrapValidation();
    }

    setupEventListeners() {
        // Form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.validateForm();
        });

        // Real-time validation
        if (this.options.validateOnChange) {
            this.form.addEventListener('input', (e) => {
                this.validateField(e.target);
            });
        }

        if (this.options.validateOnBlur) {
            this.form.addEventListener('blur', (e) => {
                this.validateField(e.target);
            }, true);
        }
    }

    addBootstrapValidation() {
        this.form.classList.add('needs-validation');
        this.form.setAttribute('novalidate', '');
    }

    /**
     * Add validation rule for a field
     */
    addRule(fieldName, validator, message) {
        if (!this.rules.has(fieldName)) {
            this.rules.set(fieldName, []);
        }
        this.rules.get(fieldName).push({ validator, message });
        return this;
    }

    /**
     * Validate entire form
     */
    async validateForm() {
        const fields = this.form.querySelectorAll('input, textarea, select');
        let isFormValid = true;
        let firstErrorField = null;

        for (const field of fields) {
            const isFieldValid = await this.validateField(field);
            if (!isFieldValid && !firstErrorField) {
                firstErrorField = field;
            }
            isFormValid = isFormValid && isFieldValid;
        }

        this.isValid = isFormValid;

        if (isFormValid) {
            this.form.classList.add('was-validated');
            this.onFormValid();
        } else {
            this.form.classList.add('was-validated');
            this.onFormInvalid(firstErrorField);
        }

        return isFormValid;
    }

    /**
     * Validate single field
     */
    async validateField(field) {
        if (!field.name || field.disabled) return true;

        let isValid = true;
        let errorMessage = '';

        // Built-in HTML5 validation
        if (!field.checkValidity()) {
            isValid = false;
            errorMessage = field.validationMessage;
        }

        // Custom rules validation
        if (isValid && this.rules.has(field.name)) {
            const rules = this.rules.get(field.name);
            
            for (const rule of rules) {
                try {
                    const result = await rule.validator(field.value, field, this.form);
                    if (!result) {
                        isValid = false;
                        errorMessage = rule.message;
                        break;
                    }
                } catch (error) {
                    console.error('Validation error:', error);
                    isValid = false;
                    errorMessage = 'Lỗi validation: ' + error.message;
                    break;
                }
            }
        }

        this.updateFieldValidation(field, isValid, errorMessage);
        return isValid;
    }

    /**
     * Update field validation state
     */
    updateFieldValidation(field, isValid, message = '') {
        // Remove existing validation classes
        field.classList.remove('is-valid', 'is-invalid');
        
        // Add appropriate validation class
        if (isValid) {
            field.classList.add('is-valid');
        } else {
            field.classList.add('is-invalid');
        }

        // Update feedback message
        this.updateFeedbackMessage(field, message, isValid);
    }

    /**
     * Update feedback message
     */
    updateFeedbackMessage(field, message, isValid) {
        const feedbackClass = isValid ? 'valid-feedback' : 'invalid-feedback';
        const oppositeFeedbackClass = isValid ? 'invalid-feedback' : 'valid-feedback';
        
        // Remove opposite feedback
        const oppositeFeedback = field.parentNode.querySelector(`.${oppositeFeedbackClass}`);
        if (oppositeFeedback) {
            oppositeFeedback.remove();
        }

        // Find or create feedback element
        let feedback = field.parentNode.querySelector(`.${feedbackClass}`);
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = feedbackClass;
            field.parentNode.appendChild(feedback);
        }

        feedback.textContent = message;
    }

    /**
     * Handle valid form submission
     */
    onFormValid() {
        if (this.options.showToast) {
            FaceID.NotificationSystem.success('Form hợp lệ!');
        }

        if (this.options.submitCallback) {
            this.options.submitCallback(this.getFormData());
        } else {
            this.form.submit();
        }
    }

    /**
     * Handle invalid form
     */
    onFormInvalid(firstErrorField) {
        if (this.options.showToast) {
            FaceID.NotificationSystem.error('Vui lòng kiểm tra lại các trường thông tin!');
        }

        if (this.options.scrollToError && firstErrorField) {
            firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstErrorField.focus();
        }
    }

    /**
     * Get form data as object
     */
    getFormData() {
        const formData = new FormData(this.form);
        const data = {};
        
        for (const [key, value] of formData.entries()) {
            if (data[key]) {
                // Handle multiple values (checkboxes, multiple selects)
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }
        
        return data;
    }

    /**
     * Reset form validation
     */
    reset() {
        this.form.classList.remove('was-validated');
        const fields = this.form.querySelectorAll('input, textarea, select');
        
        fields.forEach(field => {
            field.classList.remove('is-valid', 'is-invalid');
        });

        // Remove feedback messages
        this.form.querySelectorAll('.valid-feedback, .invalid-feedback').forEach(el => {
            el.remove();
        });

        this.isValid = false;
    }
}

/**
 * Common Validation Rules
 */
const ValidationRules = {
    required: (value) => {
        return value && value.toString().trim().length > 0;
    },

    email: (value) => {
        if (!value) return true; // Let required rule handle empty values
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(value);
    },

    phone: (value) => {
        if (!value) return true;
        const phoneRegex = /^[0-9]{10,11}$/;
        return phoneRegex.test(value.replace(/\D/g, ''));
    },

    minLength: (min) => (value) => {
        if (!value) return true;
        return value.toString().length >= min;
    },

    maxLength: (max) => (value) => {
        if (!value) return true;
        return value.toString().length <= max;
    },

    pattern: (regex) => (value) => {
        if (!value) return true;
        return regex.test(value);
    },

    studentId: (value) => {
        if (!value) return true;
        // Student ID format: 2 letters + 6 digits (e.g., HS123456)
        const studentIdRegex = /^[A-Z]{2}\d{6}$/;
        return studentIdRegex.test(value.toUpperCase());
    },

    classCode: (value) => {
        if (!value) return true;
        // Class code format: Number + Letter (e.g., 6A, 7B, 8C, 9D)
        const classCodeRegex = /^[6-9][A-Z]$/;
        return classCodeRegex.test(value.toUpperCase());
    },

    birthDate: (value) => {
        if (!value) return true;
        const date = new Date(value);
        const now = new Date();
        const minAge = 10; // Minimum age for students
        const maxAge = 18; // Maximum age for students
        
        const age = now.getFullYear() - date.getFullYear();
        return age >= minAge && age <= maxAge;
    },

    username: (value) => {
        if (!value) return true;
        // Username: alphanumeric and underscore, 3-20 characters
        const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
        return usernameRegex.test(value);
    },

    password: (value) => {
        if (!value) return true;
        // Password: at least 6 characters with letters and numbers
        return value.length >= 6 && /[a-zA-Z]/.test(value) && /\d/.test(value);
    },

    confirmPassword: (confirmValue, field, form) => {
        const passwordField = form.querySelector('input[name="password"]');
        return passwordField ? confirmValue === passwordField.value : true;
    },

    fileSize: (maxSizeMB) => (value, field) => {
        if (!field.files || field.files.length === 0) return true;
        const file = field.files[0];
        const maxSize = maxSizeMB * 1024 * 1024; // Convert to bytes
        return file.size <= maxSize;
    },

    fileType: (allowedTypes) => (value, field) => {
        if (!field.files || field.files.length === 0) return true;
        const file = field.files[0];
        return allowedTypes.includes(file.type);
    }
};

/**
 * Form Validation Presets
 */
const ValidationPresets = {
    setupStudentForm(formSelector) {
        const validator = new FormValidator(formSelector, {
            submitCallback: async (data) => {
                try {
                    FaceID.LoadingManager.show(null, 'Đang lưu thông tin học sinh...');
                    
                    const response = await FaceID.APIClient.post('/api/students', data);
                    
                    if (response.success) {
                        FaceID.NotificationSystem.success('Đã lưu thông tin học sinh thành công!');
                        if (response.redirect) {
                            window.location.href = response.redirect;
                        }
                    } else {
                        throw new Error(response.message || 'Lỗi khi lưu thông tin');
                    }
                } catch (error) {
                    FaceID.NotificationSystem.error('Lỗi: ' + error.message);
                } finally {
                    FaceID.LoadingManager.hide();
                }
            }
        });

        validator
            .addRule('student_id', ValidationRules.required, 'Mã học sinh là bắt buộc')
            .addRule('student_id', ValidationRules.studentId, 'Mã học sinh không đúng định dạng (VD: HS123456)')
            .addRule('full_name', ValidationRules.required, 'Họ tên là bắt buộc')
            .addRule('full_name', ValidationRules.minLength(2), 'Họ tên phải có ít nhất 2 ký tự')
            .addRule('birth_date', ValidationRules.required, 'Ngày sinh là bắt buộc')
            .addRule('birth_date', ValidationRules.birthDate, 'Ngày sinh không hợp lệ (tuổi từ 10-18)')
            .addRule('class_id', ValidationRules.required, 'Lớp học là bắt buộc')
            .addRule('email', ValidationRules.email, 'Email không đúng định dạng')
            .addRule('phone', ValidationRules.phone, 'Số điện thoại không đúng định dạng');

        return validator;
    },

    setupClassForm(formSelector) {
        const validator = new FormValidator(formSelector, {
            submitCallback: async (data) => {
                try {
                    FaceID.LoadingManager.show(null, 'Đang lưu thông tin lớp học...');
                    
                    const response = await FaceID.APIClient.post('/api/classes', data);
                    
                    if (response.success) {
                        FaceID.NotificationSystem.success('Đã lưu thông tin lớp học thành công!');
                        if (response.redirect) {
                            window.location.href = response.redirect;
                        }
                    } else {
                        throw new Error(response.message || 'Lỗi khi lưu thông tin');
                    }
                } catch (error) {
                    FaceID.NotificationSystem.error('Lỗi: ' + error.message);
                } finally {
                    FaceID.LoadingManager.hide();
                }
            }
        });

        validator
            .addRule('class_name', ValidationRules.required, 'Tên lớp là bắt buộc')
            .addRule('class_code', ValidationRules.required, 'Mã lớp là bắt buộc')
            .addRule('class_code', ValidationRules.classCode, 'Mã lớp không đúng định dạng (VD: 6A, 7B)')
            .addRule('teacher_id', ValidationRules.required, 'Giáo viên chủ nhiệm là bắt buộc');

        return validator;
    },

    setupUserForm(formSelector) {
        const validator = new FormValidator(formSelector, {
            submitCallback: async (data) => {
                try {
                    FaceID.LoadingManager.show(null, 'Đang lưu thông tin người dùng...');
                    
                    const response = await FaceID.APIClient.post('/api/users', data);
                    
                    if (response.success) {
                        FaceID.NotificationSystem.success('Đã lưu thông tin người dùng thành công!');
                        if (response.redirect) {
                            window.location.href = response.redirect;
                        }
                    } else {
                        throw new Error(response.message || 'Lỗi khi lưu thông tin');
                    }
                } catch (error) {
                    FaceID.NotificationSystem.error('Lỗi: ' + error.message);
                } finally {
                    FaceID.LoadingManager.hide();
                }
            }
        });

        validator
            .addRule('username', ValidationRules.required, 'Tên đăng nhập là bắt buộc')
            .addRule('username', ValidationRules.username, 'Tên đăng nhập chỉ chứa chữ, số và dấu gạch dưới (3-20 ký tự)')
            .addRule('email', ValidationRules.required, 'Email là bắt buộc')
            .addRule('email', ValidationRules.email, 'Email không đúng định dạng')
            .addRule('password', ValidationRules.required, 'Mật khẩu là bắt buộc')
            .addRule('password', ValidationRules.password, 'Mật khẩu phải có ít nhất 6 ký tự gồm chữ và số')
            .addRule('confirm_password', ValidationRules.required, 'Xác nhận mật khẩu là bắt buộc')
            .addRule('confirm_password', ValidationRules.confirmPassword, 'Mật khẩu xác nhận không khớp')
            .addRule('full_name', ValidationRules.required, 'Họ tên là bắt buộc')
            .addRule('phone', ValidationRules.phone, 'Số điện thoại không đúng định dạng');

        return validator;
    },

    setupImageUploadForm(formSelector) {
        const validator = new FormValidator(formSelector, {
            submitCallback: async (data) => {
                const formData = new FormData(document.querySelector(formSelector));
                
                try {
                    FaceID.LoadingManager.show(null, 'Đang tải ảnh lên...');
                    
                    const response = await fetch('/api/upload/images', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        FaceID.NotificationSystem.success('Đã tải ảnh lên thành công!');
                        if (result.redirect) {
                            window.location.href = result.redirect;
                        }
                    } else {
                        throw new Error(result.message || 'Lỗi khi tải ảnh lên');
                    }
                } catch (error) {
                    FaceID.NotificationSystem.error('Lỗi: ' + error.message);
                } finally {
                    FaceID.LoadingManager.hide();
                }
            }
        });

        validator
            .addRule('images', ValidationRules.required, 'Vui lòng chọn ảnh để tải lên')
            .addRule('images', ValidationRules.fileType(['image/jpeg', 'image/jpg', 'image/png']), 'Chỉ chấp nhận file ảnh JPG, PNG')
            .addRule('images', ValidationRules.fileSize(5), 'Kích thước file không được vượt quá 5MB');

        return validator;
    }
};

// Auto-initialize forms based on page
FaceID.DOMUtils.ready(() => {
    // Student form
    if (document.querySelector('#student-form')) {
        ValidationPresets.setupStudentForm('#student-form');
    }

    // Class form
    if (document.querySelector('#class-form')) {
        ValidationPresets.setupClassForm('#class-form');
    }

    // User form
    if (document.querySelector('#user-form')) {
        ValidationPresets.setupUserForm('#user-form');
    }

    // Image upload form
    if (document.querySelector('#image-upload-form')) {
        ValidationPresets.setupImageUploadForm('#image-upload-form');
    }

    // Generic form validation for forms with .needs-validation class
    document.querySelectorAll('.needs-validation').forEach(form => {
        if (!form.hasAttribute('data-validator-initialized')) {
            new FormValidator(form);
            form.setAttribute('data-validator-initialized', 'true');
        }
    });
});

// Export for global use
window.FaceID = window.FaceID || {};
window.FaceID.FormValidator = FormValidator;
window.FaceID.ValidationRules = ValidationRules;
window.FaceID.ValidationPresets = ValidationPresets;
