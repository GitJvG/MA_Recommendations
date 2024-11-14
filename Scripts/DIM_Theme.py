import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import pandas as pd
from Env import Env
env = Env.get_instance()
from Helper.CleanThemes import basic_processing
import pickle

# Load your dictionary (anchor-value pairs) from the pickle file
def save_DIM_themes(groups):
    anchors = list(groups.keys())  # List of anchor words

    # Create a DataFrame for anchors and assign anchor IDs
    dim_themes = pd.DataFrame({
        'theme_id': range(1, len(anchors) + 1),
        'name': anchors
    })
    # Save the anchor CSV
    dim_themes.to_csv(env.dim_theme, index=False)

def save_Bandthemes(groups, dim_themes):
    bridge_data = []

    # For each band, get the themes and their corresponding anchors
    df = pd.read_csv(env.deta)
    df['themes'] = df['themes'].dropna().apply(basic_processing)
    df = df.dropna(subset='themes')

    for band_id, themes in zip(df['band_id'], df['themes']):
        for theme in themes.split(','):  # Split themes if they are comma-separated
            theme = theme.strip()
            # Find the anchor word by checking which anchor group the theme belongs to
            for anchor, theme_list in groups.items():
                if theme in theme_list:
                    # Append the band_id and the corresponding anchor_id to the bridge data
                    anchor_id = dim_themes[dim_themes['name'] == anchor].iloc[0]['theme_id']
                    bridge_data.append([band_id, anchor_id])

    # Convert the bridge data to a DataFrame
    bridge_df = pd.DataFrame(bridge_data, columns=['band_id', 'theme_id'])

    # Save the bridge CSV
    bridge_df.to_csv(env.band_theme, index=False)

def main():
    with open(env.dim_theme_dict, 'rb') as pickle_file:
        groups = pickle.load(pickle_file)
    save_DIM_themes(groups)
    dim_themes = pd.read_csv(env.dim_theme)
    save_Bandthemes(groups, dim_themes)
    print("Anchor and Bridge CSVs created successfully.")