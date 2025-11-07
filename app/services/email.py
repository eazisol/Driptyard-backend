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
        Send password reset token.
        
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
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #f9f9f9;
                    border-radius: 10px;
                    padding: 30px;
                    margin: 20px 0;
                }}
                .header {{
                    text-align: center;
                    color: #2c3e50;
                    margin-bottom: 30px;
                }}
                .token {{
                    background-color: #3498db;
                    color: white;
                    font-size: 32px;
                    font-weight: bold;
                    text-align: center;
                    padding: 20px;
                    border-radius: 8px;
                    letter-spacing: 8px;
                    margin: 30px 0;
                }}
                .info {{
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #3498db;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 12px;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset Request</h1>
                </div>
                
                <p>Hello,</p>
                
                <p>We received a request to reset your password for your Driptyard account ({email}).</p>
                
                <p>Use the following code to reset your password:</p>
                
                <div class="token">{reset_token}</div>
                
                <div class="info">
                    <strong>⏰ This code will expire in 15 minutes</strong>
                    <p style="margin: 10px 0 0 0;">For security reasons, please use this code as soon as possible.</p>
                </div>
                
                <p>If you didn't request a password reset, please ignore this email and your password will remain unchanged.</p>
                
                <p>For security reasons, never share this code with anyone.</p>
                
                <div class="footer">
                    <p>This is an automated email. Please do not reply to this message.</p>
                    <p>&copy; 2024 Driptyard. All rights reserved.</p>
                </div>
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


# Global email service instance
email_service = EmailService()
