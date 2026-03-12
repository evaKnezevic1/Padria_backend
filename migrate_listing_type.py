"""
Migration script to add listing_type column to existing listings table
Run this once after updating the models
"""

from app.database.db import SessionLocal, engine
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        # Check if column exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='listings' AND column_name='listing_type'
        """))
        
        if result.fetchone() is None:
            print("Adding listing_type column to listings table...")
            # Add the column with default value 'sale'
            db.execute(text("""
                ALTER TABLE listings 
                ADD COLUMN listing_type VARCHAR DEFAULT 'sale'
            """))
            
            # Create index on the new column
            db.execute(text("""
                CREATE INDEX ix_listings_listing_type ON listings (listing_type)
            """))
            
            db.commit()
            print("✓ Successfully added listing_type column")
        else:
            print("✓ listing_type column already exists")
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    migrate()
