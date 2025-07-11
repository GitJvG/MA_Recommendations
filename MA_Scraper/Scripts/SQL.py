"""Script to push all data to SQL, currently fully cascades the existing DB out of convenience"""
import pandas as pd
from MA_Scraper.app import create_app, db
from MA_Scraper.app.models import Member, Similar_band, Discography, Band_logo, Band, Genre, Prefix, BandGenres, BandPrefixes, Theme, Themes, Candidates, Label
from sqlalchemy import text, inspect
from MA_Scraper.Env import Env
import ast
env = Env.get_instance()

def process_band_logo():
    df = pd.read_csv(env.band_logo, header=0)
    df.loc[:, 'data'] = df['data'].apply(string_representation_to_bytes)
    return df

dataframes = {
    Member.__name__: lambda: pd.read_csv(env.memb, header=0, keep_default_na=False, na_values=['']),
    Similar_band.__name__: lambda: pd.read_csv(env.simi, header=0),
    Discography.__name__: lambda: pd.read_csv(env.disc, header=0, keep_default_na=False, na_values=['']),
    Band_logo.__name__: process_band_logo,
    Band.__name__: lambda: pd.read_csv(env.fband, header=0, keep_default_na=False, na_values=['']),
    Genre.__name__: lambda: pd.read_csv(env.genre, header=0),
    Prefix.__name__: lambda: pd.read_csv(env.prefix, header=0),
    BandGenres.__name__: lambda: pd.read_csv(env.band_genres, header=0),
    BandPrefixes.__name__: lambda: pd.read_csv(env.band_prefixes, header=0),
    Theme.__name__: lambda: pd.read_csv(env.theme, header=0, keep_default_na=False, na_values=['']),
    Themes.__name__: lambda: pd.read_csv(env.themes, header=0),
    Candidates.__name__: lambda: pd.read_csv(env.candidates, header=0, keep_default_na=False, na_values=['']),
    Label.__name__: lambda: pd.read_csv(env.label, header=0, keep_default_na=False, na_values=[''])
}

def backup_logo():
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        band_logo_table_exists = inspector.has_table(Band_logo.__tablename__)
        if band_logo_table_exists:
            df_logo_backup = pd.read_sql_table(Band_logo.__tablename__, con=db.engine)
            if df_logo_backup is None or df_logo_backup.empty:
                print(f"Info: No existing data in {Band_logo.__tablename__} to back up.")
            else:
                df_logo_backup.to_csv(env.band_logo, index=False)
                print(f"Backup of {Band_logo.__tablename__} complete ({len(df_logo_backup)} rows).")

def string_representation_to_bytes(byte_string_repr):
    if isinstance(byte_string_repr, bytes):
        return byte_string_repr
    if pd.isna(byte_string_repr):
        return None
    try:
        return ast.literal_eval(byte_string_repr)
    except (ValueError, SyntaxError, TypeError):
        print(f"Warning: Could not convert string representation '{byte_string_repr}' to bytes.")
        return None 


def refresh_tables(model=None):
    """Fully drops and truncates model before recreating it, this is done to overcome annoying relationship spaggetthi"""
    app = create_app()
    with app.app_context():
        models = model if model else [Label, Band, Theme, Prefix, Genre, Discography, Similar_band, Band_logo, Member, BandGenres, BandPrefixes, Themes]
        for model in models:
            df = dataframes.get(model.__name__)()
            if df is None or df.empty:
                raise ValueError(f"DataFrame for model '{model.__name__}' is empty or None.")
        
        if Band_logo in models:
            backup_logo()
            
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