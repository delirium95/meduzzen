from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from database import get_db, engine, SessionLocal
from models import UserCreate, UserResponse, UserLogin, User, Token, ChatCreate, ChatResponse, MessageCreate, MessageResponse
from auth import create_access_token, get_current_active_user, add_token_to_blacklist
from chat_operations import (
    create_private_chat, get_or_create_private_chat, send_message, edit_message, 
    delete_message, upload_file, get_chat_messages, get_user_chats, 
    get_chat_participants, is_user_in_chat
)
from datetime import timedelta
import os

# Створюємо таблиці в базі даних
from models import Base
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure memberships exist for all chats (idempotent)
    try:
        from database import SessionLocal as _SessionLocal
        from models import Chat as _Chat
        from chat_operations import _ensure_user_membership as _ensure
        db = _SessionLocal()
        chats = db.query(_Chat).all()
        for chat in chats:
            _ensure(db, chat.id, chat.creator_id)
            _ensure(db, chat.id, chat.recipient_id)
    except Exception as e:
        print(f"⚠️ Startup membership ensure failed: {e}")
    finally:
        try:
            db.close()
        except Exception:
            pass
    yield

app = FastAPI(
    title="Meduzzen Messenger",
    description="Веб-додаток месенджер з приватними чатами один-на-один",
    version="1.0.0",
    lifespan=lifespan
)

# Додаємо CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Підключаємо статичні файли
app.mount("/static", StaticFiles(directory="static"), name="static")

security = HTTPBearer()

# Конфігурація JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 30

@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Реєстрація нового користувача"""
    # Перевіряємо, чи користувач вже існує
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Хешуємо пароль
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(user.password)
    
    # Створюємо користувача
    db_user = User(
        username=user.username,
        email=user.email,
        password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Авторизація користувача"""
    # Знаходимо користувача по email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Перевіряємо пароль
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    if not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Створюємо токен
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/logout")
def logout(credentials: HTTPBearer = Depends(security), db: Session = Depends(get_db)):
    """Вихід з системи (додавання токена в чорний список)"""
    add_token_to_blacklist(credentials.credentials, db)
    return {"message": "Successfully logged out"}

@app.get("/users", response_model=list[UserResponse])
def get_users(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Отримання списку всіх користувачів (для вибору чату)"""
    users = db.query(User).filter(User.id != current_user.id).all()
    return users

@app.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Отримання інформації про поточного користувача"""
    return current_user

@app.get("/protected")
def protected_route(current_user: User = Depends(get_current_active_user)):
    """Захищений маршрут для тестування"""
    return {
        "message": "This is a protected route",
        "username": current_user.username
    }

# Chat endpoints
@app.post("/chats", response_model=ChatResponse)
def create_chat(chat: ChatCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Створення приватного чату з іншим користувачем"""
    print(f"🔍 API: Creating chat - current_user_id={current_user.id}, recipient_id={chat.recipient_id}")
    try:
        result = create_private_chat(db, current_user.id, chat.recipient_id)
        print(f"🔍 API: Chat created - {result}")
        return result
    except Exception as e:
        print(f"❌ API: Error creating chat - {e}")
        import traceback
        traceback.print_exc()
        raise

@app.get("/chats", response_model=list[ChatResponse])
def get_chats(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Отримання всіх приватних чатів користувача"""
    print(f"🔍 API: Getting chats for user {current_user.id}")
    try:
        result = get_user_chats(db, current_user.id)
        print(f"🔍 API: Chats found: {[c.id for c in result]}")
        return result
    except Exception as e:
        print(f"❌ API: Error getting chats - {e}")
        import traceback
        traceback.print_exc()
        raise

@app.get("/chats/{chat_id}/participants", response_model=list[UserResponse])
def get_chat_participants_endpoint(
    chat_id: int, 
    current_user: User = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """Отримання учасників приватного чату"""
    # Перевіряємо, чи користувач є учасником чату
    if not is_user_in_chat(db, chat_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat"
        )
    
    participants = get_chat_participants(db, chat_id)
    return participants

@app.post("/chats/{chat_id}/messages", response_model=MessageResponse)
def send_message_endpoint(
    chat_id: int,
    message: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Відправлення повідомлення в приватний чат"""
    print(f"🔍 API: Sending message to chat {chat_id}, user {current_user.id}")
    # Перевіряємо, чи користувач є учасником чату
    try:
        is_member = is_user_in_chat(db, chat_id, current_user.id)
        print(f"🔍 API: User {current_user.id} is member of chat {chat_id}: {is_member}")
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this chat"
            )
        
        message_data = message.dict()
        message_data["chat_id"] = chat_id
        result = send_message(db, message_data, current_user.id)
        print(f"🔍 API: Message sent successfully: {result.id}")
        return result
    except Exception as e:
        print(f"❌ API: Error sending message - {e}")
        import traceback
        traceback.print_exc()
        raise

@app.get("/chats/{chat_id}/messages", response_model=list[MessageResponse])
def get_chat_messages_endpoint(
    chat_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Отримання повідомлень приватного чату"""
    print(f"🔍 API: Getting messages for chat {chat_id}, user {current_user.id}")
    # Перевіряємо, чи користувач є учасником чату
    try:
        is_member = is_user_in_chat(db, chat_id, current_user.id)
        print(f"🔍 API: User {current_user.id} is member of chat {chat_id}: {is_member}")
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this chat"
            )
        
        messages = get_chat_messages(db, chat_id, skip, limit)
        print(f"🔍 API: Found {len(messages)} messages")
        return messages
    except Exception as e:
        print(f"❌ API: Error getting messages - {e}")
        import traceback
        traceback.print_exc()
        raise

@app.put("/messages/{message_id}")
def edit_message_endpoint(
    message_id: int,
    new_content: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Редагування повідомлення"""
    return edit_message(db, message_id, new_content, current_user.id)

@app.delete("/messages/{message_id}")
def delete_message_endpoint(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Видалення повідомлення (soft delete)"""
    delete_message(db, message_id, current_user.id)
    return {"message": "Message deleted successfully"}

@app.post("/messages/{message_id}/files", response_model=dict)
def upload_file_endpoint(
    message_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Завантаження файлу до повідомлення"""
    # TODO: Додати перевірку, чи користувач може завантажувати файли до цього повідомлення
    attachment = upload_file(db, file, message_id)
    return {
        "message": "File uploaded successfully",
        "file_id": attachment.id,
        "filename": attachment.filename
    }

@app.get("/files/{file_id}")
async def download_file(file_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Завантаження файлу (TODO: реалізувати)"""
    # TODO: Реалізувати завантаження файлу з перевіркою прав доступу
    return {"message": "File download not implemented yet"}

@app.get("/")
def read_root():
    """Головна сторінка - повертає веб-інтерфейс"""
    return FileResponse('static/index.html')
    