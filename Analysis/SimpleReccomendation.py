import pandas as pd
import sys
import os
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD

# Load environment variables and database connection
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from SQLpush import loadSQLpath

load_dotenv()
LYRICS = os.getenv('BANLYR')
BANDSFILE = os.getenv('BANDPAR')
engine = loadSQLpath()

# Loading and basic data transformations
lyrics_df = pd.read_csv(LYRICS)
bands_df = pd.read_csv(BANDSFILE)


def normalize_genres_to_list(genre_string):
    # Split the string by semicolon and strip whitespace
    genres = [genre.split('(')[0].strip() for genre in genre_string.split(';')]
    return [genre.strip().lower() for genre in genres if genre]  # Normalize to lowercase and filter out empty strings

bands_df['Normalized Genre List'] = bands_df['Genre'].apply(normalize_genres_to_list)
"""A band with the genre: "Thrash Metal (early); Progressive Metal (later)" should be a match with a band with the genre 
Progressive Thrash Metal"""
print(bands_df[['Band Name', 'Normalized Genre List']])

# Preprocess themes
lyrics_df['Themes:'] = lyrics_df['Themes:'].str.split(',')
lyrics_df['Themes:'] = lyrics_df['Themes:'].apply(lambda x: ', '.join([theme.strip() for theme in x if isinstance(x, list) and theme.strip()]) if isinstance(x, list) else x)
lyrics_df = lyrics_df.dropna(subset=['Themes:'])
lyrics_df = lyrics_df[lyrics_df['Themes:'] != '']
lyrics_df['Themes:'] = lyrics_df['Themes:'].str.lower()

# Merge datasets
merged_df = pd.merge(bands_df, lyrics_df, how='inner', on='Band ID')
merged_df['Genre'] = merged_df['Genre'].str.split(',')
merged_df = merged_df.explode('Genre')
merged_df['combined_features'] = merged_df['Genre'] + ' ' + merged_df['Themes:']

# Global DataFrame for similar bands
similar_artists_df = pd.read_csv('Datasets/MA_Similar.csv')
similar_artists_df = pd.DataFrame(similar_artists_df, columns=['Band ID', 'Similar Artist ID', 'Score'])



# Function to get similar bands (same as before)
def get_complete_similar_bands(band_id):
    filtered_similar_bands = similar_artists_df[
        (similar_artists_df['Band ID'] == band_id) | (similar_artists_df['Similar Artist ID'] == band_id)
    ]
    bands_listing_original = similar_artists_df[similar_artists_df['Similar Artist ID'] == band_id]
    complete_bands = pd.concat([
        filtered_similar_bands[['Similar Artist ID', 'Score']],
        bands_listing_original[['Band ID', 'Score']].rename(columns={'Band ID': 'Similar Artist ID'})
    ])
    return aggregate_similar_bands(complete_bands)

def aggregate_similar_bands(filtered_df):
    aggregated_df = filtered_df.groupby('Similar Artist ID', as_index=False).agg({'Score': 'max'})
    return aggregated_df.sort_values(by='Score', ascending=False).reset_index(drop=True)

# Function to get recommendations based on band ID
def get_recommendations(band_id):
    band_info = merged_df[merged_df['Band ID'] == band_id]
    if band_info.empty:
        return "Band not found."

    # Get the normalized genre list for the specified band
    band_genres = set(normalize_genres_to_list(band_info['Genre'].values[0]))

    # Get similar bands
    similar_bands_df = get_complete_similar_bands(band_id)
    similar_band_ids = similar_bands_df['Similar Artist ID'].tolist()

    # Filter for bands of the same genres
    same_genre_df = merged_df.reset_index(drop=True)

    # Include similar bands in the genre-based recommendations
    filtered_similar_genre_df = same_genre_df[same_genre_df['Band ID'].isin(similar_band_ids)].reset_index(drop=True)

    if filtered_similar_genre_df.empty:
        return "No similar genre bands found."

    # Add a column to check for genre overlap
    filtered_similar_genre_df['Genre Overlap'] = filtered_similar_genre_df['Normalized Genre List'].apply(
        lambda genres: len(band_genres.intersection(set(genres))) > 0
    )

    # Filter bands that have genre overlap
    overlap_bands_df = filtered_similar_genre_df[filtered_similar_genre_df['Genre Overlap']].reset_index(drop=True)

    if overlap_bands_df.empty:
        return "No similar bands found with overlapping genres."

    # Recompute TF-IDF matrix for the overlapping bands
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(overlap_bands_df['combined_features'])

    # Dimensionality Reduction
    n_components = min(20, tfidf_matrix.shape[1])
    svd = TruncatedSVD(n_components=n_components)
    tfidf_matrix_reduced = svd.fit_transform(tfidf_matrix)

    # Compute cosine similarity matrix
    cosine_sim_genre = cosine_similarity(tfidf_matrix_reduced)

    # Find index of the band in the filtered DataFrame
    idx = overlap_bands_df[overlap_bands_df['Band ID'] == band_id].index[0]

    # Get similarity scores for the band
    sim_scores = list(enumerate(cosine_sim_genre[idx]))

    # Sort the bands based on similarity scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get indices of the top 10 most similar bands (excluding itself)
    band_indices = [i[0] for i in sim_scores[1:11]]  # Get top 10 excluding the band itself
    
    # Create a DataFrame for the results including Band ID
    recommended_bands = overlap_bands_df.iloc[band_indices][['Band ID', 'Band Name']]
    return recommended_bands

# Example of fetching recommendations for Voivod
recommendations = get_recommendations(115)  # Replace 407 with the actual band ID for Voivod
print("\nRecommendations based on Similar Bands and Genres:")
print(recommendations)