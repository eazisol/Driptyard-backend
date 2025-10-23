"""
Custom exception classes for the application.

This module defines custom exception classes that can be used throughout
the application for consistent error handling.
"""

from typing import Any, Dict, Optional


class DriptyardException(Exception):
    """Base exception class for all application exceptions."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize the exception.
        
        Args:
            message: The error message
            details: Optional additional details about the error
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(DriptyardException):
    """Exception raised for validation errors."""
    pass


class AuthenticationError(DriptyardException):
    """Exception raised for authentication errors."""
    pass


class AuthorizationError(DriptyardException):
    """Exception raised for authorization errors."""
    pass


class NotFoundError(DriptyardException):
    """Exception raised when a resource is not found."""
    pass


class ConflictError(DriptyardException):
    """Exception raised when there's a conflict (e.g., duplicate resource)."""
    pass


class BusinessLogicError(DriptyardException):
    """Exception raised for business logic violations."""
    pass


class ExternalServiceError(DriptyardException):
    """Exception raised for external service errors."""
    pass


class DatabaseError(DriptyardException):
    """Exception raised for database-related errors."""
    pass
