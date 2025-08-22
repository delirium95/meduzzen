from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from models import Chat, Message, ChatMember, FileAttachment, User, ChatType, MemberRole, MemberStatus
from typing import List, Optional
import os
import shutil
from datetime import datetime
import logging

# Налаштовуємо логування
logger = logging.getLogger(__name__)

# Налаштування для файлів
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png", ".gif"}

# Створюємо папку для завантажень
os.makedirs(UPLOAD_DIR, exist_ok=True)

def create_private_chat(db: Session, creator_id: int, recipient_id: int) -> Chat:
    """Створення приватного чату між двома користувачами"""
    logger.info(f"🔍 Creating private chat: creator_id={creator_id}, recipient_id={recipient_id}")
    
    # Перевіряємо, чи існує користувач
    recipient = db.query(User).filter(User.id == recipient_id).first()
    if not recipient:
        logger.error(f"❌ Recipient user {recipient_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient user not found"
        )
    
    # Перевіряємо, чи не створюємо чат з самим собою
    if creator_id == recipient_id:
        logger.error(f"❌ Cannot create chat with yourself")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create chat with yourself"
        )
    
    # Перевіряємо, чи вже існує чат між цими користувачами
    existing_chat = db.query(Chat).filter(
        ((Chat.creator_id == creator_id) & (Chat.recipient_id == recipient_id)) |
        ((Chat.creator_id == recipient_id) & (Chat.recipient_id == creator_id)),
        Chat.chat_type == ChatType.PRIVATE
    ).first()
    
    if existing_chat:
        logger.info(f"✅ Found existing chat: {existing_chat.id}")
        # Ensure both users are members (idempotent fix for previously missing members)
        _ensure_user_membership(db, existing_chat.id, creator_id)
        _ensure_user_membership(db, existing_chat.id, recipient_id)
        return existing_chat
    
    # Створюємо новий приватний чат
    chat = Chat(
        chat_type=ChatType.PRIVATE,
        creator_id=creator_id,
        recipient_id=recipient_id
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    logger.info(f"✅ Chat created: {chat.id}")
    
    # Додаємо обох користувачів як учасників
    creator_member = ChatMember(
        user_id=creator_id,
        chat_id=chat.id,
        role=MemberRole.PARTICIPANT,
        status=MemberStatus.ACTIVE
    )
    recipient_member = ChatMember(
        user_id=recipient_id,
        chat_id=chat.id,
        role=MemberRole.PARTICIPANT,
        status=MemberStatus.ACTIVE
    )
    
    db.add(creator_member)
    db.add(recipient_member)
    db.commit()
    logger.info(f"✅ Members added: creator={creator_id}, recipient={recipient_id}")
    
    return chat

def _ensure_user_membership(db: Session, chat_id: int, user_id: int) -> None:
    """Create ACTIVE participant membership if missing. Safe to call repeatedly."""
    member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == user_id,
        ChatMember.status == MemberStatus.ACTIVE
    ).first()
    if member:
        return
    new_member = ChatMember(
        user_id=user_id,
        chat_id=chat_id,
        role=MemberRole.PARTICIPANT,
        status=MemberStatus.ACTIVE
    )
    db.add(new_member)
    db.commit()
    logger.info(f"✅ Ensured membership: user={user_id} chat={chat_id}")

def get_or_create_private_chat(db: Session, user_id: int, other_user_id: int) -> Chat:
    """Отримання існуючого приватного чату або створення нового"""
    # Спочатку шукаємо існуючий чат
    existing_chat = db.query(Chat).filter(
        ((Chat.creator_id == user_id) & (Chat.recipient_id == other_user_id)) |
        ((Chat.creator_id == other_user_id) & (Chat.recipient_id == user_id)),
        Chat.chat_type == ChatType.PRIVATE
    ).first()
    
    if existing_chat:
        return existing_chat
    
    # Якщо чат не існує, створюємо новий
    return create_private_chat(db, user_id, other_user_id)

def add_member_to_chat(db: Session, chat_id: int, user_id: int, role: str = "participant") -> ChatMember:
    """Додавання учасника до чату (для приватних чатів зазвичай не потрібно)"""
    # Перевіряємо, чи користувач вже в чаті
    existing_member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == user_id
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this chat"
        )
    
    member = ChatMember(
        user_id=user_id,
        chat_id=chat_id,
        role=MemberRole.PARTICIPANT,
        status=MemberStatus.ACTIVE
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    
    return member

def send_message(db: Session, message_data: dict, author_id: int) -> Message:
    """Відправлення повідомлення"""
    logger.info(f"🔍 Sending message: chat_id={message_data['chat_id']}, author_id={author_id}")
    
    # Перевіряємо, чи користувач є учасником чату (з авто-додаванням для автора/одержувача приватного чату)
    member = db.query(ChatMember).filter(
        ChatMember.chat_id == message_data["chat_id"],
        ChatMember.user_id == author_id,
        ChatMember.status == MemberStatus.ACTIVE
    ).first()
    if not member:
        # Перевіряємо імпліцитне членство через creator/recipient і забезпечуємо рядок у chat_members
        chat = db.query(Chat).filter(Chat.id == message_data["chat_id"]).first()
        if chat and (chat.creator_id == author_id or chat.recipient_id == author_id):
            try:
                _ensure_user_membership(db, chat.id, author_id)
                member = db.query(ChatMember).filter(
                    ChatMember.chat_id == message_data["chat_id"],
                    ChatMember.user_id == author_id,
                    ChatMember.status == MemberStatus.ACTIVE
                ).first()
            except Exception as e:
                logger.error(f"⚠️ Failed to ensure membership before sending: {e}")
        
    logger.info(f"🔍 Chat member check after ensure: {member}")
    if not member:
        logger.error(f"❌ User {author_id} is not a member of chat {message_data['chat_id']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat"
        )
    
    message = Message(
        content=message_data["content"],
        message_type=message_data.get("message_type", "text"),
        author_id=author_id,
        chat_id=message_data["chat_id"]
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    logger.info(f"✅ Message sent: {message.id}")
    return message

def edit_message(db: Session, message_id: int, new_content: str, user_id: int) -> Message:
    """Редагування повідомлення"""
    message = db.query(Message).filter(Message.id == message_id).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    if message.author_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own messages"
        )
    
    if message.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit deleted message"
        )
    
    message.content = new_content
    message.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(message)
    
    return message

