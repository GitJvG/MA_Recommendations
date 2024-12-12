import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
import pandas as pd
from Env import Env
from DataScripts.Helper.CleanGenre import advanced_clean
env = Env.get_instance()

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

def create_bridge_csv(df, genre_dim, prefix_dim, output_path):
    bridge_rows = []
    for _, row in df.iterrows():
        band_id = row['band_id']
        
        if row['Split_Primary_Genres']:
            genres = row['Split_Primary_Genres'].split(',')
            for genre in genres:
                if genre in genre_dim['name'].values:
                    item_id = genre_dim[genre_dim['name'] == genre]['id'].values[0]
                    bridge_rows.append([band_id, item_id, 'genre'])
        if row['Prefix']:
            prefixes = row['Prefix'].split(',')
            for prefix in prefixes:
                if prefix in prefix_dim['name'].values:
                    item_id = prefix_dim[prefix_dim['name'] == prefix]['id'].values[0]
                    bridge_rows.append([band_id, item_id, 'prefix'])

    bridge_df = pd.DataFrame(bridge_rows, columns=['band_id', 'item_id', 'type'])
    bridge_df.to_csv(output_path, index=False)

def main():
    df = pd.read_csv(env.band)
    df[['Split_Primary_Genres', 'Complex_Primary_Genres', 'Prefix']] = df['genre'].apply(advanced_clean).apply(pd.Series)
    create_dim_csv(df['Split_Primary_Genres'], 'genre', env.genre)
    create_dim_csv(df['Prefix'], 'prefix', env.prefix)
    create_bridge_csv(df, genre_dim=pd.read_csv(env.genre), prefix_dim=pd.read_csv(env.prefix), output_path=env.genres)
    
if __name__ == "__main__":
    main()