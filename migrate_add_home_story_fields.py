"""
Migration script: Add homepage Our Story fields to about_content table.
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

        additions = {
            'home_story_title': "VARCHAR DEFAULT 'Naša priča'",
            'home_story_text': "TEXT DEFAULT 'Naša priča započela je s jednostavnom idejom — ponuditi nešto drugačije na tržištu nekretnina. Umjesto masovnog pristupa, odlučili smo se za boutique model, gdje je svaki klijent jedinstven, a svaka nekretnina ima svoju priču. Kao mala, posvećena agencija, gradimo odnose temeljene na povjerenju, diskreciji i vrhunskoj usluzi. Fokusirani smo na kvalitetu, ne kvantitetu — pažljivo biramo nekretnine koje predstavljamo i pružamo personaliziranu podršku kroz svaki korak procesa.'",
            'home_story_title_en': 'VARCHAR',
            'home_story_text_en': 'TEXT',
        }

        for col, col_type in additions.items():
            if col not in columns:
                conn.execute(text(f"ALTER TABLE about_content ADD COLUMN {col} {col_type}"))
                print(f"about_content: added column {col}")
            else:
                print(f"about_content: column {col} already exists")

        conn.commit()

    print('Migration complete.')


if __name__ == '__main__':
    migrate()