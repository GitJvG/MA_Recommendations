import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(project_root)

import pandas as pd
import re
from Env import Env
env= Env.get_instance()

def handle_prefix_and_hybrids(genre):
    """Handles a genre with a prefix and returns possible combinations in a comma-separated format."""
    genre = re.sub(rf'(?<!-)\s?\b{'with'}\b(?!-)', '', genre)
    # Strip the genre of any leading or trailing spaces
    genre = genre.strip()
    
    # If the genre contains a slash ('/'), it could be a hybrid genre
    if '/' in genre:
        # Check if the part before the slash looks like a valid prefix
        parts = genre.split(' ')
        prefix = ''
        mod_genre = genre
        
        # We treat the first part before '/' as a prefix only if it doesn't look like a hybrid genre
        # Example: "melodic death/doom" -> "melodic" is the prefix, "death/doom" is the hybrid
        if len(parts) > 1 and parts[0].isalpha():  # Only treat the first part as a prefix if it's a word
            prefix = parts[0]
            mod_genre = genre[len(prefix):].strip()  # Remove prefix to leave the hybrid genre
        
        hybrid_parts = mod_genre.split('/')
        
        combinations = set()
        
        for part in hybrid_parts:
            part = part.strip()  # Remove any unwanted spaces around each part
            if part:
                combinations.add(f"{prefix} {part}".strip())  # Add prefix + single genre part
        
        # Add the full hybrid combination
        combinations.add(f"{prefix} {mod_genre}".strip())
        
        # Return all combinations as a comma-separated string
        return ', '.join(sorted(combinations))
    
    # Otherwise, treat it as a single genre without a hybrid
    parts = genre.split()
    prefix = ''
    mod_genre = genre.strip()
    
    # If there's more than one part, consider it as a prefix + single genre
    if len(parts) > 1:
        prefix = ' '.join(parts[:-1]).strip()  # Everything except the last word is the prefix
        mod_genre = parts[-1].strip()  # The last part is the main genre
    
    # Now, return the combination of prefix and genre
    return f"{prefix} {mod_genre}".strip() if prefix else mod_genre

def basic_processing(genre):
    genres = genre.lower()
    genres = re.sub(r'\(.*?\)', '', genres) # removes anything between aprenthesis
    genres = re.sub(r'\s?/\s?', '/', genres) # Removes spaces before and after '/'
    genres = re.sub(r'\s+', ' ', genres) # Reduces more than one spaces to one space
    genres = re.sub(r'[^\x20-\x7E]', '', genres) # Removes non-ASCII
    genres = re.sub(r';', ',', genres) # Replace semicolon with a comma. Metallum uses this for time related distinctions but that isn't an important distinction for me.
    genres = re.sub(r'[()]+', '', genres).strip() # Removes remaining parenthesis

    # Remove 'Metal' (or ' Metal' if followed by '/' to create new hybrids, i.e. death metal/black metal-> death/black)
    genres = re.sub(r'(?<!-)\s?/?\bmetal\b(?!-)', '', genres).strip() 
    # Finally remove any remaining common unwanted words
    for word in env.unwanted:
        genres = re.sub(rf'(?<!-)\s?\b{word}\b(?!-)', '', genres)
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
    # Added super_special_cases for three-part entities such as 'black 'n' roll'
    last_part = split_parts[-1]

    if last_part in env.binary:
        result = 2
    elif last_part in env.ternary:
        result = 3
    else:
        result = 1
    return result

def extract_primal(genre):
    """Extracts the primal genre, checking for hybrid and non-hybrid genres."""
    genre = re.sub(r"\s?'n'\s?roll", '', genre)
    # Split by comma and for each part only keep what is before 'with'
    parts = [part.split('with')[0].strip() for part in genre.split(',')]

    primal_genres = set()  # To store the primal genres
    prefixes = set()
    # Handling hybrids and single genres
    for part in parts:
        # Check if the part contains a '/'
        if '/' in part.split()[-1]:
            subparts = part.rsplit('/', 1) # Only split at the final / as those before can be hybrid prefixes

            # For each subgenre, determine how many parts to take based on part_exceptions
            count_before = part_exceptions(subparts[0].strip().split())
            count_after = part_exceptions(subparts[1].strip().split())
            
            # Extract the relevant parts from the original part
            # Get the first part before '/', and take the appropriate number of words from the start
            part_before = ' '.join(subparts[0].split()[-count_before:])

            # Get the second part after '/', and take the appropriate number of words from the end
            part_after = ' '.join(subparts[1].split()[-count_after:])

            # Reassemble the hybrid genre with '/' after processing
            primal_genre = f"{part_before}/{part_after}"
            prefix = ', '.join(subparts[0].split()[:-count_before]) # part before what was kept
        else:
            # Process as a single non-hybrid genre
            count = part_exceptions(part.split())
            primal_genre = ' '.join(part.split()[-count:])
            prefix = ', '.join(part.split()[:-count])

        primal_genres.add(primal_genre)
        prefixes.add(prefix)
        
    primal_genre = ', '.join(sorted(primal_genres))
    prefixes = ', '.join(sorted(prefixes))
   
    # Split hybrid primals and prefixes
    split_parts = [part.strip() for part in primal_genre.split(',')]

    split_hybrid = set()
    for part in split_parts:
        # Splits on / and strips and filters out empty parts
        split_hybrid_parts = [x.strip() for x in part.split('/') if x.strip()]
        for x in split_hybrid_parts: split_hybrid.add(x)
    split_primal_genres = ', '.join(sorted(split_hybrid))

    split_prefixes = [part.strip() for part in prefixes.split(',')]

    hybrid_prefix = set()
    for prefixes in split_prefixes:
        split_prefix_parts = [x.strip() for x in prefixes.split('/') if x.strip()]  
        for x in split_prefix_parts:
            hybrid_prefix.add(x)

    split_prefixes = ', '.join(sorted(hybrid_prefix))

    return primal_genre, split_primal_genres, split_prefixes
    
def advanced_clean(genres):
    """single_primals, primal, prefixes"""
    genre = basic_processing(genres)
    primal, single_primals, prefixes = extract_primal(genre)
    return single_primals, primal, prefixes if prefixes else None

if __name__ == "__main__":
    pass