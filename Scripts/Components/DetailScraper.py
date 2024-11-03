# Incrementally updates MA_Bands & MA_Lyrics
import pandas as pd
import os
from dotenv import load_dotenv
from Scripts.Components.HTML_Scraper import fetch
from Scripts.utils import load_config, Parallel_processing
from bs4 import BeautifulSoup

load_dotenv(".env", override=True)

BANDSFILE = os.getenv('BANDPAR')
DETAILS = 'Datasets/MA_Details.csv'
data = pd.read_csv(BANDSFILE)
all_band_ids = data['Band ID'].tolist()
processed = pd.read_csv(DETAILS)[['Band ID']] if os.path.exists(DETAILS) else pd.DataFrame()
processed = processed['Band ID'].tolist() if not processed.empty else []
TEMPDF = pd.read_csv(os.getenv('TEMPID'))

# Constants
COOKIES = load_config('Cookies')
HEADERS = load_config('Headers')

def get_band_data(band_id, **kwargs):
    delay_between_requests = kwargs.get('delay_between_requests', 0.1)
    band_url = f'https://www.metal-archives.com/bands/id/{band_id}'
    
    try:
        html_content = fetch(band_url, cookies=COOKIES, headers=HEADERS, delay_between_requests=delay_between_requests)
        
        if html_content is None:
            return None  # Return early if fetching failed
        
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find the band stats section
        band_stats = soup.find('div', id='band_stats')
        results = {}
        
        # Loop through all dt elements to collect data
        for dt in band_stats.find_all('dt'):
            key = dt.text.strip().replace(':', '')
            value = dt.find_next('dd').text.strip()  # Get the corresponding dd text
            
            # Clean up the value further
            value = ' '.join(value.split())  # Replace multiple spaces/newlines with a single space
            results[key] = value  # Store the result in the dictionary
        
        # Add the band ID to the results dictionary
        results['Band ID'] = band_id
        
        # Create DataFrame after collecting all data
        df = pd.DataFrame([results])
        return df

    except Exception as e:
        print(f"Error fetching band data for {band_url}: {e}")
        return None

def main():
    processed_set = set(processed)
    band_ids_to_process = [band_id for band_id in all_band_ids if band_id not in processed_set]
    Parallel_processing(band_ids_to_process, 500, DETAILS, get_band_data, delay_between_requests=0.05)

def refresh():
    """Refreshes the data using band IDs from the temporary file."""
    temp_data = pd.read_csv(TEMPDF)
    band_ids_to_process = temp_data['Band ID'].tolist()

    print(f"Total bands to refresh: {len(band_ids_to_process)}")
    Parallel_processing(band_ids_to_process, 500, DETAILS, get_band_data, delay_between_requests=0.05)

if __name__ == "__main__":
    main()



