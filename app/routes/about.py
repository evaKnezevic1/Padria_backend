from fastapi import APIRouter, Depends, HTTPException, Header, Cookie
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.models import AboutContent, User
from app.schemas.schemas import AboutContentSchema, AboutContentUpdateSchema
from app.core.security import verify_token
from typing import Optional

router = APIRouter(prefix='/api/about', tags=['about'])


def get_admin_user(authorization: str = Header(None), adminToken: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    """Require admin user from token (cookie or Authorization header)"""
    token = None
    if authorization and authorization.startswith('Bearer '):
        token = authorization[7:]
    elif adminToken:
        token = adminToken
    
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid token')
    user = db.query(User).filter(User.id == payload.get('sub')).first()
    if not user or user.role != 'admin':
        raise HTTPException(status_code=403, detail='Admin access required')
    return user


def get_or_create_about(db: Session) -> AboutContent:
    content = db.query(AboutContent).filter(AboutContent.id == 1).first()
    if not content:
        content = AboutContent(id=1)
        db.add(content)
        db.commit()
        db.refresh(content)
    return content


@router.get('', response_model=AboutContentSchema)
def get_about(db: Session = Depends(get_db)):
    """Get About Us content (public)"""
    return get_or_create_about(db)


@router.put('', response_model=AboutContentSchema)
def update_about(
    data: AboutContentUpdateSchema,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Update About Us content (admin only)"""
    content = get_or_create_about(db)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(content, field, value)
    db.commit()
    db.refresh(content)
    return content