def delete_message(db: Session, message_id: int, user_id: int) -> bool:
    """Видалення повідомлення (soft delete)"""
    message = db.query(Message).filter(Message.id == message_id).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    if message.author_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own messages"
        )
    
    message.is_deleted = True
    db.commit()
    
    return True

def upload_file(db: Session, file: UploadFile, message_id: int) -> FileAttachment:
    """Завантаження файлу"""
    # Перевіряємо розмір файлу
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum allowed size"
        )
    
    # Перевіряємо розширення
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed"
        )
    
    # Генеруємо унікальне ім'я файлу
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    # Зберігаємо файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Створюємо запис в базі
    attachment = FileAttachment(
        filename=file.filename,
        file_path=file_path,
        file_size=os.path.getsize(file_path),
        mime_type=file.content_type or "application/octet-stream",
        message_id=message_id
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    
    return attachment

def get_chat_messages(db: Session, chat_id: int, skip: int = 0, limit: int = 50) -> List[Message]:
    """Отримання повідомлень чату"""
    messages = db.query(Message).filter(
        Message.chat_id == chat_id,
        Message.is_deleted == False
    ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    return messages

def get_user_chats(db: Session, user_id: int) -> List[Chat]:
    """Отримання приватних чатів користувача"""
    logger.info(f"🔍 Getting chats for user {user_id}")
    # Chats via explicit membership rows
    member_rows = db.query(ChatMember).filter(
        ChatMember.user_id == user_id,
        ChatMember.status == MemberStatus.ACTIVE
    ).all()
    member_chat_ids = {row.chat_id for row in member_rows}

    # Chats where the user is creator or recipient (implicit membership for private chats)
    # Implicit chats: do not rely on enum equality to avoid legacy enum-label mismatch
    implicit_chats = db.query(Chat).filter(
        (Chat.creator_id == user_id) | (Chat.recipient_id == user_id)
    ).all()
    implicit_chat_ids = {c.id for c in implicit_chats}

    # Ensure membership rows for implicit chats (idempotent backfill for current user)
    for chat in implicit_chats:
        try:
            _ensure_user_membership(db, chat.id, chat.creator_id)
            _ensure_user_membership(db, chat.id, chat.recipient_id)
        except Exception as e:
            logger.error(f"⚠️ Failed to ensure membership for chat {chat.id}: {e}")

    # Union of both
    all_chat_ids = list(member_chat_ids | implicit_chat_ids)
    if not all_chat_ids:
        logger.info("🔍 No chats found for user")
        return []

    chats = db.query(Chat).filter(
        Chat.id.in_(all_chat_ids)
    ).all()
    logger.info(f"🔍 Chats found: {[c.id for c in chats]}")
    return chats

def get_chat_participants(db: Session, chat_id: int) -> List[User]:
    """Отримання учасників приватного чату"""
    members = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.status == MemberStatus.ACTIVE
    ).all()
    
    user_ids = [member.user_id for member in members]
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    
    return users

def is_user_in_chat(db: Session, chat_id: int, user_id: int) -> bool:
    """Перевірка, чи користувач є учасником чату"""
    logger.info(f"🔍 Checking if user {user_id} is in chat {chat_id}")
    # Fast path: explicit membership row exists
    member = db.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == user_id,
        ChatMember.status == MemberStatus.ACTIVE
    ).first()
    if member:
        logger.info("🔍 Member row exists: True")
        return True

    # Fallback for private chats: user is creator or recipient
    # Avoid enum comparison to tolerate legacy rows
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        logger.info("🔍 Chat not found or not private")
        return False

    if chat.creator_id == user_id or chat.recipient_id == user_id:
        logger.info("🔍 Implicit membership via chat creator/recipient: True")
        # Best-effort: ensure membership row for future queries
        try:
            _ensure_user_membership(db, chat_id, user_id)
        except Exception as e:
            logger.error(f"⚠️ Failed to ensure membership row: {e}")
        return True

    logger.info("🔍 User is NOT in chat")
    return False
