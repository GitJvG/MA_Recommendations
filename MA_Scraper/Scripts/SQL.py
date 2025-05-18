"""Script to push all data to SQL, currently fully cascades the existing DB out of convenience"""
import pandas as pd
from MA_Scraper.app import create_app, db
from MA_Scraper.app.models import Member, Details, Similar_band, Discography, Band_logo, Band, Genre, Prefix, BandGenres, BandPrefixes, BandHgenres, Theme, Themes, Candidates, Hgenre, Label
from sqlalchemy import text, inspect
from MA_Scraper.Env import Env
env = Env.get_instance()

dataframes = {
    Member.__name__: lambda: pd.read_csv(env.memb, header=0),
    Details.__name__: lambda: pd.read_csv(env.deta, header=0),
    Similar_band.__name__: lambda: pd.read_csv(env.simi, header=0),
    Discography.__name__: lambda: pd.read_csv(env.disc, header=0, keep_default_na=False, na_values=['']),
    Band_logo.__name__: lambda: pd.read_csv(env.band_logo, header=0),
    Band.__name__: lambda: pd.read_csv(env.band, header=0),
    Genre.__name__: lambda: pd.read_csv(env.genre, header=0),
    Hgenre.__name__: lambda: pd.read_csv(env.hgenre, header=0),
    Prefix.__name__: lambda: pd.read_csv(env.prefix, header=0),
    BandGenres.__name__: lambda: pd.read_csv(env.band_genres, header=0),
    BandHgenres.__name__: lambda: pd.read_csv(env.band_hgenres, header=0),
    BandPrefixes.__name__: lambda: pd.read_csv(env.band_prefixes, header=0),
    Theme.__name__: lambda: pd.read_csv(env.theme, header=0),
    Themes.__name__: lambda: pd.read_csv(env.themes, header=0),
    Candidates.__name__: lambda: pd.read_csv(env.candidates, header=0),
    Label.__name__: lambda: pd.read_csv(env.label, header=0)
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


def refresh_tables(model=None):
    """Fully drops and truncates model before recreating it, this is done to overcome annoying relationship spaggetthi"""
    backup_logo()
    app = create_app()
    with app.app_context():
        models = model if model else [Label, Band, Theme, Prefix, Genre, Hgenre, Discography, Similar_band, Band_logo, Details, Member, BandGenres, BandHgenres, BandPrefixes, Themes, Candidates]
        models2 = model if model else [Label, Band, Theme, Prefix, Genre, Hgenre, Discography, Similar_band, Details, Member, BandGenres, BandHgenres, BandPrefixes, Themes, Candidates]
        for model in models2:
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