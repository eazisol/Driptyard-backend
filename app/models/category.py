"""
Category-related database models.

This module contains models for main categories, category types, sub categories,
brands, and gender.
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.models.base import CategoryBaseModel


class MainCategory(CategoryBaseModel):
    """Main category model (Fashion, Collectibles, Lifestyle)."""
    
    __tablename__ = "main_categories"
    
    name = Column(String(100), nullable=False, unique=True, index=True)
    
    # Relationships
    category_types = relationship("CategoryType", back_populates="main_category", cascade="all, delete-orphan")


class CategoryType(CategoryBaseModel):
    """Category type model with parent reference to main category."""
    
    __tablename__ = "category_types"
    
    name = Column(String(100), nullable=False, index=True)
    main_category_id = Column(Integer, ForeignKey("main_categories.id"), nullable=False, index=True)
    
    # Relationships
    main_category = relationship("MainCategory", back_populates="category_types")
    sub_categories = relationship("SubCategory", back_populates="category_type", cascade="all, delete-orphan")


class SubCategory(CategoryBaseModel):
    """Sub category model with type and gender references."""
    
    __tablename__ = "sub_categories"
    
    name = Column(String(100), nullable=False, index=True)
    type_id = Column(Integer, ForeignKey("category_types.id"), nullable=False, index=True)
    gender_id = Column(Integer, ForeignKey("genders.id"), nullable=True, index=True)
    
    # Relationships
    category_type = relationship("CategoryType", back_populates="sub_categories")
    gender = relationship("Gender", back_populates="sub_categories")


class Brand(CategoryBaseModel):
    """Brand model for product brands."""
    
    __tablename__ = "brands"
    
    name = Column(String(100), nullable=False, unique=True, index=True)
    active = Column(Boolean, default=True, nullable=False, index=True)


class Gender(CategoryBaseModel):
    """Gender model (male, female, unisex)."""
    
    __tablename__ = "genders"
    
    name = Column(String(20), nullable=False, unique=True, index=True)
    
    # Relationships
    sub_categories = relationship("SubCategory", back_populates="gender")

