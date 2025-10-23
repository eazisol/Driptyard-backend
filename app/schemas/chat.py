"""
Chat Pydantic schemas.

This module contains all Pydantic schemas related to chat operations
including request/response validation for chat endpoints.
"""

from typing import Optional, List
from pydantic import Field
from uuid import UUID
from datetime import datetime
from enum import Enum

from app.schemas.base import BaseResponseSchema, BaseCreateSchema, BaseUpdateSchema


class MessageType(str, Enum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


class ConversationBaseSchema(BaseCreateSchema):
    """Base conversation schema with common fields."""
    
    title: Optional[str] = Field(None, max_length=200, description="Conversation title")
    is_active: bool = Field(default=True, description="Whether conversation is active")


class ConversationCreate(ConversationBaseSchema):
    """Schema for conversation creation."""
    
    participant_id: UUID = Field(..., description="Other participant ID")


class ConversationResponse(BaseResponseSchema):
    """Schema for conversation response data."""
    
    title: Optional[str] = Field(None, description="Conversation title")
    is_active: bool = Field(..., description="Whether conversation is active")
    participants: List[UUID] = Field(..., description="Participant IDs")
    last_message: Optional[str] = Field(None, description="Last message preview")
    last_message_at: Optional[datetime] = Field(None, description="Last message timestamp")
    unread_count: int = Field(default=0, description="Number of unread messages")


class MessageBaseSchema(BaseCreateSchema):
    """Base message schema with common fields."""
    
    content: str = Field(..., min_length=1, max_length=2000, description="Message content")
    message_type: MessageType = Field(default=MessageType.TEXT, description="Message type")
    reply_to_id: Optional[UUID] = Field(None, description="ID of message being replied to")


class MessageCreate(MessageBaseSchema):
    """Schema for message creation."""
    
    conversation_id: UUID = Field(..., description="Conversation ID")


class MessageResponse(BaseResponseSchema):
    """Schema for message response data."""
    
    conversation_id: UUID = Field(..., description="Conversation ID")
    sender_id: UUID = Field(..., description="Sender ID")
    content: str = Field(..., description="Message content")
    message_type: MessageType = Field(..., description="Message type")
    reply_to_id: Optional[UUID] = Field(None, description="ID of message being replied to")
    is_read: bool = Field(default=False, description="Whether message has been read")
    read_at: Optional[datetime] = Field(None, description="Message read timestamp")


class MessageUpdate(BaseUpdateSchema):
    """Schema for message updates."""
    
    is_read: Optional[bool] = Field(None, description="Whether message has been read")


class ConversationListResponse(BaseResponseSchema):
    """Schema for conversation list response (limited information)."""
    
    title: Optional[str] = Field(None, description="Conversation title")
    is_active: bool = Field(..., description="Whether conversation is active")
    participant_count: int = Field(..., description="Number of participants")
    last_message: Optional[str] = Field(None, description="Last message preview")
    last_message_at: Optional[datetime] = Field(None, description="Last message timestamp")
    unread_count: int = Field(default=0, description="Number of unread messages")
