"""
Email Helper
Hàm hỗ trợ gửi email
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template_string
from app.utils.constants import EMAIL_SENDER_NAME, EMAIL_FROM

logger = logging.getLogger(__name__)

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# ============================================================================
# EMAIL SENDING FUNCTIONS
# ============================================================================

def send_email(recipient_email, subject, html_content, text_content=None):
    """
    Gửi email
    
    Args:
        recipient_email: Email người nhận
        subject: Tiêu đề email
        html_content: Nội dung HTML
        text_content: Nội dung text (nếu có)
    
    Returns:
        bool: True nếu gửi thành công, False nếu thất bại
    """
    try:
        # Lấy cấu hình từ config
        smtp_user = current_app.config.get('MAIL_USERNAME')
        smtp_password = current_app.config.get('MAIL_PASSWORD')
        
        if not smtp_user or not smtp_password:
            logger.warning('Email credentials not configured')
            return False
        
        # Tạo message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'{EMAIL_SENDER_NAME} <{EMAIL_FROM}>'
        msg['To'] = recipient_email
        
        # Thêm text content (fallback)
        if text_content:
            msg.attach(MIMEText(text_content, 'plain'))
        
        # Thêm HTML content
        msg.attach(MIMEText(html_content, 'html'))
        
        # Kết nối và gửi email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        logger.info(f'Email sent successfully to {recipient_email}')
        return True
    
    except Exception as e:
        logger.error(f'Error sending email to {recipient_email}: {str(e)}')
        return False

def send_welcome_email(user_email, user_name, username):
    """
    Gửi email chào mừng khi người dùng được tạo
    """
    subject = 'Chào mừng đến hệ thống Face-ID Attendance'
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; direction: ltr;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Chào mừng, {user_name}!</h2>
                
                <p>Tài khoản của bạn đã được tạo thành công trên hệ thống Face-ID Attendance.</p>
                
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Tên đăng nhập:</strong> {username}</p>
                    <p><strong>Email:</strong> {user_email}</p>
                </div>
                
                <p>Vui lòng đăng nhập vào hệ thống bằng tên đăng nhập và mật khẩu được cấp.</p>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    Đây là email tự động, vui lòng không trả lời email này.
                </p>
            </div>
        </body>
    </html>
    """
    
    return send_email(user_email, subject, html_content)

def send_password_reset_email(user_email, user_name, reset_token):
    """
    Gửi email đặt lại mật khẩu
    """
    subject = 'Đặt lại mật khẩu - Face-ID Attendance'
    
    reset_link = f'{current_app.config.get("APP_URL", "http://localhost:5000")}/reset-password/{reset_token}'
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; direction: ltr;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Đặt lại mật khẩu</h2>
                
                <p>Xin chào {user_name},</p>
                
                <p>Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản của bạn.</p>
                
                <p style="margin: 30px 0;">
                    <a href="{reset_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Đặt lại mật khẩu
                    </a>
                </p>
                
                <p style="color: #666; font-size: 12px;">
                    Liên kết sẽ hết hạn sau 24 giờ.
                </p>
                
                <p>Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.</p>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    Đây là email tự động, vui lòng không trả lời email này.
                </p>
            </div>
        </body>
    </html>
    """
    
    return send_email(user_email, subject, html_content)

def send_account_locked_email(user_email, user_name, lock_duration_minutes=15):
    """
    Gửi email thông báo tài khoản bị khóa
    """
    subject = 'Tài khoản bị khóa - Face-ID Attendance'
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; direction: ltr;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #d9534f;">⚠️ Tài khoản bị khóa</h2>
                
                <p>Xin chào {user_name},</p>
                
                <p>Tài khoản của bạn đã bị tạm khóa do có quá nhiều lần đăng nhập sai.</p>
                
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Lý do:</strong> Nhiều lần đăng nhập sai</p>
                    <p><strong>Thời gian khóa:</strong> {lock_duration_minutes} phút</p>
                </div>
                
                <p>Vui lòng thử lại sau {lock_duration_minutes} phút hoặc liên hệ admin nếu cần hỗ trợ.</p>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    Đây là email tự động, vui lòng không trả lời email này.
                </p>
            </div>
        </body>
    </html>
    """
    
    return send_email(user_email, subject, html_content)

def send_attendance_report_email(user_email, user_name, classroom_name, report_data, report_date):
    """
    Gửi email báo cáo điểm danh
    """
    subject = f'Báo cáo điểm danh - {classroom_name} ({report_date})'
    
    rows = ''
    for item in report_data:
        rows += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">{item['student_name']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">{item['status']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">{item['time']}</td>
        </tr>
        """
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; direction: ltr;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Báo cáo điểm danh</h2>
                
                <p>Xin chào {user_name},</p>
                
                <p>Dưới đây là báo cáo điểm danh cho lớp <strong>{classroom_name}</strong> ngày <strong>{report_date}</strong>:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <thead>
                        <tr style="background-color: #f5f5f5;">
                            <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Học sinh</th>
                            <th style="padding: 10px; text-align: center; border-bottom: 2px solid #ddd;">Trạng thái</th>
                            <th style="padding: 10px; text-align: center; border-bottom: 2px solid #ddd;">Giờ điểm danh</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    Đây là email tự động, vui lòng không trả lời email này.
                </p>
            </div>
        </body>
    </html>
    """
    
    return send_email(user_email, subject, html_content)

def send_bulk_email(recipient_list, subject, html_content):
    """
    Gửi email hàng loạt đến nhiều người
    
    Args:
        recipient_list: Danh sách email người nhận
        subject: Tiêu đề email
        html_content: Nội dung HTML
    
    Returns:
        dict: {'success': số lượng gửi thành công, 'failed': số lượng gửi thất bại}
    """
    success = 0
    failed = 0
    
    for recipient_email in recipient_list:
        if send_email(recipient_email, subject, html_content):
            success += 1
        else:
            failed += 1
    
    logger.info(f'Bulk email sent: {success} success, {failed} failed')
    return {'success': success, 'failed': failed}

# ============================================================================
# EMAIL VALIDATION HELPERS
# ============================================================================

def is_valid_email_format(email):
    """
    Kiểm tra xem định dạng email có hợp lệ hay không
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_email_list(email_list):
    """
    Xác thực danh sách email
    Trả về: (valid_emails, invalid_emails)
    """
    valid_emails = []
    invalid_emails = []
    
    for email in email_list:
        if is_valid_email_format(email):
            valid_emails.append(email)
        else:
            invalid_emails.append(email)
    
    return valid_emails, invalid_emails
