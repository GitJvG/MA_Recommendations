import pandas as pd

# Load your data from CSV
similar_artists_df = pd.read_csv('Datasets/MA_Similar.csv')
similar_artists_df = pd.DataFrame(similar_artists_df, columns=['Band ID', 'Similar Artist ID', 'Score'])

# Function to filter the similar bands table based on a given band ID
def get_similar_bands(band_id):
    """Returns a filtered DataFrame containing similar bands."""
    # Filter for bands that are either similar to or list the given band as similar
    filtered_df = similar_artists_df[
        (similar_artists_df['Band ID'] == band_id) |
        (similar_artists_df['Similar Artist ID'] == band_id)
    ]
    return filtered_df

def get_complete_similar_bands(band_id):
    """Get a complete list of similar bands for a given band ID."""
    # Get bands that are directly similar to the given band
    filtered_similar_bands = get_similar_bands(band_id)
    
    # Combine scores from both perspectives
    filtered_similar_bands['IsOriginal'] = filtered_similar_bands['Band ID'] == band_id
    bands_listing_original = similar_artists_df[similar_artists_df['Similar Artist ID'] == band_id]
    bands_listing_original['IsOriginal'] = False  # Mark these as original listings

    # Concatenate and aggregate in one step
    combined_df = pd.concat([
        filtered_similar_bands[['Similar Artist ID', 'Score', 'IsOriginal']],
        bands_listing_original[['Band ID', 'Score']].rename(columns={'Band ID': 'Similar Artist ID'})
    ])

    # Aggregate scores while ensuring uniqueness and taking the maximum score
    aggregated_df = combined_df.groupby('Similar Artist ID', as_index=False).agg({'Score': 'max'})

    # Filter out the original band from the results
    return aggregated_df[aggregated_df['Similar Artist ID'] != band_id].sort_values(by='Score', ascending=False)

# Example usage
example_band_id = 19  # ID for Slayer, a popular thrash metal band
complete_similar_bands = get_complete_similar_bands(example_band_id)

# Display the resulting DataFrame
print("\nComplete Similar Bands Sorted by Score:")
print(complete_similar_bands)
