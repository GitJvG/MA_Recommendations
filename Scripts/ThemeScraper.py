from concurrent.futures import ThreadPoolExecutor, as_completed
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

# Load band data
data = pd.read_csv(Master_Data)
processed = pd.read_csv(output_file) if os.path.exists(output_file) else pd.DataFrame()
all_band_ids = data['Band ID'].tolist()
processed_ids = processed['Band ID'].tolist() if not processed.empty else []

def save_progress(data, output_file):
    """Saves the progress of the scraping to a CSV file."""
    df = pd.DataFrame(data)
    try:
        if df.empty:
            print("No data to save.")
            return
        
        if os.path.exists(output_file) and not processed.empty:
            df.to_csv(output_file, mode='a', header=False, index=False)
        else:
            df.to_csv(output_file, mode='a', header=True, index=False)
        print(f"Progress saved to {output_file}")
    except Exception as e:
        print(f"Error saving progress: {e}")

def scrape_band_data(band_id, delay_between_requests=0.05):
    band_url = f'https://www.metal-archives.com/bands/id/{band_id}'
    band_data = get_dt(band_url, strings=["Themes:"], headers=headers, cookies=cookies, delay_between_requests=delay_between_requests)  
    if band_data:
        band_data['Band ID'] = band_id
        return band_data
    return None

def main():
    """Main function to process all band IDs."""
    processed_set = set(processed_ids)
    band_ids_to_process = [band_id for band_id in all_band_ids if band_id not in processed_set]
    print(f"Total bands to process: {len(band_ids_to_process)}")

    all_band_data = []
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
        future_to_band_id = {executor.submit(scrape_band_data, band_id, delay_between_requests=0.05): band_id for band_id in band_ids_to_process}

        for future in as_completed(future_to_band_id):
            band_id = future_to_band_id[future]
            try:
                band_data = future.result()
                if band_data:
                    all_band_data.append(band_data)  # Append band data correctly
                    update_processed_count()
                    if processed_count % batch_size == 0:
                        save_progress(all_band_data, output_file)
                        all_band_data.clear()  # Clear data after saving
            except Exception as e:
                print(f"Error processing band ID {band_id}: {e}")

    # Save any remaining data after processing
    if all_band_data:
        save_progress(all_band_data, output_file)
    
    update_metadata(os.path.basename(output_file))
    print("Metadata updated.")
    
    print("Scraping completed.")

if __name__ == "__main__":
    main()
