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
        if pd.notna(genre_string):
            genre_set.update([genre.strip() for genre in genre_string.split(',')])
    return genre_set

def create_dim_csv(df, type, hybrid=None):
    all_items = items_to_set(df)
    dfsingle = pd.DataFrame(all_items, columns=['name'])
    dfsingle['type'] = type
    if hybrid != None:
        dfsingle['hybrid'] = hybrid
        dfsingle = dfsingle[['name', 'type', 'hybrid']]
    else:
        dfsingle = dfsingle[['name', 'type']]
    return dfsingle

def process_column(row, column_name, dim_df, bridge_rows, band_id, item_type):
    """Helper function to process each column (e.g., genres or prefixes)."""
    if row[column_name]:
        items = [item.strip() for item in row[column_name].split(',')]
        for item in items:
            if item in dim_df['name'].values:
                item_id = dim_df[dim_df['name'] == item]['id'].values[0]
                bridge_rows.append([band_id, item_id, item_type])

def create_bridge_csv(df, genre_dim, prefix_dim, output_path):
    bridge_rows = []
    for _, row in df.iterrows():
        band_id = row['band_id']
        
        process_column(row, 'Split_Primary_Genres', genre_dim, bridge_rows, band_id, 'genre')
        process_column(row, 'Complex_Primary_Genres', genre_dim, bridge_rows, band_id, 'genre')
        process_column(row, 'Prefix', prefix_dim, bridge_rows, band_id, 'prefix')

    bridge_df = pd.DataFrame(bridge_rows, columns=['band_id', 'item_id', 'type'])
    bridge_df.to_csv(output_path, index=False)
def main():
    df = pd.read_csv(env.band)
    df[['Split_Primary_Genres', 'Complex_Primary_Genres', 'Prefix']] = df['genre'].apply(advanced_clean).apply(pd.Series)
    
    genre_df = create_dim_csv(df['Split_Primary_Genres'], 'genre', hybrid=False)
    hgenre_df = create_dim_csv(df['Complex_Primary_Genres'], 'genre', hybrid=True)
    pd.concat([genre_df, hgenre_df], ignore_index=True).rename_axis('id').to_csv(env.genre, index=True)
    prefix_df = create_dim_csv(df['Prefix'], 'prefix')
    prefix_df.rename_axis('id').to_csv(env.prefix, index=True)
    
    create_bridge_csv(df, genre_dim=pd.read_csv(env.genre), prefix_dim=pd.read_csv(env.prefix), output_path=env.genres)
    
if __name__ == "__main__":
    main()