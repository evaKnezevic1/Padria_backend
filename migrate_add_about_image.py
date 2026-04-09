"""
Migration script: Add about_image_url column to about_content table.
Run this once to update the existing database.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text

from app.database.db import engine


def migrate():
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'about_content'"
        ))
        columns = [row[0] for row in result]

        if 'about_image_url' not in columns:
            conn.execute(text("ALTER TABLE about_content ADD COLUMN about_image_url VARCHAR"))
            print("about_content: added column about_image_url")
        else:
            print("about_content: column about_image_url already exists")

        conn.commit()

    print("Migration complete.")


if __name__ == '__main__':
    migrate()