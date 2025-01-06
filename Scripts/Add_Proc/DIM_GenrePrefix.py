import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)
import pandas as pd
from Env import Env
from Scripts.Add_Proc.Helper.CleanGenre import advanced_clean_flat
env = Env.get_instance()

def items_to_set(flattened_data):
    """Convert flattened data to a unique set of items."""
    return set((name, type_) for name, type_ in flattened_data if name)

def create_dim_csv(flattened_data, type, output):
    """Create a dimension CSV file from flattened data."""
    all_items = items_to_set(flattened_data)
    dfsingle = pd.DataFrame(list(all_items), columns=['name', 'type'])
    dfsingle['type'] = type
    dfsingle = dfsingle[['name', 'type']]
    dfsingle.rename_axis('id').to_csv(output, index=True)

def build_name_to_id_and_type(dim_df):
    """Build a lookup dictionary for name -> (id, type)."""
    name_to_id_type = dict(((name.strip(), type.strip()), id_) for name, type, id_ in zip(dim_df['name'], dim_df['type'], dim_df['id']))
    return name_to_id_type

def process_flattened_row(flattened_data, name_to_id_type, bridge_rows, band_id):
    """Process a single flattened row of data."""
    for name, type_ in flattened_data:
        if (name, type_) in name_to_id_type:
            item_id = name_to_id_type[(name, type_)]
            bridge_rows.append([band_id, item_id, type_])

def create_bridge_csv(band_df, dim_dfs, output_path):
    """Create a bridge CSV that maps band_id to item_id and type."""
    name_to_id_type_list = [build_name_to_id_and_type(df) for df in dim_dfs]

    bridge_rows = []
    for _, row in band_df.iterrows():
        band_id = row['band_id']
        flattened_data = advanced_clean_flat(row['genre'])

        for i, name_to_id_type in enumerate(name_to_id_type_list):
            process_flattened_row(flattened_data, name_to_id_type, bridge_rows, band_id)

    if bridge_rows:
        bridge_df = pd.DataFrame(bridge_rows, columns=['band_id', 'item_id', 'type'])
        bridge_df.to_csv(output_path, index=False)
        print(f"Bridge table created with {len(bridge_rows)} rows.")
    else:
        print("No rows added to bridge table.")

def main():
    df = pd.read_csv(env.band)
    df['Flattened_Genres'] = df['genre'].apply(advanced_clean_flat)

    flattened_single_primals = [item for sublist in df['Flattened_Genres'] for item in sublist if item[1] == 'single_primal']
    flattened_primals = [item for sublist in df['Flattened_Genres'] for item in sublist if item[1] == 'primal']
    flattened_prefixes = [item for sublist in df['Flattened_Genres'] for item in sublist if item[1] == 'prefix']

    create_dim_csv(flattened_single_primals, 'single_primal', env.genre)
    create_dim_csv(flattened_primals, 'primal', env.hgenre)
    create_dim_csv(flattened_prefixes, 'prefix', env.prefix)

    dim_dfs = [pd.read_csv(env.genre), pd.read_csv(env.hgenre), pd.read_csv(env.prefix)]

    create_bridge_csv(df, dim_dfs, output_path=env.genres)

if __name__ == "__main__":
    main()