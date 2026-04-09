from fastapi import APIRouter, Depends, HTTPException, Header, Cookie, UploadFile, File
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.models import AboutContent, User
from app.schemas.schemas import AboutContentSchema, AboutContentUpdateSchema
from app.core.security import verify_token
from app.utils.image_handler import save_upload_file, delete_upload_file_sync
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


@router.post('/image', response_model=AboutContentSchema)
async def replace_about_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Replace About Us image (admin only).

    The old image URL in database is replaced with a new one and then the old
    storage object is deleted.
    """
    content = get_or_create_about(db)
    old_image_url = content.about_image_url

    try:
        new_image_url = await save_upload_file(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error uploading file: {str(e)}')

    try:
        content.about_image_url = new_image_url
        db.commit()
        db.refresh(content)
    except Exception:
        db.rollback()
        try:
            delete_upload_file_sync(new_image_url)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail='Failed to save about image')

    if old_image_url and old_image_url != new_image_url:
        try:
            delete_upload_file_sync(old_image_url)
        except Exception:
            pass

    return content
