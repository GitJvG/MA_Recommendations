import pandas as pd
import os
import json
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from datetime import datetime

load_dotenv()

def load_config(attribute):
    """Attribute as Cookies or Headers"""
    with open('config.json', 'r') as file:
        config = json.load(file)
        
    return config.get(attribute)

def get_last_scraped_date(file_path, filename):
    try:
        df = pd.read_csv(file_path)
        file_info = df[df['Filename'] == filename]
        if not file_info.empty:
            date_str = file_info.iloc[0]['Date']
            return datetime.strptime(date_str, '%Y-%m-%d')
    except Exception as e:
        print(f"Error: {e}")
    return None

class Env:
    _instance = None
    
    @staticmethod
    def get_instance():
        if Env._instance is None:
            Env._instance = Env()
        return Env._instance

    def __init__(self):
        if Env._instance is not None:
            raise Exception("This is a singleton!")
        self.cook = load_config('Cookies')
        self.head = load_config('Headers')
        self.meta = os.getenv('METADATA')
        self.simi = os.getenv('SIMBAN')
        self.disc = os.getenv('BANDIS')
        self.band = os.getenv('BANDPAR')
        self.deta = os.getenv('DETAIL')
        self.memb = os.getenv('MEMBER')
        self.url_modi= os.getenv('URLMODIFIED')
        self.url_band= os.getenv('URLBANDS')
        self.retries = load_config('Retries')
        self.delay = load_config('Delay')

env = Env.get_instance()
  
file_paths = {
    'MA_Bands.csv': ['Band ID'],
    'MA_Similar.csv': ['Band ID', 'Similar Artist ID'],
    'MA_Discog.csv': ['Album Name', 'Type', 'Year', 'Band ID'],
    'MA_Details.csv': ['Band ID'],
    'MA_Member.csv':['Band ID', 'Member ID'],
    'metadata.csv': ['Filename']
}

def extract_url_id(url):
    return url.split('/')[-1]

def save_progress(new_data, output_file):
    df_new = pd.DataFrame(new_data)

    if os.path.exists(output_file):
        df_new.to_csv(output_file, mode='a', header=False, index=False)
    else:
        # If the file doesn't exist, create it and write the new data
        df_new.to_csv(output_file, mode='w', header=True, index=False)

    print(f"Progress saved to {output_file}")

def Parallel_processing(items_to_process, batch_size, output_file, function, **kwargs):
    print(f"Total bands to process: {len(items_to_process)}")
    all_band_data = []  # This will now hold DataFrames
    processed_count = 0
    lock = Lock()

    def update_processed_count():
        nonlocal processed_count
        with lock:
            processed_count += 1
            print(f"Processed {processed_count} items.")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_band_id = {executor.submit(function, band_id, **kwargs): band_id for band_id in items_to_process}

        for future in as_completed(future_to_band_id):
            band_id = future_to_band_id[future]
            try:
                band_data = future.result()
                update_processed_count()
                if not band_data.empty:  # Check if the DataFrame is not empty
                    all_band_data.append(band_data)  # Append DataFrame

                if processed_count % batch_size == 0:
                    save_progress(pd.concat(all_band_data, ignore_index=True), output_file)  # Concatenate and save
                    all_band_data.clear()  # Clear data after saving
            except Exception as e:
                print(f"Error processing band ID {band_id}: {e}")

    if all_band_data:
        save_progress(pd.concat(all_band_data, ignore_index=True), output_file)

def update_metadata(data_filename):
    new_entry = pd.DataFrame([{
        'Filename': data_filename,
        'Date': pd.Timestamp.now().strftime('%Y-%m-%d')
    }])
    
    try:
        metadata_df = pd.read_csv(env.meta)
        
        # Drop any rows where 'Filename' matches data_filename to avoid duplicates
        metadata_df = metadata_df[metadata_df['Filename'] != data_filename]
        metadata_df = pd.concat([metadata_df, new_entry], ignore_index=True)
        
    except FileNotFoundError:
        metadata_df = new_entry

    metadata_df.to_csv(env.meta, index=False)

    print('Metadata updated!')
    return metadata_df

def remove_duplicates(file_path):
    """Removes duplicates from the CSV file based on unique columns defined in the file_paths dictionary, keeping last."""
    filename = os.path.basename(file_path)
    
    if filename not in file_paths:
        print(f"No unique columns defined for {filename}. Skipping.")
        return

    df = pd.read_csv(file_path)
    unique_columns = file_paths[filename]
    df_updated = df.drop_duplicates(subset=unique_columns, keep='last')
    df_updated.to_csv(file_path, mode='w', header=True, index=False)
    
    print(f"Duplicates removed and progress saved for {filename}.")

def Main_based_scrape(target_path):
    """Scrapes all ids existing in the main MA_bands, not in the target file"""
    env = Env.get_instance()
    all_band_ids = set(pd.read_csv(env.band)['Band ID'])
    processed_set = set(pd.read_csv(target_path)['Band ID'])

    band_ids_to_process = list(all_band_ids - processed_set)
    band_ids_to_delete = list(processed_set-all_band_ids)

    target_df = pd.read_csv(target_path)
    updated_df = target_df[~target_df['Band ID'].isin(band_ids_to_delete)]
    updated_df.to_csv(target_path, index=False)

    return band_ids_to_process