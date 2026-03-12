from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query, Header, Body, Cookie, Request
from sqlalchemy.orm import Session, joinedload, subqueryload
from sqlalchemy import and_, or_, func, case
from app.database.db import get_db
import time
import logging

perf_logger = logging.getLogger("perf")
from app.models.models import Listing, ListingImage, User
from app.schemas.schemas import ListingCreateSchema, ListingUpdateSchema, ListingSchema, PaginatedListingSchema
from app.core.security import verify_token
from app.utils.image_handler import save_upload_file, delete_upload_file_sync
from app.utils.location_handler import get_approximate_location
from typing import Optional, List

router = APIRouter(prefix='/api/listings', tags=['listings'])

def get_current_user(authorization: str = Header(None), adminToken: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    """Get current admin user from token (cookie or Authorization header)"""
    token = None
    if authorization and authorization.startswith('Bearer '):
        token = authorization[7:]
    elif adminToken:
        token = adminToken
    
    if not token:
        return None
    
    payload = verify_token(token)
    if not payload:
        return None
    
    user = db.query(User).filter(User.id == payload.get('sub')).first()
    return user

@router.get('', response_model=PaginatedListingSchema)
def get_listings(
    skip: int = Query(0, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    location: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[int] = None,
    property_type: Optional[str] = None,
    listing_type: Optional[str] = None,
    featured: Optional[bool] = None,
    sort_by: Optional[str] = 'newest',
    db: Session = Depends(get_db)
):
    """Get listings with filters and pagination"""
    t0 = time.perf_counter()
    query = db.query(Listing).options(subqueryload(Listing.images))

    # Apply filters
    if location:
        query = query.filter(
            or_(
                Listing.city.ilike(f'%{location}%'),
                Listing.state.ilike(f'%{location}%'),
                Listing.zip_code.ilike(f'%{location}%'),
                Listing.address.ilike(f'%{location}%')
            )
        )
    
    if min_price is not None:
        query = query.filter(Listing.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Listing.price <= max_price)
    
    if bedrooms is not None:
        query = query.filter(Listing.bedrooms >= bedrooms)
    
    if bathrooms is not None:
        query = query.filter(Listing.bathrooms >= bathrooms)
    
    if property_type:
        query = query.filter(Listing.property_type == property_type)

    if listing_type:
        query = query.filter(Listing.listing_type == listing_type)
    
    if featured is not None:
        query = query.filter(Listing.featured == featured)

    # Count total
    total = query.count()

    # Sort
    if sort_by == 'price_asc':
        query = query.order_by(Listing.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Listing.price.desc())
    elif sort_by == 'featured':
        query = query.order_by(Listing.featured_order.asc().nullslast(), Listing.created_at.desc())
    else:  # newest
        query = query.order_by(Listing.created_at.desc())

    # Pagination
    total_pages = (total + page_size - 1) // page_size
    listings = query.offset((page - 1) * page_size).limit(page_size).all()
    perf_logger.info(f"get_listings query took {(time.perf_counter()-t0)*1000:.1f}ms, returned {len(listings)} listings")

    return {
        'data': listings,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    }


@router.put('/featured/reorder')
def reorder_featured_listings(
    ordered_ids: List[str] = Body(..., description="List of listing IDs in desired display order"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Set the display order of featured listings atomically.
    Accepts a JSON array of listing-IDs in the desired order.
    The first ID gets featured_order=0, the second 1, etc.
    """
    if not current_user or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail='Not authorized')

    if not ordered_ids:
        raise HTTPException(status_code=400, detail='ordered_ids must not be empty')

    # Verify all supplied IDs are currently featured
    featured_listings = db.query(Listing).filter(
        Listing.id.in_(ordered_ids),
        Listing.featured == True,
    ).all()

    found_ids = {l.id for l in featured_listings}
    missing = set(ordered_ids) - found_ids
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f'These IDs are not featured listings: {list(missing)}'
        )

    # Check for duplicates in the request
    if len(ordered_ids) != len(set(ordered_ids)):
        raise HTTPException(status_code=400, detail='Duplicate listing IDs')

    # Build a map for O(1) lookup
    listing_map = {l.id: l for l in featured_listings}

    # Assign new sequential order
    for position, lid in enumerate(ordered_ids):
        listing_map[lid].featured_order = position

    db.commit()
    return {'message': 'Featured listings reorder saved', 'count': len(ordered_ids)}


@router.get('/{listing_id}', response_model=ListingSchema)
def get_listing(listing_id: str, db: Session = Depends(get_db)):
    """Get a specific listing"""
    listing = db.query(Listing).options(joinedload(Listing.images)).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail='Listing not found')
    return listing

@router.post('', response_model=ListingSchema)
def create_listing(
    listing_data: ListingCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new listing (admin only)"""
    if not current_user or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail='Not authorized')

    new_listing = Listing(**listing_data.dict())
    new_listing.agent_id = current_user.id

    # Auto-assign featured_order if marked as featured
    if new_listing.featured:
        max_order = db.query(func.max(Listing.featured_order)).filter(
            Listing.featured == True
        ).scalar()
        new_listing.featured_order = (max_order + 1) if max_order is not None else 0
    else:
        new_listing.featured_order = None

    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)
    return new_listing

@router.put('/{listing_id}', response_model=ListingSchema)
def update_listing(
    listing_id: str,
    listing_data: ListingUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a listing (admin only)"""
    if not current_user or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail='Not authorized')

    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail='Listing not found')

    update_data = listing_data.dict(exclude_unset=True)
    was_featured = listing.featured
    becoming_featured = update_data.get('featured', was_featured)

    for field, value in update_data.items():
        setattr(listing, field, value)

    # Handle featured_order transitions
    if becoming_featured and not was_featured:
        max_order = db.query(func.max(Listing.featured_order)).filter(
            Listing.featured == True
        ).scalar()
        listing.featured_order = (max_order + 1) if max_order is not None else 0
    elif not becoming_featured and was_featured:
        _compact_featured_order(db, exclude_id=listing_id)
        listing.featured_order = None

    db.commit()
    db.refresh(listing)
    return listing

@router.patch('/{listing_id}', response_model=ListingSchema)
def patch_listing(
    listing_id: str,
    listing_data: ListingUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Partially update a listing (admin only)"""
    if not current_user or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail='Not authorized')

    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail='Listing not found')

    update_data = listing_data.dict(exclude_unset=True)
    was_featured = listing.featured

    for field, value in update_data.items():
        if value is not None:
            setattr(listing, field, value)

    becoming_featured = listing.featured
    # Handle featured_order transitions
    if becoming_featured and not was_featured:
        max_order = db.query(func.max(Listing.featured_order)).filter(
            Listing.featured == True
        ).scalar()
        listing.featured_order = (max_order + 1) if max_order is not None else 0
    elif not becoming_featured and was_featured:
        _compact_featured_order(db, exclude_id=listing_id)
        listing.featured_order = None

    db.commit()
    db.refresh(listing)
    return listing

@router.delete('/{listing_id}')
def delete_listing(
    listing_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a listing (admin only)"""
    if not current_user or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail='Not authorized')

    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail='Listing not found')

    was_featured = listing.featured
    db.delete(listing)
    db.flush()

    # Compact the ordering so there are no gaps
    if was_featured:
        _compact_featured_order(db)

    db.commit()
    return {'message': 'Listing deleted successfully'}

@router.get('/{listing_id}/images')
def get_listing_images(listing_id: str, db: Session = Depends(get_db)):
    """Get all images for a listing"""
    images = db.query(ListingImage).filter(
        ListingImage.listing_id == listing_id
    ).order_by(ListingImage.order).all()
    return images

@router.get('/{listing_id}/image')
def get_primary_listing_image(listing_id: str, db: Session = Depends(get_db)):
    """Get primary image for a listing"""
    # Single query: prefer primary image, fallback to lowest order
    image = db.query(ListingImage).filter(
        ListingImage.listing_id == listing_id
    ).order_by(
        case((ListingImage.is_primary == True, 0), else_=1),
        ListingImage.order
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail='No images found')
    
    return image

@router.post('/{listing_id}/images')
async def upload_listing_images(
    listing_id: str,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload images for a listing (admin only)"""
    if not current_user or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail='Not authorized')

    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail='Listing not found')

    uploaded_images = []
    for idx, file in enumerate(files):
        try:
            image_url = await save_upload_file(file)
            
            is_primary = idx == 0 and not db.query(ListingImage).filter(
                ListingImage.listing_id == listing_id
            ).first()
            
            new_image = ListingImage(
                listing_id=listing_id,
                image_url=image_url,
                is_primary=is_primary,
                order=idx
            )
            db.add(new_image)
            uploaded_images.append(new_image)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f'Error uploading file: {str(e)}')
    
    db.commit()
    for img in uploaded_images:
        db.refresh(img)
    
    return uploaded_images

