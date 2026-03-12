"""
Script to mark some listings as featured
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.database.db import SessionLocal
from app.models.models import Listing
from sqlalchemy import func

def mark_featured_listings(num_listings=6):
    """Mark the newest listings as featured"""
    db = SessionLocal()
    try:
        # Get the newest active listings
        listings = db.query(Listing).filter(
            Listing.status == 'active'
        ).order_by(Listing.created_at.desc()).limit(num_listings).all()
        
        if not listings:
            print("No active listings found in database.")
            return
        
        print(f"Marking {len(listings)} listings as featured...")
        
        for listing in listings:
            listing.featured = True
            print(f"  ✓ {listing.title} - {listing.city}")
        
        db.commit()
        print(f"\n✅ Successfully marked {len(listings)} listings as featured!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    mark_featured_listings()
