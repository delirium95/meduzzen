from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from database import get_db
from models import User, BlacklistedToken

SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Створення JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, db: Session) -> Optional[dict]:
    """Перевірка JWT токена"""
    try:
        if is_token_blacklisted(token, db):
            return None
            
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return payload
    except JWTError:
        return None

def is_token_blacklisted(token: str, db: Session) -> bool:
    """Перевірка, чи токен в чорному списку"""
    blacklisted = db.query(BlacklistedToken).filter(
        BlacklistedToken.token == token
    ).first()
    return blacklisted is not None

def add_token_to_blacklist(token: str, db: Session):
    """Додавання токена в чорний список"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            expires_at = datetime.fromtimestamp(exp_timestamp)
        else:
            expires_at = datetime.utcnow() + timedelta(hours=1)
    except:
        expires_at = datetime.utcnow() + timedelta(hours=1)
    
    blacklisted_token = BlacklistedToken(
        token=token,
        expires_at=expires_at
    )
    db.add(blacklisted_token)
    db.commit()

def get_current_user(token: str = Depends(security), db: Session = Depends(get_db)) -> User:
    """Отримання поточного користувача з токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token.credentials, db)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == username).first()
    if user is None:
        raise credentials_exception
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Отримання активного користувача"""
    if not current_user:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
