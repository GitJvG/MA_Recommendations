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
with open(env.dim_theme_dict, 'rb') as pickle_file:
    groups = pickle.load(pickle_file)

# Create the anchor CSV (anchor -> anchor_id)
anchors = list(groups.keys())  # List of anchor words

# Create a DataFrame for anchors and assign anchor IDs
anchor_df = pd.DataFrame({
    'anchor_id': range(1, len(anchors) + 1),
    'anchor': anchors
})

# Save the anchor CSV
anchor_df.to_csv('anchor.csv', index=False)

bridge_data = []

# For each band, get the themes and their corresponding anchors
df = pd.read_csv(env.deta)
df['Themes'] = df['Themes'].dropna().apply(basic_processing)
df = df.dropna(subset='Themes')

for band_id, themes in zip(df['Band ID'], df['Themes']):
    for theme in themes.split(','):  # Split themes if they are comma-separated
        theme = theme.strip()
        # Find the anchor word by checking which anchor group the theme belongs to
        for anchor, theme_list in groups.items():
            if theme in theme_list:
                # Append the band_id and the corresponding anchor_id to the bridge data
                anchor_id = anchor_df[anchor_df['anchor'] == anchor].iloc[0]['anchor_id']
                bridge_data.append([band_id, anchor_id])

# Convert the bridge data to a DataFrame
bridge_df = pd.DataFrame(bridge_data, columns=['band_id', 'anchor_id'])

# Save the bridge CSV
bridge_df.to_csv('bridge.csv', index=False)

print("Anchor and Bridge CSVs created successfully.")