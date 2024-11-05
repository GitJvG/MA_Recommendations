# Incrementally updates MA_Bands & MA_Lyrics
import pandas as pd
import os
from dotenv import load_dotenv
from Scripts.Components.HTML_Scraper import fetch
from Scripts.utils import Parallel_processing, Env, Main_based_scrape
from bs4 import BeautifulSoup
from Scripts.Components.ModifiedUpdater import Modified_based_scrape

load_dotenv(".env", override=True)
env = Env.get_instance()

data = pd.read_csv(env.band)
all_band_ids = data['Band ID'].tolist()
processed = pd.read_csv(env.deta)[['Band ID']] if os.path.exists(env.deta) else pd.DataFrame()
processed = processed['Band ID'].tolist() if not processed.empty else []

def get_band_data(band_id, **kwargs):
    delay_between_requests = kwargs.get('delay_between_requests', 0.1)
    band_url = f'https://www.metal-archives.com/bands/id/{band_id}'
    
    try:
        html_content = fetch(band_url, cookies=env.cook, headers=env.head, delay_between_requests=delay_between_requests)
        
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
    band_ids_to_process = Main_based_scrape(env.deta)
    Parallel_processing(band_ids_to_process, 500, env.deta, get_band_data, delay_between_requests=0.05)

def refresh():
    # Complete = true because all band ids in main should at least have a profile
    Modified_based_scrape(env.deta, get_band_data, complete=True)

if __name__ == "__main__":
    print(get_band_data(70))


