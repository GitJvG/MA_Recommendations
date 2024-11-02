from .root import roots
roots()
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import warnings
from app.models import DIM_Band, DIM_Lyrics, DIM_Similar_Band
from Scripts.utils import load_config
from Scripts.Components.CleanGenre import simple_clean2

warnings.filterwarnings("ignore")

# Create a database engine
DATABASE_URI = load_config('SQL_Url')
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

def Prepare_Items():
    # Load data from your tables
    dim_band_data = session.query(DIM_Band).all()
    lyrical_data = session.query(DIM_Lyrics).all()
    popularity = session.query(DIM_Similar_Band).all()

    # Create items DataFrame
    items = pd.DataFrame(
        [(band.Band_ID, band.Band_Name, band.Country, band.Genre, band.Status) for band in dim_band_data],
        columns=['item', 'band_name', 'country', 'genre', 'status']
    )

    popularity = pd.DataFrame(
        [(pop.Band_ID, pop.Artist_URL, pop.Similar_Artist_ID, pop.Score) for pop in popularity],
        columns=['item', 'band_name', 'similar_item', 'score']
    )
    popularity = precompute_all_similarities(popularity)[['item', 'score']]

    items['cleaned_genre'] = items['genre'].apply(simple_clean2)
    # Split the cleaned genres by commas into separate columns
    genres_split = items['cleaned_genre'].str.split(r',\s*', expand=True)
    genres_split = genres_split.iloc[:, :4]
    # Rename columns for the split genres
    genres_split.columns = [f'genre{i+1}' for i in range(genres_split.shape[1])]

    # Concatenate the split genres back to the original DataFrame
    items = pd.concat([items, genres_split], axis=1)

    # Drop the original 'genre' and 'cleaned_genre' columns if desired
    items.drop(columns=['genre', 'cleaned_genre'], inplace=True)

    lyrics = pd.DataFrame(
        [(lyr.Themes, lyr.Band_ID) for lyr in lyrical_data],
        columns=['theme', 'item']
    )

    themes_split = lyrics['theme'].str.split(',', expand=True)

    #limit it to max 4 themes
    themes_split = themes_split.iloc[:, :4]
    # Optionally rename columns before concatenation
    themes_split.columns = [f'theme{i+1}' for i in range(themes_split.shape[1])]

    # Concatenate the split themes back to the original DataFrame
    lyrics = pd.concat([lyrics, themes_split], axis=1)

    # Drop the original 'Themes' column
    lyrics.drop(columns=['theme'], inplace=True)

    # Complete band set, used separately later on as well
    all_items = items.merge(lyrics, on='item').merge(popularity, on='item')

    return all_items

def precompute_all_similarities(df):
    """Precomputes all similar bands and avoids duplicates."""
    # Create a copy of the DataFrame with Band ID and Similar Artist ID switched
    switched_df = df.copy()

    switched_df = switched_df.rename(columns={'item': 'similar_item', 'similar_item': 'item'})

    # Append the switched version to the original DataFrame
    combined_df = pd.concat([df, switched_df])

    # Sum to indicate popularity
    aggregated_df = combined_df.groupby(['item'], as_index=False).agg({'score': 'sum'})

    return aggregated_df

if __name__ == "__main__":
    print(Prepare_Items().info())