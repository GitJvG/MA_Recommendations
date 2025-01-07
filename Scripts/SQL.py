"""Script to push all data to SQL, currently fully cascades the existing DB out of convenience"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from app import create_app, db
from app.models import member, details, similar_band, discography, band, genre, prefix, genres, theme, themes, candidates, hgenre, label
from sqlalchemy import text
from Env import Env
env = Env.get_instance()

dataframes = {
    member.__name__: lambda: pd.read_csv(env.memb, header=0),
    details.__name__: lambda: pd.read_csv(env.deta, header=0),
    similar_band.__name__: lambda: pd.read_csv(env.simi, header=0),
    discography.__name__: lambda: pd.read_csv(env.disc, header=0, keep_default_na=False, na_values=['']),
    band.__name__: lambda: pd.read_csv(env.band, header=0),
    genre.__name__: lambda: pd.read_csv(env.genre, header=0),
    hgenre.__name__: lambda: pd.read_csv(env.hgenre, header=0),
    prefix.__name__: lambda: pd.read_csv(env.prefix, header=0),
    genres.__name__: lambda: pd.read_csv(env.genres, header=0),
    theme.__name__: lambda: pd.read_csv(env.theme, header=0),
    themes.__name__: lambda: pd.read_csv(env.themes, header=0),
    candidates.__name__: lambda: pd.read_csv(env.candidates, header=0),
    label.__name__: lambda: pd.read_csv(env.label, header=0)
}

def refresh_tables(model=None):
    """Fully drops and truncates model before recreating it, this is done to overcome annoying relationship spaggetthi"""
    app = create_app()
    with app.app_context():
        models = model if model else [label, band, theme, prefix, genre, hgenre, discography, similar_band, details, member, genres, themes, candidates]

        for model in models:
            df = dataframes.get(model.__name__)()
            if df is None or df.empty:
                raise ValueError(f"DataFrame for model '{model.__name__}' is empty or None.")

        for model in models:
            db.session.execute(text(f'DROP TABLE IF EXISTS "{model.__tablename__}" CASCADE;'))
        db.session.commit()

        db.create_all()

        for model in models:
            df = dataframes.get(model.__name__)()
            df.to_sql(model.__tablename__, con=db.engine, if_exists='append', index=False)

        print("All tables refreshed successfully with constraints applied.")

if __name__ == "__main__":
    refresh_tables()
