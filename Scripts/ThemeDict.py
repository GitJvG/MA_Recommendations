import sys
import os
import pandas as pd
from rapidfuzz import fuzz
from collections import Counter
from Helper.CleanThemes import basic_processing
import pickle
from collections import defaultdict

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
from Env import Env
env = Env.get_instance()

# Function to extract unique themes from the dataframe and count their frequency
def items_to_set(genre_series):
    genre_set = set()
    theme_count = Counter()  # Counter to hold theme frequencies
    for genre_string in genre_series:
        if pd.notna(genre_string):  # Ensure no NaN values are included
            genre_string = genre_string.strip()  # Strip leading/trailing spaces
            if genre_string:
                # Split by comma, strip whitespace, and add valid genres to the set
                for genre in genre_string.split(','):
                    genre_cleaned = genre.strip()
                    if len(genre_cleaned) <= 40 and genre_cleaned:  # Check for empty strings and length
                        genre_set.add(genre_cleaned)
                        theme_count[genre_cleaned] += 1  # Increase the count for each theme
    return genre_set, theme_count

# Function to group similar strings using RapidFuzz with frequency-based sorting
def group_themes(themes, theme_count, threshold=85):
    # Sort themes by frequency (most frequent first)
    sorted_themes = sorted(themes, key=lambda theme: theme_count[theme], reverse=True)
    
    theme_dict = defaultdict(list)
    for theme in sorted_themes:
        found_group = False
        
        # Try to add the theme to an existing group by checking against anchor words
        for anchor_word in theme_dict.keys():
            # Check if the theme contains the anchor word and if fuzzy matching passes
            if any(fuzz.partial_ratio(anchor_word, item) >= threshold for item in theme_dict[anchor_word]):
                if anchor_word in theme:
                    theme_dict[anchor_word].append(theme)
                    found_group = True
                    break

        # If no suitable group found, create a new entry in the dictionary
        if not found_group:
            anchor_word = max(theme.split(), key=len)
            theme_dict[anchor_word].append(theme)

    return theme_dict

# Function to create and save the grouped themes to a CSV file
def create_pickle():
    df = pd.read_csv(env.deta)['themes']
    df = df.dropna().apply(basic_processing)
    output_path = env.dim_theme_dict

    all_items, theme_count = items_to_set(df)  # Extract unique themes and count frequencies
    preprocessed_items = list(all_items)  # Clean strings before fuzzy matching
    groups = group_themes(preprocessed_items, theme_count)  # Group similar themes based on fuzzy matching

    # Step 4: Save the dictionary to a pickle file
    with open(output_path, 'wb') as pickle_file:
        pickle.dump(groups, pickle_file)

# Main execution
if __name__ == "__main__":
    create_pickle()
