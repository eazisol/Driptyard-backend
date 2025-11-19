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
