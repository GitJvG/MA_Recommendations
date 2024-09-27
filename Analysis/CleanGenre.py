import pandas as pd
import re

data = pd.read_csv('Datasets/MA_Bands.csv')
DF = pd.DataFrame(data)

def clean_and_split_genre(genre):
    """Cleans and splits the genre string into a list of unique words.
    e.g. Experimental/Symphonic Black/Death Metal -> [Experimental, Symphonic, Black, Death]"""
    # Define unwanted words
    unwanted_words = ['metal', 'with', 'influences', 'earlier', 'later', 
                      'early', '', ' ', 'and', 'or']
    
    # Remove unwanted characters and split by '/' or whitespace or ','
    parts = re.split(r'[ /;,-]+', genre.lower())
    
    # Remove unwanted characters and strip any extra whitespace
    cleaned_parts = {re.sub(r'[()]+', '', part).strip() for part in parts if part.strip()}
    
    # Filter unwanted words
    cleaned_parts = [part for part in cleaned_parts if part not in unwanted_words]
    
    # Remove duplicates and sort the list
    return sorted(set(cleaned_parts))

def simple_clean(genre):
    """Cleans genre while preserving word order and removing unwanted words."""
    # Define unwanted words and characters to remove
    S_unwanted_words = ['with', 'influences', 'earlier', 'later', 'early', 'and', 'or']
    
    # Split genre string by semicolon or comma, preserving genre phrases
    parts = re.split(r'[;/,]+', genre.lower())
    
    cleaned_parts = []
    
    # Process each part separately
    for part in parts:
        # Remove parentheses and strip extra whitespace
        part = re.sub(r'[()]+', '', part).strip()
        
        # Remove unwanted words but preserve the order of remaining words
        words = part.split()
        cleaned_words = [word for word in words if word not in S_unwanted_words]
        
        # Join cleaned words back into a phrase and add to cleaned_parts list
        if cleaned_words:
            cleaned_parts.append(' '.join(cleaned_words))
    
    # Join all cleaned parts into a final string, maintaining the original order
    return ' '.join(cleaned_parts)

def process_genres(df, genre_column):
    """Adds a fully processed genre column [Processed Genre] and performs basic normalization on the provided genre column."""
    # Apply the cleaning function to the specified genre column
    df['Processed Genre'] = df[genre_column].apply(clean_and_split_genre)
    df[genre_column] = df[genre_column].apply(simple_clean)
    df[genre_column] = df[genre_column].apply(lambda genres: ' '.join(genres) if isinstance(genres, list) else genres)
    return df