from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Token blacklist for logout (in-memory storage)
# For production with multiple instances, use Redis or database
token_blacklist = set()

def hash_password(password: str) -> str:
    # Encode and truncate to 72 bytes (bcrypt limit)
    password_bytes = password.encode('utf-8')[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Encode and truncate to 72 bytes (bcrypt limit)
    password_bytes = plain_password.encode('utf-8')[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def is_token_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted (logged out)."""
    return token in token_blacklist

def blacklist_token(token: str) -> None:
    """Add a token to the blacklist when user logs out."""
    token_blacklist.add(token)

def verify_token(token: str) -> dict:
    try:
        # Check if token is blacklisted
        if is_token_blacklisted(token):
            return None
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
