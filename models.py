from pydantic import BaseModel, EmailStr
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

# Enums
class ChatType(str, enum.Enum):
    PRIVATE = "private"  # Тільки приватні чати для месенджера

class MessageType(str, enum.Enum):
    TEXT = "text"
    FILE = "file"
    SYSTEM = "system"

class MemberRole(str, enum.Enum):
    PARTICIPANT = "participant"  # Спрощуємо ролі для приватних чатів

class MemberStatus(str, enum.Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    LEFT = "left"

# Pydantic моделі для API
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Chat моделі
class ChatBase(BaseModel):
    name: Optional[str] = None  # Для приватних чатів може бути None
    description: Optional[str] = None
    chat_type: ChatType = ChatType.PRIVATE

class ChatCreate(ChatBase):
    recipient_id: int  # ID користувача, з яким створюємо чат

class ChatResponse(ChatBase):
    id: int
    creator_id: int
    recipient_id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Message моделі
class MessageBase(BaseModel):
    content: str
    message_type: MessageType = MessageType.TEXT

class MessageCreate(MessageBase):
    chat_id: int

class MessageResponse(MessageBase):
    id: int
    author_id: int
    chat_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_deleted: bool

    class Config:
        from_attributes = True

# File Attachment моделі
class FileAttachmentBase(BaseModel):
    filename: str
    file_path: str
    file_size: int
    mime_type: str

class FileAttachmentCreate(FileAttachmentBase):
    message_id: int

class FileAttachmentResponse(FileAttachmentBase):
    id: int
    message_id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

# Chat Member моделі
class ChatMemberBase(BaseModel):
    role: MemberRole = MemberRole.PARTICIPANT
    status: MemberStatus = MemberStatus.ACTIVE

class ChatMemberCreate(ChatMemberBase):
    user_id: int
    chat_id: int

class ChatMemberResponse(ChatMemberBase):
    id: int
    user_id: int
    chat_id: int
    joined_at: datetime

    class Config:
        from_attributes = True

# SQLAlchemy моделі для бази даних
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    messages = relationship("Message", back_populates="author")
    created_chats = relationship("Chat", foreign_keys="Chat.creator_id", back_populates="creator")
    received_chats = relationship("Chat", foreign_keys="Chat.recipient_id", back_populates="recipient")
    chat_memberships = relationship("ChatMember", back_populates="user")

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)  # Може бути None для приватних чатів
    description = Column(Text, nullable=True)
    chat_type = Column(Enum(ChatType), nullable=False, default=ChatType.PRIVATE)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Додаємо recipient_id
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_chats")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_chats")
    messages = relationship("Message", back_populates="chat")
    members = relationship("ChatMember", back_populates="chat")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    author = relationship("User", back_populates="messages")
    chat = relationship("Chat", back_populates="messages")
    attachments = relationship("FileAttachment", back_populates="message")

class FileAttachment(Base):
    __tablename__ = "file_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("Message", back_populates="attachments")

class ChatMember(Base):
    __tablename__ = "chat_members"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    role = Column(Enum(MemberRole), default=MemberRole.PARTICIPANT)
    status = Column(Enum(MemberStatus), default=MemberStatus.ACTIVE)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_memberships")
    chat = relationship("Chat", back_populates="members")

class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    blacklisted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    