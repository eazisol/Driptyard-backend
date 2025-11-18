"""
Base model class with common fields.

This module contains the BaseModel class that all other models inherit from.
"""

from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class BaseModel(Base):
    """
    Base model class with common fields.
    
    All models should inherit from this class to get common fields
    like id, created_at, and updated_at.
    """
    
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp"
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name from class name.
        
        Converts CamelCase class names to snake_case table names.
        Example: UserProfile -> user_profiles
        """
        # Convert CamelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        
        # Add 's' for plural (simple pluralization)
        if name.endswith('y'):
            return f"{name[:-1]}ies"
        elif name.endswith(('s', 'sh', 'ch', 'x', 'z')):
            return f"{name}es"
        else:
            return f"{name}s"
    
    def __repr__(self) -> str:
        """String representation of the model instance."""
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Returns:
            dict: Dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class CategoryBaseModel(Base):
    """
    Base model class for category-related models with Integer IDs.
    
    All category-related models (MainCategory, CategoryType, SubCategory, Brand, Gender)
    should inherit from this class to get integer IDs instead of UUIDs.
    """
    
    __abstract__ = True
    
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
        comment="Unique identifier"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp"
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name from class name.
        
        Converts CamelCase class names to snake_case table names.
        Example: UserProfile -> user_profiles
        """
        # Convert CamelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        
        # Add 's' for plural (simple pluralization)
        if name.endswith('y'):
            return f"{name[:-1]}ies"
        elif name.endswith(('s', 'sh', 'ch', 'x', 'z')):
            return f"{name}es"
        else:
            return f"{name}s"
    
    def __repr__(self) -> str:
        """String representation of the model instance."""
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Returns:
            dict: Dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class UserProductBaseModel(Base):
    """
    Base model class for User, Product, and Order models with Integer IDs.
    
    These models should inherit from this class to get integer IDs instead of UUIDs.
    """
    
    __abstract__ = True
    
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
        comment="Unique identifier"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp"
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name from class name.
        
        Converts CamelCase class names to snake_case table names.
        Example: UserProfile -> user_profiles
        """
        # Convert CamelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        
        # Add 's' for plural (simple pluralization)
        if name.endswith('y'):
            return f"{name[:-1]}ies"
        elif name.endswith(('s', 'sh', 'ch', 'x', 'z')):
            return f"{name}es"
        else:
            return f"{name}s"
    
    def __repr__(self) -> str:
        """String representation of the model instance."""
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Returns:
            dict: Dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
