import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import pandas as pd
from Env import Env
env = Env.get_instance()
from DataScripts.Helper.CleanThemes import basic_processing
import pickle

def save_DIM_themes(anchor_groups):
    anchors = list(anchor_groups.keys())

    theme = pd.DataFrame({
        'theme_id': range(1, len(anchors) + 1),
        'name': anchors
    })
    theme.to_csv(env.theme, index=False)

def save_Bandthemes(anchor_groups, theme_df):
    bridge_data = []

    # For each band, get the themes and their corresponding anchors
    df = pd.read_csv(env.deta)
    df['themes'] = df['themes'].dropna().apply(basic_processing)
    df = df.dropna(subset='themes')

    for band_id, themes in zip(df['band_id'], df['themes']):
        for theme in themes.split(','):
            theme = theme.strip()
            # Find the anchor word by checking which anchor group the theme belongs to
            for anchor, theme_list in anchor_groups.items():
                if theme in theme_list:
                    anchor_id = theme_df[theme_df['name'] == anchor].iloc[0]['theme_id']
                    bridge_data.append([band_id, anchor_id])

    themes_df = pd.DataFrame(bridge_data, columns=['band_id', 'theme_id'])
    themes_df.to_csv(env.themes, index=False)

def main():
    with open(env.dim_theme_dict, 'rb') as pickle_file:
        anchor_groups = pickle.load(pickle_file)
    save_DIM_themes(anchor_groups)
    theme_df = pd.read_csv(env.theme)
    save_Bandthemes(anchor_groups, theme_df)
    print("Anchor and Bridge CSVs created successfully.")

if __name__ == '__main__':
    main()