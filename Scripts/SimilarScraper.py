import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from utils import load_cookies, update_metadata
import os
from dotenv import load_dotenv
from HTML_Scraper import fetch, extract_href, extract_text, parse_table  # Import your fetch function

# Load environment variables
load_dotenv()
Master_Data = os.getenv('BANDPAR')
output_file = os.getenv('SIMBAN')

# Load band data
data = pd.read_csv(Master_Data)
processed = pd.read_csv(output_file)
all_band_ids = data['Band ID'].tolist()
processed = processed['Band ID'].tolist()

# Load cookies
cookies = load_cookies("Cookies.json")

def parse_similar_artists(html, band_id):
    """Parses similar artists from the provided HTML."""
    column_extractors = [
        {'key': 'Artist URL', 'extractor': extract_href},  # Extract the href attribute for the artist URL
        {'key': 'Band ID', 'extractor': lambda _: band_id},  # Add the band ID directly
        {'key': 'Similar Artist ID', 'extractor': extract_href},  # Extract artist ID from URL
        {'key': 'Score', 'extractor': extract_text},  # Extract the score as text
    ]
    results = parse_table(html, table_id='artist_list', row_selector='tr', column_extractors=column_extractors)
    for result in results:
        artist_url = result.get('Artist URL')
        if artist_url:
            result['Similar Artist ID'] = artist_url.split('/')[-1]

    return results

def save_progress(data, output_file):
    """Saves the progress of the scraping to a CSV file."""
    df = pd.DataFrame(data)
    try:
        if pd.read_csv(output_file).empty:
            df.to_csv(output_file, mode='a', header=True, index=False)
        else:
            df.to_csv(output_file, mode='a', header=False, index=False)
    except FileNotFoundError:
        df.to_csv(output_file, mode='a', header=True, index=False)
    print(f"Progress saved to {output_file}")

def process_band_id(band_id, delay_between_requests=0.1):
    """Processes a single band ID to fetch and parse similar artists."""
    # Define the URL
    url = f'https://www.metal-archives.com/band/ajax-recommendations/id/{band_id}'
    html_content = fetch(url, retries=5, delay_between_requests=delay_between_requests, cookies=cookies)

    if html_content:
        similar_artists = parse_similar_artists(html_content, band_id)
        return similar_artists
    return []

def main():
    """Main function to process all band IDs."""
    processed_set = set(processed)
    band_ids_to_process = [band_id for band_id in all_band_ids if band_id not in processed_set]
    print(f"Total bands to process: {len(band_ids_to_process)}")

    all_similar_artists = []
    processed_count = 0
    batch_size = 200 

    lock = Lock()

    def update_processed_count():
        nonlocal processed_count
        with lock:
            processed_count += 1
            print(f"Processed {processed_count} band IDs.")
    
    # Use ThreadPoolExecutor to process band IDs concurrently
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_band_id = {executor.submit(process_band_id, band_id, delay_between_requests=0.15): band_id for band_id in band_ids_to_process}

        for future in as_completed(future_to_band_id):
            band_id = future_to_band_id[future]
            try:
                similar_artists = future.result()
                if similar_artists:
                    all_similar_artists.extend(similar_artists)
                    update_processed_count()
                    if processed_count % batch_size == 0:
                        save_progress(all_similar_artists, output_file)
                        all_similar_artists.clear()
            except Exception as e:
                print(f"Error processing band ID {band_id}: {e}")

    # Save any remaining data after processing
    if all_similar_artists:
        save_progress(all_similar_artists, output_file)
    
    update_metadata(os.path.basename(output_file))
    print("Metadata updated.")

if __name__ == "__main__":
    main()