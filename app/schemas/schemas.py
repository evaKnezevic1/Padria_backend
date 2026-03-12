from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ListingImageSchema(BaseModel):
    id: str
    image_url: str
    alt_text: Optional[str] = None
    is_primary: bool
    order: int
    created_at: datetime

    class Config:
        from_attributes = True

class ListingCreateSchema(BaseModel):
    title: str
    description: str
    title_en: Optional[str] = None
    description_en: Optional[str] = None
    price: float
    location: str
    address: str
    city: str
    state: str
    zip_code: str
    bedrooms: int
    bathrooms: int
    size_sqft: int
    property_type: str
    listing_type: str = 'sale'
    featured: bool = False
    featured_order: Optional[int] = None

class ListingUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    title_en: Optional[str] = None
    description_en: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    size_sqft: Optional[int] = None
    property_type: Optional[str] = None
    listing_type: Optional[str] = None
    featured: Optional[bool] = None
    featured_order: Optional[int] = None

class ListingSchema(BaseModel):
    id: str
    title: str
    description: str
    title_en: Optional[str] = None
    description_en: Optional[str] = None
    price: float
    location: str
    address: str
    city: str
    state: str
    zip_code: str
    bedrooms: int
    bathrooms: int
    size_sqft: int
    property_type: str
    listing_type: str
    featured: bool
    featured_order: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    images: List[ListingImageSchema] = []

    class Config:
        from_attributes = True

class UserCreateSchema(BaseModel):
    email: str
    password: str
    name: str

class UserSchema(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class LoginSchema(BaseModel):
    email: str
    password: str

class TokenSchema(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: UserSchema

class PaginatedListingSchema(BaseModel):
    data: List[ListingSchema]
    total: int
    page: int
    page_size: int
    total_pages: int

class AboutContentSchema(BaseModel):
    id: int
    title: str
    intro: str
    mission_title: str
    mission_text: str
    why_title: str
    why_items: str
    contact_title: str
    contact_text: str
    title_en: Optional[str] = None
    intro_en: Optional[str] = None
    mission_title_en: Optional[str] = None
    mission_text_en: Optional[str] = None
    why_title_en: Optional[str] = None
    why_items_en: Optional[str] = None
    contact_title_en: Optional[str] = None
    contact_text_en: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AboutContentUpdateSchema(BaseModel):
    title: Optional[str] = None
    intro: Optional[str] = None
    mission_title: Optional[str] = None
    mission_text: Optional[str] = None
    why_title: Optional[str] = None
    why_items: Optional[str] = None
    contact_title: Optional[str] = None
    contact_text: Optional[str] = None
    title_en: Optional[str] = None
    intro_en: Optional[str] = None
    mission_title_en: Optional[str] = None
    mission_text_en: Optional[str] = None
    why_title_en: Optional[str] = None
    why_items_en: Optional[str] = None
    contact_title_en: Optional[str] = None
    contact_text_en: Optional[str] = None


class ContactContentSchema(BaseModel):
    id: int
    title: str
    subtitle: str
    title_en: Optional[str] = None
    subtitle_en: Optional[str] = None
    address: str
    phone: str
    email: str
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContactContentUpdateSchema(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    title_en: Optional[str] = None
    subtitle_en: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
