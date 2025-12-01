"""
Security utilities for authentication.

This module provides password hashing, JWT token creation and verification,
and authentication utilities.
"""

from datetime import datetime, timedelta
from typing import Any, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database import settings
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.moderator import ModeratorPermission

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__default_rounds=12,
    bcrypt__min_rounds=4,
    bcrypt__max_rounds=31
)

# Security scheme for Bearer token
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password from database
        
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        # First try bcrypt verification
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # If bcrypt fails, try SHA256 fallback (for legacy passwords)
        import hashlib
        try:
            # Truncate password to 72 bytes if it's too long (bcrypt limit)
            if len(plain_password.encode('utf-8')) > 72:
                plain_password = plain_password[:72]
            sha256_hash = hashlib.sha256(plain_password.encode()).hexdigest()
            return sha256_hash == hashed_password
        except Exception:
            return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password
        
    Returns:
        str: The hashed password
        
    Raises:
        Exception: If password hashing fails
    """
    try:
        # Truncate password to 72 bytes if it's too long (bcrypt limit)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            # Truncate at 72 bytes, not characters (important for multi-byte chars)
            password = password_bytes[:72].decode('utf-8', errors='ignore')
        return pwd_context.hash(password)
    except ValueError as e:
        # If we still get a bcrypt error, truncate more aggressively
        if "password cannot be longer than 72 bytes" in str(e):
            password = password[:50]  # Be more conservative
            return pwd_context.hash(password)
        raise


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: The subject (usually user ID) to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        str: The encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token to verify
        
    Returns:
        Optional[str]: The subject (user ID) if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None


def create_token_response(user_id: str) -> dict[str, Any]:
    """
    Create a complete token response with access token and metadata.
    
    Args:
        user_id: The user ID to create token for
        
    Returns:
        dict[str, Any]: Token response with access_token and token_type
    """
    access_token = create_access_token(subject=user_id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Get current user ID from Bearer token in Authorization header.
    
    Args:
        credentials: HTTP Authorization credentials containing the Bearer token
        
    Returns:
        str: The user ID
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    user_id = verify_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


def get_optional_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[str]:
    """
    Get current user ID from Bearer token if present, otherwise return None.
    
    This allows endpoints to work with or without authentication.
    
    Args:
        credentials: Optional HTTP Authorization credentials containing the Bearer token
        
    Returns:
        Optional[str]: The user ID if token is valid, None otherwise
    """
    if credentials is None:
        return None
    token = credentials.credentials
    return verify_token(token)


def check_spotlight_permission(user: User, db: Session) -> bool:
    """
    Check if user can apply spotlight.
    
    Args:
        user: User object
        db: Database session
        
    Returns:
        bool: True if user can apply spotlight, False otherwise
    """
    # Admin always has permission
    if user.is_admin:
        return True
    
    # Check moderator permission
    if user.is_moderator:
        permissions = db.query(ModeratorPermission).filter(
            ModeratorPermission.user_id == user.id
        ).first()
        if permissions and permissions.can_spotlight:
            return True
    
    return False


def check_remove_spotlight_permission(user: User, db: Session) -> bool:
    """
    Check if user can remove spotlight.
    
    Args:
        user: User object
        db: Database session
        
    Returns:
        bool: True if user can remove spotlight, False otherwise
    """
    # Admin always has permission
    if user.is_admin:
        return True
    
    # Check moderator permission
    if user.is_moderator:
        permissions = db.query(ModeratorPermission).filter(
            ModeratorPermission.user_id == user.id
        ).first()
        if permissions and permissions.can_remove_spotlight:
            return True
    
    return False


def verify_admin_or_moderator_with_permission(
    user: User,
    permission_type: str,
    db: Session
) -> User:
    """
    Verify that user is admin or moderator with required permission.
    
    Args:
        user: User object
        permission_type: Type of permission ('spotlight' or 'remove_spotlight')
        db: Database session
        
    Returns:
        User: The verified user object
        
    Raises:
        HTTPException: If user doesn't have required permission
    """
    if permission_type == "spotlight":
        if not check_spotlight_permission(user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to apply spotlight"
            )
    elif permission_type == "remove_spotlight":
        if not check_remove_spotlight_permission(user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to remove spotlight"
            )
    else:
        raise ValueError(f"Unknown permission type: {permission_type}")
    
    return user
