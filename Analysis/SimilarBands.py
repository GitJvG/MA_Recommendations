import pandas as pd

# Load your data from CSV
similar_artists_df = pd.read_csv('Datasets/MA_Similar.csv')
similar_artists_df = pd.DataFrame(similar_artists_df, columns=['Band ID', 'Similar Artist ID', 'Score'])

# Function to filter the similar bands table based on a given band ID
def get_similar_bands(band_id):
    """
    Returns a filtered DataFrame containing rows where the specified band ID
    is present in either the Similar Artist ID or the Band ID columns.
    
    Parameters:
    - band_id (int or str): The ID of the band to search for.
    
    Returns:
    - pd.DataFrame: Filtered DataFrame with relevant similar bands.
    """
    # Filter rows where the specified band ID is in either column
    filtered_df = similar_artists_df[
        (similar_artists_df['Band ID'] == band_id) | 
        (similar_artists_df['Similar Artist ID'] == band_id)
    ]
    return filtered_df.reset_index(drop=True)

# Function to aggregate scores and return a unique set of similar bands
def aggregate_similar_bands(filtered_df):
    """
    Aggregates the scores for similar bands to ensure unique bands
    are returned with the highest similarity score.
    
    Parameters:
    - filtered_df (pd.DataFrame): DataFrame containing similar bands.
    
    Returns:
    - pd.DataFrame: DataFrame with unique bands and their highest similarity scores.
    """
    # Group by Similar Artist ID and take the max score
    aggregated_df = filtered_df.groupby('Similar Artist ID', as_index=False).agg({
        'Score': 'max'
    })

    # Sort by Score in descending order
    aggregated_df = aggregated_df.sort_values(by='Score', ascending=False).reset_index(drop=True)
    
    return aggregated_df

# Function to get the complete list of similar bands for a given band ID
def get_complete_similar_bands(band_id):
    """
    Get a complete list of similar bands for a given band ID.
    
    Parameters:
    - band_id (int or str): The ID of the band to search for.
    
    Returns:
    - pd.DataFrame: DataFrame of complete similar bands sorted by score.
    """
    # Get bands that are directly similar to the given band
    filtered_similar_bands = get_similar_bands(band_id)
    
    # Include bands that list the original band as similar
    bands_listing_original = similar_artists_df[similar_artists_df['Similar Artist ID'] == band_id]

    # Combine the two DataFrames
    complete_bands = pd.concat([
        filtered_similar_bands[['Similar Artist ID', 'Score']],
        bands_listing_original[['Band ID', 'Score']].rename(columns={'Band ID': 'Similar Artist ID'})
    ])

    # Aggregate scores to ensure unique similar bands
    complete_aggregated = aggregate_similar_bands(complete_bands)
    #Ensures it won't show itself as a similar band.
    complete_aggregated = complete_aggregated[complete_aggregated['Similar Artist ID'] != band_id]
    return complete_aggregated

# Example usage
example_band_id = 115  # ID for Slayer, a popular thrash metal band
complete_similar_bands = get_complete_similar_bands(example_band_id)

# Display the resulting DataFrame
print("\nComplete Similar Bands Sorted by Score:")
print(complete_similar_bands)
