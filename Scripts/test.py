import requests
from bs4 import BeautifulSoup
from threading import Lock
import pandas as pd
import os
from dotenv import load_dotenv
from HTML_Scraper import get_dt
from utils import update_metadata

# Load environment variables and setup cookies/headers
load_dotenv()
cookies = {
    'cookie_name': 'cookie_value'  # Replace with actual cookies loaded from "Cookies.json"
}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

# Environment variables for input/output files
Master_Data = os.getenv('BANDPAR')
output_file = os.getenv('BANLYR')

# Load band data (assuming this is necessary for other processing)
data = pd.read_csv(Master_Data)
all_band_ids = data['Band ID'].tolist()

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

def scrape_band_data(band_id, delay_between_requests=0.05):
    band_url = f'https://www.metal-archives.com/bands/id/{band_id}'
    print(f"Fetching data for band ID: {band_id}")
    band_data = get_dt(band_url, strings=["Themes:"], headers=headers, cookies=cookies, delay_between_requests=delay_between_requests)  
    if band_data:
        band_data['Band ID'] = band_id
        print(f"Data fetched for band ID {band_id}: {band_data}")
        return band_data
    print(f"No data found for band ID {band_id}")
    return None

def main():
    """Main function to process band ID 75."""
    band_id = 75  # Hardcoded band ID for testing
    print(f"Total bands to process: 1 (only band ID {band_id})")

    all_band_data = []
    lock = Lock()

    band_data = scrape_band_data(band_id, delay_between_requests=0.05)
    if band_data:
        all_band_data.append(band_data)
        save_progress(all_band_data, output_file)

    update_metadata(os.path.basename(output_file))
    print("Metadata updated.")
    
    print("Scraping completed.")

if __name__ == "__main__":
    main()
