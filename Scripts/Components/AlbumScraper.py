#Retrieves id's and corresponding urls from the band scraper dump. Run that first or edit this script

import pandas as pd
from Scripts.utils import load_config, Parallel_processing
import os
from dotenv import load_dotenv
from Scripts.Components.HTML_Scraper import fetch, parse_table, extract_text

load_dotenv()
BANDSFILE = os.getenv('BANDPAR')
DISCOGFILE = os.getenv('BANDIS')
data = pd.read_csv(BANDSFILE)
processed = pd.read_csv(DISCOGFILE)
processed = processed['Band ID'].tolist()
all_band_ids = data['Band ID'].tolist()
cookies = load_config('Cookies')
headers = load_config('Headers')
temp_file = os.getenv('TEMPID')

BASEURL = 'https://www.metal-archives.com/band/discography/id/'
ENDURL = '/tab/all'

def parse_html(html, band_id):
    """Parses album data from the provided HTML, including the band ID."""
    column_extractors = [
        (0, extract_text),  # (Album Name)
        (1, extract_text),  # (Type)
        (2, extract_text),  # (Year)
        (3, extract_text),  # (Reviews)
    ]
    albums = parse_table(html, table_class='display discog', row_selector='tr', column_extractors=column_extractors)

    # Convert to DataFrame and add Band ID
    df_albums = pd.DataFrame(albums)
    df_albums['Band ID'] = band_id
    return df_albums

def fetch_album_data(band_id, **kwargs):
    """Fetches album data for a given band ID and returns it as a DataFrame."""
    delay_between_requests = kwargs.get('delay_between_requests', 0.1)
    cookies = kwargs.get('cookies', None)
    headers = kwargs.get('headers', None)
    url = f"{BASEURL}{band_id}{ENDURL}"
    html_content = fetch(url, retries=5, delay_between_requests=delay_between_requests, cookies=cookies, headers=headers)

    if html_content:
        return parse_html(html_content, band_id)[['Album Name', 'Type', 'Year', 'Reviews', 'Band ID']]
    return pd.DataFrame(columns=['Album Name', 'Type', 'Year', 'Reviews', 'Band ID'])

def refresh():
    """Refreshes the data using band IDs from the temporary file."""
    temp_data = pd.read_csv(temp_file)
    band_ids_to_process = temp_data['Band ID'].tolist()

    print(f"Total bands to refresh: {len(band_ids_to_process)}")
    Parallel_processing(band_ids_to_process, 200, DISCOGFILE, fetch_album_data, delay_between_requests=0.05, cookies=cookies, headers=headers)

def main():
    """Main function to process all band IDs."""
    processed_set = set(processed)
    band_ids_to_process = [band_id for band_id in all_band_ids if band_id not in processed_set]
    Parallel_processing(band_ids_to_process, 200, DISCOGFILE, fetch_album_data, delay_between_requests=0.05, cookies=cookies, headers=headers)


if __name__ == "__main__":
    main()

