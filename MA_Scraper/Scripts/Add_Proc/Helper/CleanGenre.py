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

    df_series = df_series.str.replace(r'[\s-]+', ' ', regex=True) # replaces consecutive spaces with a single space
    df_series = df_series.str.replace(r'\s?/\s?', '/', regex=True) # removes space around /
    df_series = df_series.str.replace(r'\(.*?\)|\s?\'n\'\s?roll', '', regex=True) # removes 'n roll and parenthesis
    main_genres_check = ['metal', 'punk', 'rock']
    for genre in main_genres_check:
        df_series = df_series.str.replace(rf'(?<=\b{genre})\s*/', ', ', regex=True) # replaces / with comma if preceeded by main genre

    df_series = df_series.str.replace(r'(?<!-),?\s?/?\bmetal\b(?!-)', '', regex=True) # removes metal and optional leading slashes

    # match "with <genre>, <genre> and <genre> influences and convert to "with <genre> and <genre> and <genre> influences and convert for proper splitting and influence detection"
    df_series = df_series.str.replace(r'(with)(.*?)(and)', lambda m: m.group(1) + m.group(2).replace(',', ' and') + m.group(3), regex=True)
    df_series = df_series.str.replace(r'\s?,\s?', ',', regex=True) # removes space around ','
    
    df_series = df_series.str.replace(' wave', 'wave')
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

def part_exceptions(split_parts):
    # Last word except for when it is an exception ('age' in 'new age' then take last 2)
    # Added ternary for three-part entities such as 'black 'n' roll'
    last_part = split_parts[-1]

    if last_part in env.binary:
        result = 2
    elif last_part in env.ternary:
        result = 3
    else:
        result = 1
    return result

def dissect_genre(genre):
    """Extracts the primal genre, checking for hybrid and non-hybrid genres."""
    parts = [part.split('with')[0].strip() for part in genre.split(',')]

    hybrid_genre = set()
    prefixes = set()

    for part in parts:
        partslist = part.split()
        if '/' not in partslist[-1]:
            count = part_exceptions(partslist)
            primary_genre = ' '.join(partslist[-count:])
            prefixlist = partslist[:-count]
        else:
            subparts = part.rsplit('/', 1) # Only split at the final / as earlier ones can be hybrid prefixes

            count_before = part_exceptions(subparts[0].strip().split())
            count_after = part_exceptions(subparts[1].strip().split())
            
            part_before = ' '.join(subparts[0].split()[-count_before:])
            part_after = ' '.join(subparts[1].split()[-count_after:])
            primary_genre = f"{part_before}/{part_after}"

            prefixlist = subparts[0].split()[:-count_before]

        hybrid_genre.add(primary_genre)
        for prefix in prefixlist:
            prefixes.add(prefix)

    def split_and_strip(parts):
        return {x.strip() for part in parts for x in part.split('/') if x.strip()}

    genre = split_and_strip(hybrid_genre)
    prefixes = split_and_strip(prefixes)

    genre_output = ','.join(sorted(list(genre)))
    hybrid_genre_output = ','.join(sorted(list(hybrid_genre)))
    prefixes_output = ','.join(sorted(list(prefixes)))

    return genre_output, hybrid_genre_output, prefixes_output

def process_genres(df_series):
    df_series = basic_processing(df_series)
    df_series2 = df_series.apply(dissect_genre).apply(pd.Series)
    df_series2.columns = ['genre', 'hybrid_genre', 'prefix']

    return df_series2