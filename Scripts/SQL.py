import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from app import create_app, db
from sqlalchemy import text
from Env import Env
env = Env.get_instance()

bands_df = pd.read_csv(env.band, header=0)
similar_bands_df = pd.read_csv(env.simi, header=0)
details_df = pd.read_csv(env.deta, header=0)
discography_df = pd.read_csv(env.disc, header=0)
member_df = pd.read_csv(env.memb, header=0)
genre_df = pd.read_csv(env.genre, header=0)
prefix_df = pd.read_csv(env.prefix, header=0)
bandgenre_df = pd.read_csv(env.genres, header=0)
bandtheme_df = pd.read_csv(env.themes, header=0)
theme_df = pd.read_csv(env.theme, header=0)
    
def refresh_tables():
    app = create_app()
    with app.app_context():
        # Drop tables if they exist to refresh structure
        db.session.execute(text('DROP TABLE IF EXISTS "member" CASCADE;'))
        db.session.execute(text('DROP TABLE IF EXISTS "details" CASCADE;'))
        db.session.execute(text('DROP TABLE IF EXISTS "similar_band" CASCADE;'))
        db.session.execute(text('DROP TABLE IF EXISTS "discography" CASCADE;'))
        db.session.execute(text('DROP TABLE IF EXISTS "band" CASCADE;'))
        db.session.execute(text('DROP TABLE IF EXISTS "genre" CASCADE;'))
        db.session.execute(text('DROP TABLE IF EXISTS "prefix" CASCADE;'))
        db.session.execute(text('DROP TABLE IF EXISTS "genres" CASCADE;'))
        db.session.execute(text('DROP TABLE IF EXISTS "theme" CASCADE;'))
        db.session.execute(text('DROP TABLE IF EXISTS "themes" CASCADE;'))
        # Commit the table drops
        db.session.commit()

        # Recreate tables based on model definitions
        db.create_all()

        # Insert data into tables from DataFrames
        bands_df.to_sql('band', con=db.engine, if_exists='append', index=False)
        similar_bands_df.to_sql('similar_band', con=db.engine, if_exists='append', index=False)
        discography_df.to_sql('discography', con=db.engine, if_exists='append', index=False)
        details_df.to_sql('details', con=db.engine, if_exists='append', index=False)
        member_df.to_sql("member", con=db.engine, if_exists='append', index=False)

        genre_df.to_sql('genre', con=db.engine, if_exists='append', index=False)
        prefix_df.to_sql('prefix', con=db.engine, if_exists='append', index=False)
        bandgenre_df.to_sql('genres', con=db.engine, if_exists='append', index=False)
        theme_df.to_sql('theme', con=db.engine, if_exists='append', index=False)
        bandtheme_df.to_sql('themes', con=db.engine, if_exists='append', index=False)
        

        print("All tables refreshed successfully with constraints applied.")

if __name__ == "__main__":
    refresh_tables()
