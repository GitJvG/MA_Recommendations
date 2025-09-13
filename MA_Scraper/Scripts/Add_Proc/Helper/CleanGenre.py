import regex as re
from MA_Scraper.Env import Env
import pandas as pd
env = Env.get_instance()

def exception(df_series):
    for genre in ['metal', 'punk', 'rock','shoegaze', 'shred', 'grunge', 'aor', 'hip_hop', 'grind', 'wave', 'jazz']:
        df_series = df_series.str.replace(rf'(?<=\b{genre})\s*/', ', ', regex=True)
    return df_series

def basic_processing(df_series):
    df_series = df_series.copy()
    df_series.loc[:] = df_series.str.lower()

    df_series.loc[:] = df_series.str.replace(r'[^\x20-\x7E]|\(.*?\)', '', regex=True) # Remove non-ascii and everything in parenthesis
    df_series.loc[:] = df_series.str.replace(r'[;.]', ',', regex=True) # replaces semicolon and period with comma

    unwanted_genre_words = ["earlier", "later", "early", "or", "mid", "late", "from", "music","ballad"]
    unwanted_patterns = [re.escape(word) for word in unwanted_genre_words]
    combined_unwanted_regex = r'(?<!-)\s?\b(?:' + '|'.join(unwanted_patterns) + r')\b(?!-)'
    df_series.loc[:] = df_series.str.replace(combined_unwanted_regex, '', regex=True)

    df_series.loc[:] = df_series.str.replace(r'[\s-]+(?!garde|\bbeat\b)', ' ', regex=True) # replaces consecutive spaces with a single space
    df_series.loc[:] = df_series.str.replace(r'/{2,}', '/', regex=True)

    df_series.loc[:] = df_series.str.replace(r'\s?/\s?', '/', regex=True) # remometalves space around /
    df_series.loc[:] = df_series.str.replace(r"([\w-]+)\s*'n'\s*roll", r"roll \1", regex=True) # "x 'n' roll" becomes "roll x"

    #df_series.loc[:] = df_series.str.replace(r'(?<!-),?\s?/?\bmetal\b(?!-)', '', regex=True) # removes metal and optional leading slashes
    df_series.loc[:] = df_series.str.replace(r'with.*?elements|with.*?influences', '', regex=True)

    df_series.loc[:] = df_series.str.replace(r'\s?,\s?', ',', regex=True) # removes space around ','
    df_series.loc[:] = df_series.str.replace(r'with[^,]*', '', regex=True)
    df_series.loc[:] = df_series.str.replace(r'!|influences|with|elements', '', regex=True)

    df_series.loc[:] = df_series.str.replace(r'\bhardcore\b(?!\s*punk)', 'hardcore punk', regex=True)

    df_series.loc[:] = df_series.str.replace(' wave', 'wave')
    normalize_patterns = [re.escape(word) for word in ["grind", "electro", "noise", "synth", "wave", "crust", "rock", "punk", "reggae", "avant",'sludge']]
    normalized_genre_pattern = r'\b\w*(' + '|'.join(normalize_patterns) + r')\w*\b'
    df_series.loc[:] = df_series.str.replace(normalized_genre_pattern, r'\1', regex=True)

    df_series = exception(df_series)

    for genre in ['hardcore','crust','powerviolence']:
        df_series.loc[:] = df_series.str.replace(rf'\b{genre}\b(?!\s*punk)', f'{genre} punk', regex=True)

    for genre in ['death','black','thrash','sludge','doom','crossover', 'nwobhm','djent','shred','groove','symphonic','progressive','technical','avant-garde','alternative','glam','atmospheric','gothic','experimental']:
        df_series.loc[:] = df_series.str.replace(rf'\b{genre}\b(?!\s*(?:metal|rock|punk))', f'{genre} metal', regex=True)

    for genre in ['surf']:
        df_series.loc[:] = df_series.str.replace(rf'\b{genre}\b(?!\s*rock)', f'{genre} rock', regex=True)

    for genre in ['deathcore', 'mathcore']:
        df_series.loc[:] = df_series.str.replace(rf'\b{genre}\b(?!\s*metalcore)', f'{genre} metalcore', regex=True)

    df_series = exception(df_series)

    genres_with_space = ["new age","easy listening","spoken word","a cappella","trip hop","hip hop","middle eastern", "drum and bass"]
    regex_pattern = r'\b(' + '|'.join(re.escape(phrase) for phrase in genres_with_space) + r')\b'
    df_series.loc[:] = df_series.str.replace(regex_pattern, lambda x: x.group(0).replace(' ', '_'), regex=True)

    for genre in ['dungeon synth']:
        df_series.loc[:] = df_series.str.replace(rf'\/(?=\s*{genre})', ',', regex=True)

    genre_replacements = {
        'symphonic': ['epic'],
        'folk-world': ['celtic','neofolk','folk','acoustic','pagan','viking', 'enka','flamenco','country','bluegrass','roots', 'blues','world','medieval','dub','ska','reggae'],
        'ambient': ['psybient'],
        'soundtrack': ['film score'],
        'rock': ['aor', 'psychobilly'],
        'punk': ['rac', 'screamo', 'oi'],
        'hardcore punk': ['d-beat'],
        'jazz': ['bossa nova', 'funk'],
        'avant-garde': ['experimental'],
        'electronic': ['techno', 'ebm', 'electro', 'downtempo', 'trance', 'dance', 'new_age',
            'chiptune', 'drum_and_bass', 'dubstep', 'house', 'breakcore', 'glitch', 'synth'],
        'death': ['daeth'],
        'hip_hop': ['rap','rapcore','phonk','trip_hop','trap'],
        'alternative': ['nu'],
        'pop': ['easy_listening', 'soft'],
        'classical': ['neoclassical','orchestral','opera'],
        'melodic': ['meodic'],
        'progessive': ['progressive'],
        'crossover': ['crossover thrash'],
        'powerviolence': ['power electronics'],
        'industrial': ['digital'],
        'alternative rock': ['grunge', 'jazz rock', 'hip_hop rock'],
        'alternative metal': ['funk metal', 'jazz metal','hip_hop metal'],
        'fusion jazz': ['jazz fusion']
    }

    for new_genre, old_genres_list in genre_replacements.items():
        escaped_genres = [re.escape(genre) for genre in old_genres_list]
        pattern = r'\b(' + '|'.join(escaped_genres) + r')\b' 
        df_series.loc[:] = df_series.str.replace(pattern, new_genre, regex=True)

    for genre in ['grind', 'wave', 'jazz']:
        df_series.loc[:] = df_series.str.replace(rf'(?<=\b{genre})\s*/', ', ', regex=True) # replaces / with comma if preceeded by main genre

    df_series = exception(df_series)

    return df_series
    
