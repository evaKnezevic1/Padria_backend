"""
Migration: Add featured_order column to listings table
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.database.db import engine, SessionLocal
from app.models.models import Listing
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        # Check if column already exists and add if needed
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='listings' AND column_name='featured_order'"
            ))
            if result.fetchone():
                print("Column 'featured_order' already exists. Skipping DDL.")
            else:
                conn.execute(text("ALTER TABLE listings ADD COLUMN featured_order INTEGER"))
                conn.commit()
                print("Added 'featured_order' column to listings table.")

        # Assign sequential order to existing featured listings that lack one
        featured = (
            db.query(Listing)
            .filter(Listing.featured == True, Listing.featured_order == None)
            .order_by(Listing.created_at.asc())
            .all()
        )

        if featured:
            # Find the current max order
            max_order = (
                db.query(Listing.featured_order)
                .filter(Listing.featured == True, Listing.featured_order != None)
                .order_by(Listing.featured_order.desc())
                .first()
            )
            next_order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0

            for listing in featured:
                listing.featured_order = next_order
                next_order += 1

            db.commit()
            print(f"Assigned featured_order to {len(featured)} existing featured listings.")
        else:
            print("No featured listings without an order found.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
