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
    dfsingle.rename_axis('id').to_csv(output_path, index=True)

def build_name_to_id_and_type(dim_df):
    """Build a lookup dictionary for name -> (id, type)."""
    name_to_id_type = dict(((name.strip(), type.strip()), id_) for name, type, id_ in zip(dim_df['name'], dim_df['type'], dim_df['id']))
    return name_to_id_type

def build_name_to_id_and_type(dim_df, item_type):
    name_to_id_type = {}
    for id_, name in zip(dim_df['id'], dim_df['name']):
        name_to_id_type[(str(name).strip(), item_type)] = id_
    return name_to_id_type

def create_split_bridge_csvs_optimized(band_df, combined_name_to_id_lookup, output_paths):
    def get_band_bridge_tuples(row):
        band_id = row['band_id']
        flattened_data = row['Flattened_Genres'] if isinstance(row['Flattened_Genres'], list) else []
        band_links = set()

        for name, type_ in flattened_data:
            name = str(name).strip()
            type_ = str(type_).strip()
            if (name, type_) in combined_name_to_id_lookup:
                item_id = combined_name_to_id_lookup[(name, type_)]
                band_links.add((band_id, item_id, type_))

        return list(band_links)
    list_of_link_lists = band_df.apply(get_band_bridge_tuples, axis=1)
    all_bridge_tuples = [
        link_tuple
        for link_list in list_of_link_lists
        for link_tuple in link_list
    ]
    final_unique_bridge_tuples = set(all_bridge_tuples)

    if final_unique_bridge_tuples:
        bridge_df = pd.DataFrame(list(final_unique_bridge_tuples), columns=['band_id', 'id', 'type'])
        print(f"Total unique bridge rows collected: {len(bridge_df)}")

        for item_type, file_path in output_paths.items():
            type_df = bridge_df[bridge_df['type'] == item_type][['band_id', 'id']].copy()
            type_df.to_csv(file_path, index=False)
            print(f"Bridge data for '{item_type}' created with {len(type_df)} rows (saved to {file_path}).")

def main():
    df = pd.read_csv(env.band)
    df['Flattened_Genres'] = df['genre'].apply(lambda x: process_genres(x) if pd.notna(x) else [])
    all_flattened_data = [item for sublist in df['Flattened_Genres'] for item in sublist]

    unique_names_by_type = {
        'genre': set(name for name, type_ in all_flattened_data if type_ == 'genre'),
        'hybrid_genre': set(name for name, type_ in all_flattened_data if type_ == 'hybrid_genre'),
        'prefix': set(name for name, type_ in all_flattened_data if type_ == 'prefix'),
    }

    dim_output_paths = {
        'genre': env.genre,
        'hybrid_genre': env.hgenre,
        'prefix': env.prefix,
    }
    
    dim_dfs = {}
    combined_name_to_id_lookup = {}

    for item_type, unique_names in unique_names_by_type.items():
        output_path = dim_output_paths[item_type]
        create_dim_csv(unique_names, output_path)
        dim_df = pd.read_csv(output_path)
        dim_dfs[item_type] = dim_df

        lookup_for_type = build_name_to_id_and_type(dim_df, item_type)
        combined_name_to_id_lookup.update(lookup_for_type)

    bridge_output_paths = {
        'genre': env.band_genres,
        'hybrid_genre': env.band_hgenres,
        'prefix': env.band_prefixes,
    }

    create_split_bridge_csvs_optimized(df, combined_name_to_id_lookup, bridge_output_paths)

if __name__ == "__main__":
    main()