"""
Migration: Drop lot_size_sqft, year_built, and status columns from listings table
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.database.db import engine
from sqlalchemy import text

COLUMNS_TO_DROP = ['lot_size_sqft', 'year_built', 'status']

def migrate():
    with engine.connect() as conn:
        # Check which columns exist before attempting to drop them
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='listings' AND column_name = ANY(:cols)"
        ), {'cols': COLUMNS_TO_DROP})
        existing = {row[0] for row in result.fetchall()}

        if not existing:
            print("None of the target columns exist. Nothing to do.")
            return

        for col in COLUMNS_TO_DROP:
            if col in existing:
                conn.execute(text(f"ALTER TABLE listings DROP COLUMN {col}"))
                print(f"Dropped column '{col}' from listings table.")
            else:
                print(f"Column '{col}' does not exist. Skipping.")

        conn.commit()
        print("Migration complete.")

if __name__ == '__main__':
    migrate()
