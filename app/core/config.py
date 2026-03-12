import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7 days

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

# Google Maps API Key for geocoding
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')

# Supabase Storage
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'listing-images')

# CORS
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000')

# Default admin credentials
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'password')
