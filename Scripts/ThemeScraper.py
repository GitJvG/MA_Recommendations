import pandas as pd
import os
from dotenv import load_dotenv
from HTML_Scraper import get_dt
from utils import update_metadata, load_config, process_band_ids

# Load environment variables and setup cookies/headers
load_dotenv()
cookies = load_config('Cookies')
headers = load_config('Headers')
Master_Data = os.getenv('BANDPAR')
output_file = os.getenv('BANLYR')
data = pd.read_csv(Master_Data)
processed = pd.read_csv(output_file) if os.path.exists(output_file) else pd.DataFrame()
all_band_ids = data['Band ID'].tolist()
processed_ids = processed['Band ID'].tolist() if not processed.empty else []
TEMPFILE = os.getenv('TEMPID')
TEMPDF = pd.read_csv(TEMPFILE)

def scrape_band_data(band_id, **kwargs):
    delay_between_requests = kwargs.get('delay_between_requests', 0.1)
    band_url = f'https://www.metal-archives.com/bands/id/{band_id}'
    band_data = get_dt(band_url, strings=["Themes:"], headers=headers, cookies=cookies, delay_between_requests=delay_between_requests)  
    if band_data:
        band_data['Band ID'] = band_id
        return pd.DataFrame([band_data])[['Themes:','Band ID']]
    return pd.DataFrame(columns=['Themes:','Band ID'])

"""Included for completeness. It's advised to use BandUpdtr instead if you want to update MA_Bands and MA_Themes. BandUpdtr combines these as the status data is on the same page"""
def refresh(): 
    band_ids_to_process = [band_id for band_id in TEMPDF['Band ID'].tolist()]
    process_band_ids(band_ids_to_process, 200, output_file, scrape_band_data, delay_between_requests=0.05)
    print("Scraping completed.")
    update_metadata(os.path.basename(output_file))

def main():
    """Main function to process all band IDs."""
    processed_set = set(processed_ids)
    band_ids_to_process = [band_id for band_id in all_band_ids if band_id not in processed_set]
    process_band_ids(band_ids_to_process, 200, output_file, scrape_band_data, delay_between_requests=0.05)
    print("Scraping completed.")
    update_metadata(os.path.basename(output_file))

if __name__ == "__main__":
    main()
