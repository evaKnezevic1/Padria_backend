"""
Migration script: Add bilingual (English) columns to about_content and contact_content tables.
Run this once to update the existing database.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app.database.db import engine
from sqlalchemy import text


def migrate():
    with engine.connect() as conn:
        # --- about_content: add _en columns ---
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'about_content'"
        ))
        about_cols = [row[0] for row in result]

        about_new = {
            'title_en': 'VARCHAR',
            'intro_en': 'TEXT',
            'mission_title_en': 'VARCHAR',
            'mission_text_en': 'TEXT',
            'why_title_en': 'VARCHAR',
            'why_items_en': 'TEXT',
            'contact_title_en': 'VARCHAR',
            'contact_text_en': 'TEXT',
        }
        for col, col_type in about_new.items():
            if col not in about_cols:
                conn.execute(text(f"ALTER TABLE about_content ADD COLUMN {col} {col_type}"))
                print(f"about_content: added column {col}")
            else:
                print(f"about_content: column {col} already exists")

        # --- contact_content: add title, subtitle, title_en, subtitle_en ---
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'contact_content'"
        ))
        contact_cols = [row[0] for row in result]

        contact_new = {
            'title': ("VARCHAR", "DEFAULT 'Kontaktirajte nas'"),
            'subtitle': ("TEXT", "DEFAULT 'Javite nam se putem bilo kojeg od kanala ispod.'"),
            'title_en': ("VARCHAR", ""),
            'subtitle_en': ("TEXT", ""),
        }
        for col, (col_type, extra) in contact_new.items():
            if col not in contact_cols:
                conn.execute(text(f"ALTER TABLE contact_content ADD COLUMN {col} {col_type} {extra}".strip()))
                print(f"contact_content: added column {col}")
            else:
                print(f"contact_content: column {col} already exists")

        conn.commit()
    print("Migration complete.")


if __name__ == '__main__':
    migrate()
