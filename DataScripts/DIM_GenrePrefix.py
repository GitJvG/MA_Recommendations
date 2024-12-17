import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
import pandas as pd
from Env import Env
from DataScripts.Helper.CleanGenre import advanced_clean
env = Env.get_instance()

def items_to_set(genre_series):
    """Convert the genre Series to a unique set of items."""
    all_items = genre_series.dropna().str.split(',').explode().str.strip().unique()
    return set(all_items)

def create_dim_csv(df, type, output):
    """Create a dimension CSV file from the genre series."""
    all_items = items_to_set(df)
    dfsingle = pd.DataFrame(all_items, columns=['name'])
    dfsingle['type'] = type
    dfsingle = dfsingle[['name', 'type']]
    dfsingle.rename_axis('id').to_csv(output, index=True)

def build_name_to_id_and_type(dim_df):
    """Build a lookup dictionary for name -> (id, type)"""
    name_to_id_type = dict(zip(dim_df['name'], zip(dim_df['id'], dim_df['type'])))
    return name_to_id_type

def process_column(row, column_name, name_to_id_type, bridge_rows, band_id):
    """Helper function to process each column (e.g., genres or prefixes)."""
    if row[column_name]:
        items = [item.strip() for item in row[column_name].split(',')]
        for item in items:
            if item in name_to_id_type:
                item_id, item_type = name_to_id_type[item]
                if [band_id, item_id, item_type] not in bridge_rows:
                    bridge_rows.append([band_id, item_id, item_type])

def create_bridge_csv(band_df, dim_dfs, output_path):
    """Create a bridge CSV that maps band_id to item_id and type."""
    name_to_id_type_list = [build_name_to_id_and_type(df) for df in dim_dfs]

    bridge_rows = []
    for _, row in band_df.iterrows():
        band_id = row['band_id']
        process_column(row, 'Split_Primary_Genres', name_to_id_type_list[0], bridge_rows, band_id)
        process_column(row, 'Complex_Primary_Genres', name_to_id_type_list[1], bridge_rows, band_id)
        process_column(row, 'Prefix', name_to_id_type_list[2], bridge_rows, band_id)

    bridge_df = pd.DataFrame(bridge_rows, columns=['band_id', 'item_id', 'type'])
    bridge_df.to_csv(output_path, index=False)

def main():
    df = pd.read_csv(env.band)
    df[['Split_Primary_Genres', 'Complex_Primary_Genres', 'Prefix']] = df['genre'].apply(advanced_clean).apply(pd.Series)

    create_dim_csv(df['Split_Primary_Genres'], 'genre', env.genre)
    create_dim_csv(df['Complex_Primary_Genres'], 'hybrid_genre', env.hgenre)
    create_dim_csv(df['Prefix'], 'prefix', env.prefix)

    dim_dfs = [pd.read_csv(env.genre), pd.read_csv(env.hgenre), pd.read_csv(env.prefix)]

    create_bridge_csv(df, dim_dfs, output_path=env.genres)

if __name__ == "__main__":
    main()
