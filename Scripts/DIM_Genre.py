import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import pandas as pd
from Env import Env
from Helper.CleanGenre import advanced_clean
env = Env.get_instance()

df = pd.read_csv(env.band)
def safe_advanced_clean(genre):
    try:
        return pd.Series(advanced_clean(genre))
    except Exception as e:
        print(f"Error processing genre: {genre} - {e}")
        raise

df[['Primal_genre', 'ProcGenre', 'single']] = df['Genre'].apply(safe_advanced_clean)
filtered_df = df[df['single'].apply(lambda x: 'epic' in [part.strip() for part in str(x).split(',')])]

# Display the filtered results
print(filtered_df['Genre'])

def get_all_genres(genre_series):
    genre_list = []
    for genre_string in genre_series:
        if pd.notna(genre_string):  # Safeguard against NaN values
            genre_list.extend([genre.strip() for genre in genre_string.split(',')])  # Split by comma and strip
    return genre_list

# Get all genres from Primal_genre column (no need to filter unique genres here)
all_primal_genres = get_all_genres(df['single'])
# Display the sorted dataframe
primal_set = set(all_primal_genres)
dfsingle = pd.DataFrame(primal_set)
dfsingle.to_csv('testing.csv', index=False)