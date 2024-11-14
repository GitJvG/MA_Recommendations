import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import pandas as pd
from Env import Env
from Helper.CleanGenre import advanced_clean
env = Env.get_instance()

df = pd.read_csv(env.band)
def raise_advanced_clean(genre):
    try:
        return pd.Series(advanced_clean(genre))
    except Exception as e:
        print(f"Error processing genre: {genre} - {e}")
        raise

df[['Split_Primary_Genres', 'Complex_Primary_Genres', 'Prefix']] = df['genre'].apply(raise_advanced_clean)

def items_to_set(genre_series):
    genre_set = set()
    for genre_string in genre_series:
        if pd.notna(genre_string):  # Safeguard against NaN values
            # Split by comma, strip whitespace, and add directly to the set to avoid duplicates
            genre_set.update([genre.strip() for genre in genre_string.split(',')])
    return genre_set

# Get all unique genres from Primal_genre column
def create_dim_csv(df, type, output_path):
    all_items = items_to_set(df)
    dfsingle = pd.DataFrame(all_items, columns=['name'])
    # Add ID and type columns
    dfsingle['id'] = range(1, len(dfsingle) + 1)  # Incremental ID
    dfsingle['type'] = type
    dfsingle = dfsingle[['id', 'name', 'type']]
    dfsingle.to_csv(output_path, index=False)

if __name__ == "__main__":
    create_dim_csv(df['Split_Primary_Genres'], 'genre', env.dim_genre)
    create_dim_csv(df['Prefix'], 'prefix', env.dim_prefix)