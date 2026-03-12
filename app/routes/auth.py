from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.models import User
from app.schemas.schemas import UserCreateSchema, LoginSchema, TokenSchema, UserSchema
from app.core.security import hash_password, verify_password, create_access_token, blacklist_token
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from typing import Optional

router = APIRouter(prefix='/api/admin', tags=['admin'])

COOKIE_NAME = 'adminToken'
COOKIE_MAX_AGE = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds

@router.post('/register', response_model=TokenSchema)
def register(user_data: UserCreateSchema, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail='Email already registered')
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        name=user_data.name,
        role='admin'
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create token
    access_token = create_access_token(
        data={'sub': new_user.id, 'email': new_user.email}
    )
    
    return {
        'access_token': access_token,
        'token_type': 'bearer',
        'user': UserSchema.from_orm(new_user)
    }

@router.post('/login')
def login(credentials: LoginSchema, response: Response, db: Session = Depends(get_db)):
    try:
        print(f"[LOGIN] Attempting login for email: {credentials.email}")
        
        # Find user
        user = db.query(User).filter(User.email == credentials.email).first()
        if not user:
            print(f"[LOGIN] User not found: {credentials.email}")
            raise HTTPException(status_code=401, detail='Invalid credentials')
        
        print(f"[LOGIN] User found: {credentials.email}")
        
        # Verify password
        if not verify_password(credentials.password, user.hashed_password):
            print(f"[LOGIN] Password verification failed for: {credentials.email}")
            raise HTTPException(status_code=401, detail='Invalid credentials')
        
        print(f"[LOGIN] Password verified for: {credentials.email}")
        
        # Create token
        access_token = create_access_token(
            data={'sub': user.id, 'email': user.email}
        )
        
        print(f"[LOGIN] Token created for: {credentials.email}")
        
        # Set HTTP-only cookie
        response.set_cookie(
            key=COOKIE_NAME,
            value=access_token,
            httponly=True,
            secure=True,
            samesite='none',
            max_age=COOKIE_MAX_AGE,
            path='/',
        )
        
        user_schema = UserSchema.from_orm(user)
        return {
            'message': 'Login successful',
            'user': user_schema.dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[LOGIN ERROR] Exception during login: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@router.get('/me', response_model=UserSchema)
def get_current_user_route(request: Request, db: Session = Depends(get_db), adminToken: Optional[str] = Cookie(None)):
    from app.core.security import verify_token
    token = adminToken
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid token')
    
    user = db.query(User).filter(User.id == payload.get('sub')).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    
    return user

@router.post('/logout')
def logout(response: Response, adminToken: Optional[str] = Cookie(None)):
    # Blacklist the token if it exists
    if adminToken:
        blacklist_token(adminToken)
    
    # Clear the cookie
    response.delete_cookie(key=COOKIE_NAME, path='/')
    return {'message': 'Logged out successfully'}
