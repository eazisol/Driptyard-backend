"""
Email service for sending emails.

This module provides email sending functionality with template support.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from jinja2 import Template

from app.database import settings


class EmailService:
    """Service class for sending emails."""
    
    def __init__(self):
        """Initialize email service with SMTP configuration."""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.from_name = settings.EMAIL_FROM_NAME
        self.from_address = settings.EMAIL_FROM_ADDRESS
    
    def _load_template(self, template_name: str) -> str:
        """
        Load HTML template from templates directory.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            str: Template content
        """
        template_path = Path(__file__).parent.parent / "templates" / "email" / template_name
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _create_message(self, to_email: str, subject: str, html_content: str) -> MIMEMultipart:
        """
        Create email message.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            
        Returns:
            MIMEMultipart: Email message
        """
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{self.from_name} <{self.from_address}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Create HTML part
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        return msg
    
    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Send email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = self._create_message(to_email, subject, html_content)
            
            # Connect to SMTP server
            if self.smtp_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            
            # Login and send email
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    
    def send_verification_email(self, email: str, verification_code: str) -> bool:
        """
        Send email verification code.
        
        Args:
            email: User email address
            verification_code: 6-digit verification code
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "Verify Your Email - Driptyard"
        
        # Load template and render with variables
        template_content = self._load_template("verification.html")
        template = Template(template_content)
        html_content = template.render(
            verification_code=verification_code,
            email=email
        )
        
        return self._send_email(email, subject, html_content)
    
    def send_password_reset_email(self, email: str, reset_token: str) -> bool:
        """
        Send password reset token (for client-side password reset flow).
        
        Args:
            email: User email address
            reset_token: 6-digit reset token
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "Reset Your Password - Driptyard"
        
        # Create HTML content for password reset
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f0f0f0;
                    margin: 0;
                    padding: 40px 20px;
                }}
                .email-card {{
                    background-color: #ffffff;
                    max-width: 600px;
                    margin: 0 auto;
                    border-radius: 12px;
                    border: 1px solid #e0e0e0;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    padding: 50px 40px;
                }}
                .title {{
                    color: #000000;
                    font-size: 36px;
                    font-weight: bold;
                    margin: 0 0 30px 0;
                    text-align: center;
                    font-family: Arial, sans-serif;
                }}
                .greeting {{
                    color: #333333;
                    font-size: 16px;
                    margin: 0 0 15px 0;
                    font-weight: normal;
                }}
                .instruction {{
                    color: #333333;
                    font-size: 16px;
                    margin: 0 0 30px 0;
                    font-weight: normal;
                }}
                .otp-code {{
                    color: #22c55e;
                    font-size: 48px;
                    font-weight: bold;
                    text-align: center;
                    margin: 40px 0;
                    letter-spacing: 6px;
                    font-family: Arial, sans-serif;
                }}
                .warning {{
                    color: #333333;
                    font-size: 16px;
                    margin: 30px 0 20px 0;
                    line-height: 1.6;
                    font-weight: normal;
                }}
                .closing {{
                    color: #333333;
                    font-size: 16px;
                    margin: 30px 0 10px 0;
                    font-weight: normal;
                }}
                .dots {{
                    color: #333333;
                    font-size: 16px;
                    margin: 0;
                    text-align: left;
                }}
            </style>
        </head>
        <body>
            <div class="email-card">
                <h1 class="title">Password Reset OTP</h1>
                
                <p class="greeting">Dear User,</p>
                
                <p class="instruction">Your One-Time Password (OTP) for password reset is:</p>
                
                <div class="otp-code">{reset_token}</div>
                
                <p class="warning">
                    Please use this OTP to complete your password reset process. Do not share this code with anyone.
                </p>
                
                <p class="closing">Thank you for using Driptyard!</p>
                
                <p class="dots">...</p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(email, subject, html_content)
    
    def send_admin_password_reset_email(self, email: str, username: str, new_password: str) -> bool:
        """
        Send admin-initiated password reset email with new password.
        
        Args:
            email: User email address
            username: Username
            new_password: The new password set by admin
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "Your Password Has Been Reset - Driptyard"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f0f0f0;
                    margin: 0;
                    padding: 40px 20px;
                }}
                .email-card {{
                    background-color: #ffffff;
                    max-width: 600px;
                    margin: 0 auto;
                    border-radius: 12px;
                    border: 1px solid #e0e0e0;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    padding: 50px 40px;
                }}
                .title {{
                    color: #000000;
                    font-size: 28px;
                    font-weight: bold;
                    margin: 0 0 30px 0;
                    text-align: center;
                }}
                .greeting {{
                    color: #333333;
                    font-size: 16px;
                    margin: 0 0 15px 0;
                    font-weight: normal;
                }}
                .content {{
                    color: #333333;
                    font-size: 16px;
                    margin: 0 0 20px 0;
                    line-height: 1.6;
                }}
                .password-box {{
                    background-color: #f8f9fa;
                    border: 2px solid #22c55e;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 30px 0;
                    text-align: center;
                }}
                .password-label {{
                    color: #666666;
                    font-size: 14px;
                    margin: 0 0 10px 0;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .password-value {{
                    color: #22c55e;
                    font-size: 24px;
                    font-weight: bold;
                    font-family: 'Courier New', monospace;
                    margin: 0;
                    word-break: break-all;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 30px 0;
                    border-radius: 4px;
                }}
                .warning-text {{
                    color: #856404;
                    font-size: 14px;
                    margin: 0;
                    line-height: 1.6;
                }}
                .closing {{
                    color: #333333;
                    font-size: 16px;
                    margin: 30px 0 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="email-card">
                <h1 class="title">Password Reset</h1>
                
                <p class="greeting">Dear {username},</p>
                
                <p class="content">
                    Your password has been reset by an administrator. Your new password is:
                </p>
                
                <div class="password-box">
                    <p class="password-label">Your New Password</p>
                    <p class="password-value">{new_password}</p>
                </div>
                
                <div class="warning">
                    <p class="warning-text">
                        <strong>Security Notice:</strong> Please log in with this password and change it 
                        to a new password of your choice as soon as possible. Do not share this password 
                        with anyone.
                    </p>
                </div>
                
                <p class="content">
                    You can now log in to your account using this password. We recommend changing it 
                    to something more memorable after logging in.
                </p>
                
                <p class="closing">Thank you for using Driptyard!</p>
                
                <p class="content">Best regards,<br>The Driptyard Team</p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(email, subject, html_content)

    def send_product_verification_email(self, email: str, product_title: str, verification_code: str) -> bool:
        """Send product listing verification code."""
        subject = "Verify Your Product Listing - Driptyard"

        template_content = self._load_template("product_verification.html")
        template = Template(template_content)
        html_content = template.render(
            verification_code=verification_code,
            email=email,
            product_title=product_title
        )

        return self._send_email(email, subject, html_content)
    
    def send_account_suspended_email(self, email: str, username: str) -> bool:
        """
        Send account suspended notification email.
        
        Args:
            email: User email address
            username: Username
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "Your Account Has Been Suspended - Driptyard"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f0f0f0;
                    margin: 0;
                    padding: 40px 20px;
                }}
                .email-card {{
                    background-color: #ffffff;
                    max-width: 600px;
                    margin: 0 auto;
                    border-radius: 12px;
                    border: 1px solid #e0e0e0;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    padding: 50px 40px;
                }}
                .title {{
                    color: #dc2626;
                    font-size: 28px;
                    font-weight: bold;
                    margin: 0 0 30px 0;
                    text-align: center;
                }}
                .content {{
                    color: #333333;
                    font-size: 16px;
                    margin: 0 0 20px 0;
                    line-height: 1.6;
                }}
                .closing {{
                    color: #333333;
                    font-size: 16px;
                    margin: 30px 0 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="email-card">
                <h1 class="title">Account Suspended</h1>
                
                <p class="content">Dear {username},</p>
                
                <p class="content">
                    Your Driptyard account has been suspended. This means you will not be able to 
                    log in or access your account until the suspension is lifted.
                </p>
                
                <p class="content">
                    If you believe this is an error or have questions about your account suspension, 
                    please contact our support team for assistance.
                </p>
                
                <p class="closing">Thank you for your understanding.</p>
                
                <p class="content">Best regards,<br>The Driptyard Team</p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(email, subject, html_content)
    
    def send_account_reinstated_email(self, email: str, username: str) -> bool:
        """
        Send account reinstated notification email.
        
        Args:
            email: User email address
            username: Username
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "Your Account Has Been Reinstated - Driptyard"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f0f0f0;
                    margin: 0;
                    padding: 40px 20px;
                }}
                .email-card {{
                    background-color: #ffffff;
                    max-width: 600px;
                    margin: 0 auto;
                    border-radius: 12px;
                    border: 1px solid #e0e0e0;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    padding: 50px 40px;
                }}
                .title {{
                    color: #22c55e;
                    font-size: 28px;
                    font-weight: bold;
                    margin: 0 0 30px 0;
                    text-align: center;
                }}
                .content {{
                    color: #333333;
                    font-size: 16px;
                    margin: 0 0 20px 0;
                    line-height: 1.6;
                }}
                .closing {{
                    color: #333333;
                    font-size: 16px;
                    margin: 30px 0 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="email-card">
                <h1 class="title">Account Reinstated</h1>
                
                <p class="content">Dear {username},</p>
                
                <p class="content">
                    Good news! Your Driptyard account has been reinstated and you now have full 
                    access to your account again.
                </p>
                
                <p class="content">
                    You can now log in and use all features of the platform as normal.
                </p>
                
                <p class="closing">Thank you for your patience.</p>
                
                <p class="content">Best regards,<br>The Driptyard Team</p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(email, subject, html_content)
    
    def send_account_deleted_email(self, email: str, username: str) -> bool:
        """
        Send account deleted notification email.
        
        Args:
            email: User email address
            username: Username
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "Your Account Has Been Deleted - Driptyard"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f0f0f0;
                    margin: 0;
                    padding: 40px 20px;
                }}
                .email-card {{
                    background-color: #ffffff;
                    max-width: 600px;
                    margin: 0 auto;
                    border-radius: 12px;
                    border: 1px solid #e0e0e0;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    padding: 50px 40px;
                }}
                .title {{
                    color: #dc2626;
                    font-size: 28px;
                    font-weight: bold;
                    margin: 0 0 30px 0;
                    text-align: center;
                }}
                .content {{
                    color: #333333;
                    font-size: 16px;
                    margin: 0 0 20px 0;
                    line-height: 1.6;
                }}
                .closing {{
                    color: #333333;
                    font-size: 16px;
                    margin: 30px 0 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="email-card">
                <h1 class="title">Account Deleted</h1>
                
                <p class="content">Dear {username},</p>
                
                <p class="content">
                    Your Driptyard account and all associated data have been permanently deleted 
                    from our system. This action cannot be undone.
                </p>
                
                <p class="content">
                    All of your personal information, listings, orders, and other account data 
                    have been permanently removed in accordance with our data deletion policy.
                </p>
                
                <p class="content">
                    If you have any questions or concerns about this deletion, please contact our 
                    support team.
                </p>
                
                <p class="closing">Thank you for using Driptyard.</p>
                
                <p class="content">Best regards,<br>The Driptyard Team</p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(email, subject, html_content)


# Global email service instance
email_service = EmailService()
