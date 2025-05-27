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

def create_bridge_csv(band_df, dim_df_for_type, output_file_path, item_type_label):
    bridge_tuples_for_type = set()
    dim_lookup = pd.Series(dim_df_for_type['id'].values, index=dim_df_for_type['name']).to_dict()

    for _, row in band_df.iterrows():
        band_id = row['band_id']
        terms_string = row[item_type_label]

        if isinstance(terms_string, str) and terms_string.strip():
            individual_terms = [t.strip() for t in terms_string.split(',') if t.strip()]

            for term_name in individual_terms:
                item_id = dim_lookup.get(term_name)
                if item_id is not None:
                    bridge_tuples_for_type.add((band_id, item_id))

    if bridge_tuples_for_type:
        bridge_df = pd.DataFrame(list(bridge_tuples_for_type), columns=['band_id', f'{item_type_label}_id'])
        bridge_df.to_csv(output_file_path, index=False)
        print(f"Bridge data for '{item_type_label}' created with {len(bridge_df)} rows (saved to {output_file_path}).")

def main():
    df = pd.read_csv(env.band)
    df[['genre', 'hybrid_genre', 'prefix']] = process_genres(df['genre'])

    unique_names_by_type = {
        'genre': set(item.strip() for s in df['genre'] if isinstance(s, str) and s for item in s.split(',') if item.strip()),
        'hybrid_genre': set(item.strip() for s in df['hybrid_genre'] if isinstance(s, str) and s for item in s.split(',') if item.strip()),
        'prefix': set(item.strip() for s in df['prefix'] if isinstance(s, str) and s for item in s.split(',') if item.strip()),
    }

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
        create_dim_csv(unique_names, output_path)
        dim_df = pd.read_csv(output_path)
  
        create_bridge_csv(
            band_df=df,
            dim_df_for_type=dim_df,
            output_file_path=bridge_output_paths[item_type],
            item_type_label=item_type
        )

if __name__ == "__main__":
    main()