@router.delete('/{listing_id}/images/{image_id}')
def delete_listing_image(
    listing_id: str,
    image_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an image from a listing (admin only)"""
    if not current_user or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail='Not authorized')

    image = db.query(ListingImage).filter(
        and_(
            ListingImage.id == image_id,
            ListingImage.listing_id == listing_id
        )
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail='Image not found')

    # Delete file from Supabase Storage
    try:
        delete_upload_file_sync(image.image_url)
    except Exception:
        pass

    db.delete(image)
    db.commit()
    return {'message': 'Image deleted successfully'}


# ── Featured listing reorder helpers ──────────────────────────────────

def _compact_featured_order(db: Session, exclude_id: str | None = None):
    """Re-number featured listings so positions are 0, 1, 2, … with no gaps.
    Called inside an open transaction (caller must commit)."""
    q = db.query(Listing).filter(
        Listing.featured == True,
        Listing.featured_order != None,
    )
    if exclude_id:
        q = q.filter(Listing.id != exclude_id)
    featured = q.order_by(Listing.featured_order.asc()).all()
    for idx, listing in enumerate(featured):
        listing.featured_order = idx


@router.get('/{listing_id}/approximate-location')
def get_listing_approximate_location(
    listing_id: str,
    db: Session = Depends(get_db)
):
    """
    Get approximate location for a listing.
    
    Returns shifted coordinates with a radius for displaying an approximate
    area on a map. The real coordinates are NEVER exposed.
    
    The location is deterministic based on listing ID - same request
    always returns the same approximate location.
    
    Returns:
        {
            "lat": float,  # Shifted latitude (150-350m from real location)
            "lng": float,  # Shifted longitude
            "radius": int  # Circle radius in meters (400-600m)
        }
    """
    # Get the listing to retrieve address info
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    
    if not listing:
        raise HTTPException(status_code=404, detail='Listing not found')
    
    # Get approximate location - address may be empty, city is used as fallback
    approximate_location = get_approximate_location(
        listing_id=listing.id,
        address=listing.address or "",
        city=listing.city or "",
        country="Croatia"
    )
    
    if not approximate_location:
        raise HTTPException(
            status_code=503,
            detail='Unable to determine location. Please check the address or try again later.'
        )
    
    return approximate_location



