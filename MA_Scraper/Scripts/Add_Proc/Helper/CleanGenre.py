import regex as re
from MA_Scraper.Env import Env
import pandas as pd
env = Env.get_instance()

def basic_processing(df_series):
    df_series = df_series.copy()
    df_series = df_series.str.lower()

    df_series = df_series.str.replace(r'[^\x20-\x7E]|\(.*?\)', '', regex=True) # Remove non-ascii and everything in parenthesis
    df_series = df_series.str.replace(r'[;.]', ',', regex=True) # replaces semicolon and period with comma

    unwanted_patterns = [re.escape(word) for word in env.unwanted]
    combined_unwanted_regex = r'(?<!-)\s?\b(?:' + '|'.join(unwanted_patterns) + r')\b(?!-)'
    df_series = df_series.str.replace(combined_unwanted_regex, '', regex=True)

    df_series = df_series.str.replace(r'[\s-]+(?!garde|\bbeat\b)', ' ', regex=True) # replaces consecutive spaces with a single space
    df_series = df_series.str.replace(r'\s?/\s?', '/', regex=True) # removes space around /
    df_series = df_series.str.replace(r'\(.*?\)|\s?\'n\'\s?roll', '', regex=True) # removes 'n roll and parenthesis
    main_genres_check = ['metal', 'punk', 'rock', 'metal']
    for genre in main_genres_check:
        df_series = df_series.str.replace(rf'(?<=\b{genre})\s*/', ', ', regex=True) # replaces / with comma if preceeded by main genre

    df_series = df_series.str.replace(r'(?<!-),?\s?/?\bmetal\b(?!-)', '', regex=True) # removes metal and optional leading slashes

    # remove everything after with
    df_series = df_series.str.replace(r'with[^,]*', '', regex=True)
    df_series = df_series.str.replace(r'\s?,\s?', ',', regex=True) # removes space around ','
    
    df_series = df_series.str.replace(' wave', 'wave')
    df_series = df_series.str.replace(r'\bfilm score\b', 'soundtrack', regex=True)
    df_series = df_series.str.replace(r'\baor\b', 'rock', regex=True)
    df_series = df_series.str.replace(r'\brac\b|\bscreamo\b', 'punk', regex=True)
    df_series = df_series.str.replace(r'\bbossa nova\b', 'jazz', regex=True)

    genres_with_space = ["new age","easy listening","spoken word","a cappella","trip hop","hip hop","middle eastern", "drum and bass"]
    regex_pattern = r'\b(' + '|'.join(re.escape(phrase) for phrase in genres_with_space) + r')\b'
    df_series = df_series.str.replace(regex_pattern, lambda x: x.group(0).replace(' ', '_'), regex=True)

    df_series = df_series.str.replace(r'\bbossa nova\b', 'jazz', regex=True)

    normalize_patterns = [re.escape(word) for word in ["grind", "electro", "noise", "synth", "wave", "crust", "dub", "rock", "punk", "reggae", "avant"]]
    normalized_genre_pattern = r'\b\w*(' + '|'.join(normalize_patterns) + r')\w*\b'
    df_series = df_series.str.replace(normalized_genre_pattern, r'\1', regex=True)

    return df_series

def elements(genre):
    """Removes 'with influences' endings and returns the genre and the elements separately in a comma-separated format."""
    # Split on commas or semicolons
    parts = re.split(r'[;,]+', genre.lower())
    genre_without_element = set()
    element_parts = set()

    for part in parts:
        part = re.sub(r'[()]+', '', part).strip()

        # Handle "with" or "influences" descriptions
        if 'with' in part:
            part_split = re.split(r'with', part)
            genre_main = part_split[0].strip()  # The main genre
            
            element_description = part_split[1].strip() if len(part_split) > 1 else ""
            
            # Clean the "elemental" part (e.g., "with doom elements")
            element_cleaned = ' '.join([word for word in element_description.split()])
            if element_cleaned:
                element_parts.add(element_cleaned)
            
            # Clean the main genre (without the element part)
            genre_cleaned = ' '.join([word for word in genre_main.split()])
            if genre_cleaned:
                genre_without_element.add(genre_cleaned)
        else:
            # If no "with" or "influences", just clean the genre
            genre_cleaned = ' '.join([word for word in part.split()])
            if genre_cleaned:
                genre_without_element.add(genre_cleaned)

    # Return both genre without element and the elements as comma-separated strings
    cleaned_genre_output = ', '.join(sorted(genre_without_element))
    element_output = ', '.join(sorted(element_parts)) if element_parts else None

    return cleaned_genre_output, element_output
    
def dissect_genre(series):
    df_exploded = series.str.split(',').explode()
    df_exploded = df_exploded.str.strip()
    dissected_df = pd.DataFrame({'row_id': df_exploded.index, 'og_genre': df_exploded.values})

    main_pattern = r"^(?:(.+?)\s+)?([^/\s]+(?:/[^/\s]+)?)$" # Match any non white character optionally followed by a '/' and any non white character
    full_pattern = r"^(.*?)\s*?" + main_pattern + r"$"
    extracted_data = dissected_df['og_genre'].str.extract(full_pattern, flags=re.IGNORECASE)

    dissected_df['prefix'] = extracted_data[1].str.replace(r'[ /]', ',', regex=True)
    dissected_df['hybrid_genre'] = extracted_data[2]
    dissected_df['genre'] = dissected_df['hybrid_genre'].str.replace('/', ',')

    dissected_df[['row_id', 'og_genre', 'genre', 'prefix', 'hybrid_genre']]

    return dissected_df

def process_genres(df_series):
    df_series = basic_processing(df_series)
    df_series2 = dissect_genre(df_series)

    return df_series2