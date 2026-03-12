"""
Migration script: Add English translation columns (title_en, description_en) to the listings table.
Run this once to update the existing database.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app.database.db import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        # Check existing columns
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'listings'"
        ))
        columns = [row[0] for row in result]

        if 'title_en' not in columns:
            conn.execute(text("ALTER TABLE listings ADD COLUMN title_en VARCHAR"))
            print("Added column: title_en")
        else:
            print("Column title_en already exists")

        if 'description_en' not in columns:
            conn.execute(text("ALTER TABLE listings ADD COLUMN description_en TEXT"))
            print("Added column: description_en")
        else:
            print("Column description_en already exists")

        conn.commit()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
