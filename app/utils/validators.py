"""
Custom validators for data validation.

This module contains custom validation functions used throughout
the application for data validation and business rule enforcement.
"""

import re
from typing import Any, Optional
from uuid import UUID
from decimal import Decimal


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if email is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        bool: True if phone is valid, False otherwise
    """
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (7-15 digits)
    return 7 <= len(digits_only) <= 15


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        tuple[bool, list[str]]: (is_valid, list_of_issues)
    """
    issues = []
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    
    if not re.search(r'[a-z]', password):
        issues.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'[A-Z]', password):
        issues.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'\d', password):
        issues.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        issues.append("Password must contain at least one special character")
    
    return len(issues) == 0, issues


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    Validate username format.
    
    Args:
        username: Username to validate
        
    Returns:
        tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 50:
        return False, "Username must be at most 50 characters long"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    if username.startswith(('_', '-')) or username.endswith(('_', '-')):
        return False, "Username cannot start or end with underscore or hyphen"
    
    return True, None


def validate_price(price: Decimal) -> tuple[bool, Optional[str]]:
    """
    Validate price value.
    
    Args:
        price: Price to validate
        
    Returns:
        tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if price <= 0:
        return False, "Price must be greater than 0"
    
    if price > Decimal('999999.99'):
        return False, "Price must be less than 1,000,000"
    
    return True, None


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID string format.
    
    Args:
        uuid_string: UUID string to validate
        
    Returns:
        bool: True if UUID is valid, False otherwise
    """
    try:
        UUID(uuid_string)
        return True
    except ValueError:
        return False


def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """
    Validate file extension.
    
    Args:
        filename: File name to validate
        allowed_extensions: List of allowed extensions
        
    Returns:
        bool: True if extension is allowed, False otherwise
    """
    if not filename:
        return False
    
    extension = filename.lower().split('.')[-1]
    return extension in [ext.lower() for ext in allowed_extensions]


def validate_file_size(file_size: int, max_size: int) -> bool:
    """
    Validate file size.
    
    Args:
        file_size: File size in bytes
        max_size: Maximum allowed size in bytes
        
    Returns:
        bool: True if file size is valid, False otherwise
    """
    return file_size <= max_size


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input.
    
    Args:
        text: Text to sanitize
        max_length: Maximum length (optional)
        
    Returns:
        str: Sanitized text
    """
    # Remove leading/trailing whitespace
    sanitized = text.strip()
    
    # Remove excessive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Truncate if max_length is specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip()
    
    return sanitized


def validate_pagination_params(skip: int, limit: int) -> tuple[bool, Optional[str]]:
    """
    Validate pagination parameters.
    
    Args:
        skip: Number of items to skip
        limit: Number of items to return
        
    Returns:
        tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if skip < 0:
        return False, "Skip must be non-negative"
    
    if limit < 1:
        return False, "Limit must be at least 1"
    
    if limit > 100:
        return False, "Limit must be at most 100"
    
    return True, None
