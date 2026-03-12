from fastapi import APIRouter, Depends, HTTPException, Header, Cookie
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.models import ContactContent, User
from app.schemas.schemas import ContactContentSchema, ContactContentUpdateSchema
from app.core.security import verify_token
from typing import Optional

router = APIRouter(prefix='/api/contact', tags=['contact'])


def get_admin_user(authorization: str = Header(None), adminToken: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
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


def get_or_create_contact(db: Session) -> ContactContent:
    content = db.query(ContactContent).filter(ContactContent.id == 1).first()
    if not content:
        content = ContactContent(id=1)
        db.add(content)
        db.commit()
        db.refresh(content)
    return content


@router.get('', response_model=ContactContentSchema)
def get_contact(db: Session = Depends(get_db)):
    """Get contact info (public)"""
    return get_or_create_contact(db)


@router.put('', response_model=ContactContentSchema)
def update_contact(
    data: ContactContentUpdateSchema,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Update contact info (admin only)"""
    content = get_or_create_contact(db)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(content, field, value)
    db.commit()
    db.refresh(content)
    return content
