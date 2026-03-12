"""
Migration script to remove condo and townhouse property types
This script will delete all listings with property_type='condo' or 'townhouse'
Run this once after updating the models to remove unsupported property types
"""

from app.database.db import SessionLocal
from app.models.models import Listing
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        # Find and delete condo listings
        condo_count = db.query(Listing).filter(Listing.property_type == 'condo').count()
        if condo_count > 0:
            print(f"Removing {condo_count} condo listings...")
            db.query(Listing).filter(Listing.property_type == 'condo').delete()
            print(f"✓ Successfully removed {condo_count} condo listings")
        
        # Find and delete townhouse listings
        townhouse_count = db.query(Listing).filter(Listing.property_type == 'townhouse').count()
        if townhouse_count > 0:
            print(f"Removing {townhouse_count} townhouse listings...")
            db.query(Listing).filter(Listing.property_type == 'townhouse').delete()
            print(f"✓ Successfully removed {townhouse_count} townhouse listings")
        
        db.commit()
        
        # Show remaining property types
        remaining = db.query(Listing.property_type).distinct().all()
        print("\nRemaining property types in database:")
        for prop_type in remaining:
            count = db.query(Listing).filter(Listing.property_type == prop_type[0]).count()
            print(f"  - {prop_type[0]}: {count} listings")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    migrate()
