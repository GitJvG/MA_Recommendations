#Retrieves id's and corresponding urls from the band scraper dump. Run that first or edit this script

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from utils import load_cookies, update_metadata
import os
from dotenv import load_dotenv
from HTML_Scraper import fetch, parse_table, extract_href, extract_text

load_dotenv()
Master_Data = os.getenv('BANDPAR')
output_file = os.getenv('BANDIS')
data = pd.read_csv(Master_Data)
processed = pd.read_csv(output_file)
all_band_ids = data['Band ID'].tolist()
processed = processed['Band ID'].tolist()


cookies = load_cookies("Cookies.json")

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }

BASEURL = 'https://www.metal-archives.com/band/discography/id/'
ENDURL = '/tab/all'
ID = '75'
FULLURL = BASEURL + ID + ENDURL

html = fetch(FULLURL, 5, 0.05, cookies=cookies, headers=headers)

def parse_html(html, band_id):
    """Parses album data from the provided HTML, including the band ID."""
    column_extractors = [
        {'key': 'Album Name', 'extractor': extract_text},
        {'key': 'Type', 'extractor': extract_text},
        {'key': 'Year', 'extractor': extract_text},
        {'key': 'Reviews', 'extractor': extract_text},
    ]
    albums = parse_table(html, table_class='display discog', row_selector='tr', column_extractors=column_extractors)
    
    # Add the band ID to each album entry
    for album in albums:
        album['Band ID'] = band_id
        
    return albums

def save_progress(data, output_file):
    df = pd.DataFrame(data)
    try:
        if pd.read_csv(output_file).empty:
            df.to_csv(output_file, mode='a', header=True, index=False)
        else:
            df.to_csv(output_file, mode='a', header=False, index=False)
    except FileNotFoundError:
        df.to_csv(output_file, mode='a', header=True, index=False)
    print(f"Progress saved to {output_file}")

def main():
    """Main function to process all band IDs."""
    processed_set = set(processed)
    band_ids_to_process = [band_id for band_id in all_band_ids if band_id not in processed_set]
    print(f"Total bands to process: {len(band_ids_to_process)}")

    all_album_data = []
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
        future_to_band_id = {
            executor.submit(fetch, f"{BASEURL}{band_id}{ENDURL}", 5, 0.05, cookies=cookies, headers=headers): band_id
            for band_id in band_ids_to_process
        }

        for future in as_completed(future_to_band_id):
            band_id = future_to_band_id[future]
            try:
                html_content = future.result()  # Get the fetched HTML content
                if html_content:
                    album_data = parse_html(html_content, band_id)  # Parse the HTML for album data
                    if album_data:
                        all_album_data.extend(album_data)
                        update_processed_count()
                        if processed_count % batch_size == 0:
                            save_progress(all_album_data, output_file)
                            all_album_data.clear()
            except Exception as e:
                print(f"Error processing band ID {band_id}: {e}")

    # Save any remaining data after processing
    if all_album_data:
        save_progress(all_album_data, output_file)
    
    update_metadata(os.path.basename(output_file))
    print("Metadata updated.")

if __name__ == "__main__":
    main()

