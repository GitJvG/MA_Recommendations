import pandas as pd
from Scripts.utils import load_config, Parallel_processing
import os
from dotenv import load_dotenv
from Scripts.Components.HTML_Scraper import fetch, extract_href, extract_text, parse_table  # Import your fetch function

# Load environment variables
load_dotenv(".env", override=True)
BANDSFILE = os.getenv('BANDPAR')
SIMILARFILE = os.getenv('SIMBAN')
TEMPFILE = os.getenv('TEMPID')

# Load band data
data = pd.read_csv(BANDSFILE)
processed = pd.read_csv(SIMILARFILE)
processed = processed['Band ID'].tolist()
all_band_ids = data['Band ID'].tolist()
TEMPDF = pd.read_csv(TEMPFILE)

# Load cookies
COOKIES = load_config('Cookies')
HEADERS = load_config('Headers')

def parse_similar_artists(html, band_id):
    """Parses similar artists from the provided HTML."""
    column_extractors = [
        (0, extract_href),  # First column Similar Artist ID
        (3, extract_text),  # Fourth column (Score)
    ]
    results = parse_table(html, table_id='artist_list', row_selector='tr', column_extractors=column_extractors)
    for result in results:
        if result[0]:  # Accessing the first column which is 'Similar Artist ID'
            result[0] = result[0].split('/')[-1]  # Extracting the ID from the URL
        result['Band ID'] = band_id

    return results

def scrape_band_data(band_id, **kwargs):
    delay_between_requests = kwargs.get('delay_between_requests', 0.1)
    # Define the URL
    url = f'https://www.metal-archives.com/band/ajax-recommendations/id/{band_id}'
    html_content = fetch(url, retries=5, delay_between_requests=delay_between_requests, cookies=COOKIES, headers=HEADERS)

    if html_content:
        if "No similar artist has been recommended yet" in html_content:
            return pd.DataFrame(columns=['Similar Artist ID', 'Score', 'Band ID'])  # Return an empty DataFrame with the correct columns
        similar_artists = parse_similar_artists(html_content, band_id)
        df = pd.DataFrame(similar_artists)[['Similar Artist ID', 'Score', 'Band ID']]
        return df
    return pd.DataFrame(columns=['Similar Artist ID', 'Score', 'Band ID'])

def refresh():
    band_ids_to_process = [band_id for band_id in TEMPDF['Band ID'].tolist()]
    Parallel_processing(band_ids_to_process, 200, SIMILARFILE, scrape_band_data, delay_between_requests=0.05)
    
def main():
    """Main function to process all band IDs."""
    processed_set = set(processed)
    band_ids_to_process = [band_id for band_id in all_band_ids if band_id not in processed_set]
    Parallel_processing(band_ids_to_process, 200, SIMILARFILE, scrape_band_data, delay_between_requests=0.05)

if __name__ == "__main__":
    main()