def dissect_genre(series):
    df_exploded = series.str.split(',').explode()
    df_exploded.iloc[:] = df_exploded.str.strip()
    dissected_df = pd.DataFrame({'row_id': df_exploded.index, 'og_genre': df_exploded.values})

    main_pattern = r"^(?:(.+?)\s+)?([^\/\s]+(?:[\/][^\s\/]+)*)$" # Match any non white character optionally followed by a '/' and any non white character
    extracted_data = dissected_df['og_genre'].str.extract(main_pattern, flags=re.IGNORECASE)

    terms_to_remove = ['metal', 'punk', 'rock']
    exploded_prefix = extracted_data[0].str.split(r'[ /]').explode().str.strip().to_frame(name='prefix')
    exploded_prefix = exploded_prefix[~exploded_prefix['prefix'].isin(terms_to_remove)]
    exploded_genre = extracted_data[1].str.split('/').explode().str.strip().to_frame(name='genre')

    dissected_df = pd.merge(dissected_df, exploded_prefix, left_index=True, right_index=True, how='left')
    dissected_df = pd.merge(dissected_df, exploded_genre, left_index=True, right_index=True, how='left')

    return dissected_df[['row_id','prefix','genre']]

def process_genres(df_series):
    df_series = basic_processing(df_series)
    dissected_df = dissect_genre(df_series)

    return dissected_df