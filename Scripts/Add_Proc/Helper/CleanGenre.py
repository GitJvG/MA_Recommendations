import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(project_root)
import re
from Env import Env
env = Env.get_instance()

def replace_wrong_comma(genre):
    """Replaces element comma with 'and' to prevent unintended splitting."""
    def replace_with_and(match):
        return match.group(0).replace(',', ' and')

    genre = re.sub(r'with(.*?)(and)', replace_with_and, genre)
    return genre

def basic_processing(genre):
    genres = genre.lower()
    genres = re.sub(r'\(.*?\)', '', genres) # removes anything between parenthesis
    genres = re.sub(r'\s?/\s?', '/', genres) # Removes spaces before and after '/'
    genres = re.sub(r'\s+', ' ', genres) # Reduce consecutive spaces to one space
    genres = re.sub(r'[^\x20-\x7E]', '', genres) # Removes non-ASCII
    genres = re.sub(r';', ',', genres) # Replace semicolon with a comma. Metallum uses this for time related distinctions but that isn't an important distinction for me.
    genres = re.sub(r'[()]+', '', genres).strip() # Removes remaining parenthesis

    # Remove 'Metal' (or ' Metal' if followed by '/' to create new hybrids, i.e. death metal/black metal-> death/black)
    genres = re.sub(r'(?<!-)\s?/?\bmetal\b(?!-)', '', genres).strip() 
    # Finally remove any remaining common unwanted words
    for word in env.unwanted:
        genres = re.sub(rf'(?<!-)\s?\b{word}\b(?!-)', '', genres)

    genres = replace_wrong_comma(genres)

    return genres

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
    genre = re.sub(r"\s?'n'\s?roll", '', genre)
    parts = [part.split('with')[0].strip() for part in genre.split(',')]

    primal_genres = set()
    prefixes = set()

    for part in parts:
        partslist = part.split()
        if '/' not in partslist[-1]:

            count = part_exceptions(partslist)
            primal_genre = ' '.join(partslist[-count:])
            prefixList = partslist[:-count]
        else:
            subparts = part.rsplit('/', 1) # Only split at the final / as earlier ones can be hybrid prefixes

            count_before = part_exceptions(subparts[0].strip().split())
            count_after = part_exceptions(subparts[1].strip().split())
            
            part_before = ' '.join(subparts[0].split()[-count_before:])
            part_after = ' '.join(subparts[1].split()[-count_after:])
            primal_genre = f"{part_before}/{part_after}"

            prefixList = subparts[0].split()[:-count_before]

        primal_genres.add(primal_genre)
        for prefix in prefixList:
            prefixes.add(prefix)

    def split_and_strip(parts):
        return {x.strip() for part in parts for x in part.split('/') if x.strip()}

    split_primal_genres = split_and_strip(primal_genres)
    split_prefixes = split_and_strip(prefixes)

    return split_primal_genres, primal_genres, split_prefixes

def advanced_clean_flat(genres):
    """Returns a flattened list for bridge table creation."""
    try:
        genre = basic_processing(genres)
        single_primals, primal, prefixes = dissect_genre(genre)

        results = []
        if single_primals:
            results.extend([(item.strip(), 'single_primal') for item in single_primals])
        if primal:
            results.extend([(item.strip(), 'primal') for item in primal])
        if prefixes:
            results.extend([(item.strip(), 'prefix') for item in prefixes])

        return results
    except Exception as e:
        print(f"Error processing genre: {genres} - {e}")
        raise