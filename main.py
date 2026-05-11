from fastapi import FastAPI, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from app.database.db import engine, Base, SessionLocal
from app.models.models import User, Listing, ListingImage, AboutContent, ContactContent
from app.routes import auth, listings, about, contact
from app.core.security import hash_password
from app.core.config import CORS_ORIGINS, ADMIN_EMAIL, ADMIN_PASSWORD

# Create tables
Base.metadata.create_all(bind=engine)

# Create default admin user if not exists
def create_default_admin():
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not existing_admin:
            admin_user = User(
                email=ADMIN_EMAIL,
                hashed_password=hash_password(ADMIN_PASSWORD),
                name='Admin',
                role='admin'
            )
            db.add(admin_user)
            db.commit()
            print(f"Default admin user created: {ADMIN_EMAIL}")
        else:
            existing_admin.hashed_password = hash_password(ADMIN_PASSWORD)
            db.commit()
            print(f"Default admin password synced from .env: {ADMIN_EMAIL}")
    finally:
        db.close()

create_default_admin()

app = FastAPI(title='Real Estate API', version='1.0.0')

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS.split(',')],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Include routes
app.include_router(auth.router)
app.include_router(listings.router)
app.include_router(about.router)
app.include_router(contact.router)

# Extract token from Authorization header
def get_token(authorization: str = Header(None)):
    if authorization and authorization.startswith('Bearer '):
        return authorization[7:]
    return None

@app.get('/')
def root():
    return {
        'message': 'Real Estate Agency API',
        'version': '1.0.0',
        'docs': '/docs'
    }

@app.get('/health')
def health_check():
    return {'status': 'ok'}
