import os
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.db import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    name = Column(String)
    role = Column(String, default='admin')  # 'admin' or 'user'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    listings = relationship('Listing', back_populates='agent')

class Listing(Base):
    __tablename__ = 'listings'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, index=True)
    description = Column(Text)
    title_en = Column(String, nullable=True)
    description_en = Column(Text, nullable=True)
    price = Column(Float)
    location = Column(String)
    address = Column(String)
    city = Column(String, index=True)
    state = Column(String)
    zip_code = Column(String)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    size_sqft = Column(Integer)
    property_type = Column(String)  # house, condo, apartment, townhouse
    listing_type = Column(String, default='sale', index=True)  # sale, rent
    featured = Column(Boolean, default=False, index=True)
    featured_order = Column(Integer, nullable=True, index=True)  # explicit ordering for featured listings
    agent_id = Column(String, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images = relationship('ListingImage', back_populates='listing', cascade='all, delete-orphan')
    agent = relationship('User', back_populates='listings')

class ListingImage(Base):
    __tablename__ = 'listing_images'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id = Column(String, ForeignKey('listings.id', ondelete='CASCADE'), index=True)
    image_url = Column(String)
    alt_text = Column(String, nullable=True)
    is_primary = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship('Listing', back_populates='images')


class AboutContent(Base):
    __tablename__ = 'about_content'

    id = Column(Integer, primary_key=True, default=1)
    title = Column(String, default='O nama')
    intro = Column(Text, default='S više od 15 godina iskustva u industriji nekretnina, posvećeni smo pomaganju klijentima da pronađu svoj dom iz snova i naprave pametne investicije u nekretnine.')
    mission_title = Column(String, default='Naša misija')
    mission_text = Column(Text, default='Pružiti iznimne usluge u području nekretnina s integritetom, transparentnošću i predanošću premašivanju očekivanja klijenata.')
    why_title = Column(String, default='Zašto odabrati nas?')
    why_items = Column(Text, default='Stručni agenti s detaljnim poznavanjem tržišta|Sveobuhvatni popisi i informacije o nekretninama|Profesionalno vodstvo kroz svaki korak|Predanost zadovoljstvu klijenata')
    contact_title = Column(String, default='Kontaktirajte nas')
    contact_text = Column(Text, default='Imate pitanja? Kontaktirajte nas danas kako biste saznali više o našim uslugama.')
    title_en = Column(String, nullable=True)
    intro_en = Column(Text, nullable=True)
    mission_title_en = Column(String, nullable=True)
    mission_text_en = Column(Text, nullable=True)
    why_title_en = Column(String, nullable=True)
    why_items_en = Column(Text, nullable=True)
    contact_title_en = Column(String, nullable=True)
    contact_text_en = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContactContent(Base):
    __tablename__ = 'contact_content'

    id = Column(Integer, primary_key=True, default=1)
    title = Column(String, default='Kontaktirajte nas')
    subtitle = Column(Text, default='Javite nam se putem bilo kojeg od kanala ispod.')
    title_en = Column(String, nullable=True)
    subtitle_en = Column(Text, nullable=True)
    address = Column(String, default='Madijevaca 3, Zadar')
    phone = Column(String, default='+385 98 893 547')
    email = Column(String, default='padriarealestate@gmail.com')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
