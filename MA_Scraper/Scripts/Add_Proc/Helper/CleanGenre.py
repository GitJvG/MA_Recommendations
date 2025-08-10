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
    df_series = df_series.str.replace(r'with[^,]*', '', regex=True)
    df_series = df_series.str.replace(r'\s?,\s?', ',', regex=True) # removes space around ','

    genres_with_space = ["new age","easy listening","spoken word","a cappella","trip hop","hip hop","middle eastern", "drum and bass"]
    regex_pattern = r'\b(' + '|'.join(re.escape(phrase) for phrase in genres_with_space) + r')\b'
    df_series = df_series.str.replace(regex_pattern, lambda x: x.group(0).replace(' ', '_'), regex=True)

    df_series = df_series.str.replace(' wave', 'wave')
    normalize_patterns = [re.escape(word) for word in ["grind", "electro", "noise", "synth", "wave", "crust", "rock", "punk", "reggae", "avant"]]
    normalized_genre_pattern = r'\b\w*(' + '|'.join(normalize_patterns) + r')\w*\b'
    df_series = df_series.str.replace(normalized_genre_pattern, r'\1', regex=True)
    
    genre_replacements = {
        'world': ['enka'],
        'symphonic': ['epic'],
        'folk': ['celtic', 'roots', 'neofolk'],
        'ambient': ['psybient'],
        'soundtrack': ['film score'],
        'reggae': ['dub'],
        'rock': ['aor', 'psychobilly'],
        'punk': ['rac', 'screamo'],
        'hardcore': ['d-beat', 'mathcore'],
        'jazz': ['bossa nova'],
        'avant-garde': ['experimental'],
        'electronic': [
            'techno', 'ebm', 'electro', 'downtempo', 'trance', 'dance', 'new_age',
            'chiptune', 'drum_and_bass', 'dubstep', 'house', 'breakcore'
        ]
    }

    for new_genre, old_genres_list in genre_replacements.items():
        escaped_genres = [re.escape(genre) for genre in old_genres_list]
        pattern = r'\b(' + '|'.join(escaped_genres) + r')\b'
        df_series = df_series.str.replace(pattern, new_genre, regex=True)

    return df_series
    
def dissect_genre(series):
    df_exploded = series.str.split(',').explode()
    df_exploded = df_exploded.str.strip()
    dissected_df = pd.DataFrame({'row_id': df_exploded.index, 'og_genre': df_exploded.values})

    main_pattern = r"^(?:(.+?)\s+)?([^\/\s]+(?:[\/][^\s\/]+)*)$" # Match any non white character optionally followed by a '/' and any non white character
    extracted_data = dissected_df['og_genre'].str.extract(main_pattern, flags=re.IGNORECASE)

    exploded_prefix = extracted_data[0].str.split(r'[ /]').explode().str.strip().to_frame(name='prefix')
    exploded_genre = extracted_data[1].str.split('/').explode().str.strip().to_frame(name='genre')

    dissected_df = pd.merge(dissected_df, exploded_prefix, left_index=True, right_index=True, how='left')
    dissected_df = pd.merge(dissected_df, exploded_genre, left_index=True, right_index=True, how='left')

    return dissected_df

def process_genres(df_series):
    df_series = basic_processing(df_series)
    df_series2 = dissect_genre(df_series)

    return df_series2