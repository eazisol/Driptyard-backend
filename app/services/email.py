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


# Global email service instance
email_service = EmailService()
