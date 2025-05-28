import pandas as pd
from MA_Scraper.Env import Env
from MA_Scraper.Scripts.Add_Proc.Helper.CleanGenre import process_genres
env = Env.get_instance()

def items_to_set(flattened_data):
    """Convert flattened data to a unique set of items."""
    return set((name, type_) for name, type_ in flattened_data if name)

def create_dim_csv(unique_names_for_type, output_path):
    dfsingle = pd.DataFrame(list(unique_names_for_type), columns=['name'])
    dfsingle = dfsingle.sort_values(by='name').reset_index(drop=True)
    dfsingle['id'] = dfsingle.index
    dfsingle.to_csv(output_path, index=False)

    return dfsingle

def build_name_to_id_and_type(dim_df):
    """Build a lookup dictionary for name -> (id, type)."""
    name_to_id_type = dict(((name.strip(), type.strip()), id_) for name, type, id_ in zip(dim_df['name'], dim_df['type'], dim_df['id']))
    return name_to_id_type

def build_name_to_id_and_type(dim_df, item_type):
    name_to_id_type = {}
    for id_, name in zip(dim_df['id'], dim_df['name']):
        name_to_id_type[(str(name).strip(), item_type)] = id_
    return name_to_id_type

def create_bridge_csv(processed_df, dim_df, output_file_path, item_type_label):
    temp_series = processed_df[item_type_label].dropna().astype(str)
        
    if item_type_label == 'genre':
        exploded_items = temp_series.str.split(' ').explode().str.strip()
    elif item_type_label == 'prefix':
        exploded_items = temp_series.str.split(' ').explode().str.strip()
    else:
        exploded_items = temp_series

    temp_bridge_df = pd.DataFrame({
        'item_name': exploded_items,
        'original_processed_df_index': exploded_items.index
    })

    temp_bridge_df = pd.merge(
        temp_bridge_df,
        processed_df[['row_id', 'band_id']],
        left_on='original_processed_df_index',
        right_on=processed_df.index,
        how='left'
    )

    temp_bridge_df = temp_bridge_df.drop(columns=['original_processed_df_index'])

    bridge_df = pd.merge(
        temp_bridge_df, dim_df[['id', 'name']], left_on='item_name', right_on='name', how='inner')

    bridge_df = bridge_df[['band_id', 'id']].drop_duplicates()

    if not bridge_df.empty:
        bridge_df.to_csv(output_file_path, index=False)
        print(f"Bridge data for '{item_type_label}' created with {len(bridge_df)} rows (saved to {output_file_path}).")

def main():
    df = pd.read_csv(env.band)
    processed_df = process_genres(df['genre'])
    processed_df['band_id'] = processed_df['row_id'].map(df['band_id'])

    unique_names_by_type = {}
    unique_names_by_type['genre'] = set(processed_df['genre'].str.split(',').explode().str.strip().dropna().unique())
    unique_names_by_type['hybrid_genre'] = set(processed_df['genre'].dropna().unique())
    unique_names_by_type['prefix'] = set(processed_df['prefix'].str.split(',').explode().str.strip().dropna().unique())

    dim_output_paths = {
        'genre': env.genre,
        'hybrid_genre': env.hgenre,
        'prefix': env.prefix,
    }

    bridge_output_paths = {
        'genre': env.band_genres,
        'hybrid_genre': env.band_hgenres,
        'prefix': env.band_prefixes,
    }

    for item_type, unique_names in unique_names_by_type.items():
        output_path = dim_output_paths[item_type]
        dim_df = create_dim_csv(unique_names, output_path)
  
        create_bridge_csv(
            processed_df=processed_df,
            dim_df=dim_df,
            output_file_path=bridge_output_paths[item_type],
            item_type_label=item_type
        )

if __name__ == "__main__":
    main()