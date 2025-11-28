/**
 * Face-ID Attendance System - Main JavaScript
 * Bootstrap 5.3 integration with modern ES6+ features
 */

// Global configuration
const CONFIG = {
    API_BASE_URL: '/api',
    TIMEOUT: 30000,
    DEBOUNCE_DELAY: 300,
    ANIMATION_DURATION: 300
};

/**
 * DOM Utilities
 */
class DOMUtils {
    static ready(callback) {
        if (document.readyState !== 'loading') {
            callback();
        } else {
            document.addEventListener('DOMContentLoaded', callback);
        }
    }

    static createElement(tag, className = '', innerHTML = '') {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (innerHTML) element.innerHTML = innerHTML;
        return element;
    }

    static show(element, animation = 'fade') {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (!element) return;

        element.style.display = 'block';
        if (animation === 'fade') {
            element.style.opacity = '0';
            element.offsetHeight; // Trigger reflow
            element.style.transition = 'opacity 0.3s ease';
            element.style.opacity = '1';
        }
    }

    static hide(element, animation = 'fade') {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (!element) return;

        if (animation === 'fade') {
            element.style.transition = 'opacity 0.3s ease';
            element.style.opacity = '0';
            setTimeout(() => {
                element.style.display = 'none';
            }, CONFIG.ANIMATION_DURATION);
        } else {
            element.style.display = 'none';
        }
    }
}

/**
 * Navigation Manager
 */
class NavigationManager {
    constructor() {
        this.sidebar = document.querySelector('.sidebar');
        this.sidebarToggle = document.querySelector('[data-bs-toggle="sidebar"]');
        this.init();
    }

    init() {
        this.setupSidebarToggle();
        this.setupActiveNavigation();
        this.setupDropdowns();
    }

    setupSidebarToggle() {
        if (this.sidebarToggle) {
            this.sidebarToggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleSidebar();
            });
        }

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 992) {
                if (!this.sidebar.contains(e.target) && !this.sidebarToggle?.contains(e.target)) {
                    this.closeSidebar();
                }
            }
        });
    }

    toggleSidebar() {
        if (this.sidebar) {
            this.sidebar.classList.toggle('show');
        }
    }

    closeSidebar() {
        if (this.sidebar) {
            this.sidebar.classList.remove('show');
        }
    }

    setupActiveNavigation() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.sidebar .nav-link');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && currentPath.includes(href)) {
                link.classList.add('active');
            }
        });
    }

    setupDropdowns() {
        // Initialize Bootstrap dropdowns
        const dropdownElementList = [].slice.call(document.querySelectorAll('[data-bs-toggle="dropdown"]'));
        dropdownElementList.map(function (dropdownToggleEl) {
            return new bootstrap.Dropdown(dropdownToggleEl);
        });
    }
}

/**
 * Notification System
 */
class NotificationSystem {
    static show(message, type = 'info', duration = 5000) {
        const container = this.getContainer();
        const notification = this.createNotification(message, type);
        
        container.appendChild(notification);
        
        // Trigger animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Auto-remove
        setTimeout(() => {
            this.remove(notification);
        }, duration);
        
        return notification;
    }

    static getContainer() {
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = DOMUtils.createElement('div', 'notification-container position-fixed top-0 end-0 p-3');
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        return container;
    }

    static createNotification(message, type) {
        const alertClass = this.getAlertClass(type);
        const icon = this.getIcon(type);
        
        const notification = DOMUtils.createElement('div', 
            `alert ${alertClass} alert-dismissible fade notification-item mb-2`);
        
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="${icon} me-2"></i>
                <div class="flex-grow-1">${message}</div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        return notification;
    }

    static getAlertClass(type) {
        const classes = {
            success: 'alert-success',
            error: 'alert-danger',
            warning: 'alert-warning',
            info: 'alert-info'
        };
        return classes[type] || classes.info;
    }

    static getIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    static remove(notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, CONFIG.ANIMATION_DURATION);
    }

    static success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    }

    static error(message, duration = 7000) {
        return this.show(message, 'error', duration);
    }

    static warning(message, duration = 6000) {
        return this.show(message, 'warning', duration);
    }

    static info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }
}

/**
 * Loading Manager
 */
class LoadingManager {
    static show(element = null, text = 'Đang tải...') {
        if (element) {
            this.showElementLoading(element, text);
        } else {
            this.showGlobalLoading(text);
        }
    }

    static hide(element = null) {
        if (element) {
            this.hideElementLoading(element);
        } else {
            this.hideGlobalLoading();
        }
    }

    static showElementLoading(element, text) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (!element) return;

        const loadingHtml = `
            <div class="loading-overlay-element d-flex flex-column align-items-center justify-content-center">
                <div class="spinner-border text-primary mb-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="text-muted">${text}</div>
            </div>
        `;

        element.style.position = 'relative';
        element.insertAdjacentHTML('beforeend', loadingHtml);
    }

    static hideElementLoading(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (!element) return;

        const loadingOverlay = element.querySelector('.loading-overlay-element');
        if (loadingOverlay) {
            loadingOverlay.remove();
        }
    }

    static showGlobalLoading(text) {
        const existingOverlay = document.querySelector('.loading-overlay-global');
        if (existingOverlay) return;

        const overlay = DOMUtils.createElement('div', 'loading-overlay-global position-fixed top-0 start-0 w-100 h-100 d-flex flex-column align-items-center justify-content-center');
        overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        overlay.style.zIndex = '9999';
        
        overlay.innerHTML = `
            <div class="bg-white rounded-3 p-4 shadow text-center">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="text-muted">${text}</div>
            </div>
        `;

        document.body.appendChild(overlay);
    }

    static hideGlobalLoading() {
        const overlay = document.querySelector('.loading-overlay-global');
        if (overlay) {
            overlay.remove();
        }
    }
}

/**
 * API Client
 */
class APIClient {
    static async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            },
            timeout: CONFIG.TIMEOUT
        };

        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
            defaultOptions.headers['Authorization'] = `Bearer ${token}`;
        }

        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), mergedOptions.timeout);
            
            const response = await fetch(url, {
                ...mergedOptions,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            throw error;
        }
    }

    static async get(url) {
        return this.request(url, { method: 'GET' });
    }

    static async post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async put(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    static async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
}

/**
 * Utility Functions
 */
const Utils = {
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    formatDate(date, format = 'dd/mm/yyyy') {
        if (!(date instanceof Date)) {
            date = new Date(date);
        }
        
        const day = date.getDate().toString().padStart(2, '0');
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const year = date.getFullYear();
        
        return format
            .replace('dd', day)
            .replace('mm', month)
            .replace('yyyy', year);
    },

    formatTime(date) {
        if (!(date instanceof Date)) {
            date = new Date(date);
        }
        
        return date.toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    },

    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            NotificationSystem.success('Đã sao chép vào clipboard!');
        }).catch(() => {
            NotificationSystem.error('Không thể sao chép vào clipboard');
        });
    },

    downloadFile(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
};

/**
 * Initialize application
 */
DOMUtils.ready(() => {
    // Initialize navigation
    new NavigationManager();
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Setup global error handling
    window.addEventListener('unhandledrejection', (event) => {
        console.error('Unhandled promise rejection:', event.reason);
        NotificationSystem.error('Đã xảy ra lỗi không mong muốn. Vui lòng thử lại.');
    });
    
    console.log('Face-ID Attendance System initialized successfully!');
});

// Export for global use
window.FaceID = {
    DOMUtils,
    NavigationManager,
    NotificationSystem,
    LoadingManager,
    APIClient,
    Utils,
    CONFIG
};
