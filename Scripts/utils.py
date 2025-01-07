import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from datetime import datetime
import pytz
from Env import Env
import requests
import time

env = Env.get_instance()

def fetch(url, retries=env.retries, delay_between_requests=env.delay, headers=env.head, type='text', params=None):
    session = requests.Session()
    session.headers.update(headers)
    session.cookies.update(env.cook)
    
    for attempt in range(retries):
        try:
            response = session.get(url, params=params)
            time.sleep(delay_between_requests)

            if response.status_code == 200:
                if type == 'text':
                    return response.text
                elif type == 'json':
                    return response.json()
            else:

                print(f"Retrying {url} due to status code {response.status_code}. Attempt {attempt + 1}")
                sleep_time = 2.5 ** attempt
                time.sleep(sleep_time)
        except requests.RequestException as e:

            print(f"Request failed for {url}: {e}. Attempt {attempt + 1}")
            time.sleep(2 ** attempt)
    
    print(f"Failed to retrieve {url}.")
    return None

def get_last_scraped_date(file_path, filename):
    try:
        df = pd.read_csv(file_path)
        file_info = df[df['name'] == filename]
        if not file_info.empty:
            date_str = file_info.iloc[0]['date']
            return datetime.strptime(date_str, '%Y-%m-%d')
    except Exception as e:
        print(f"Error: {e}")
    return None

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

def Parallel_processing(items_to_process, batch_size, output_files, function, **kwargs):
    """Wrapping function for multithreading, supports functions that have multiple dataframe outputs as long as multiple output_files are provided in order of returned dataframes."""
    # Ensure `output_files` is a list, even if only one file is passed
    if not isinstance(output_files, list):
        output_files = [output_files]
    
    # Initialize a list of lists, each one to collect data for an output file
    all_data = [[] for _ in output_files]
    to_be_processed_count = len(items_to_process)
    processed_count = 0
    lock = Lock()

    def update_processed_count():
        nonlocal processed_count
        with lock:
            processed_count += 1
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_items = {executor.submit(function, items, **kwargs): items for items in items_to_process}

        for future in as_completed(future_to_items):
            itemid = future_to_items[future]
            try:
                result = future.result()  # Get result(s) from the function
                
                # If function returns a single DataFrame, wrap it in a tuple for consistency
                if isinstance(result, pd.DataFrame):
                    result = (result,)
                
                # Append each result DataFrame to the corresponding list in all_data
                for i, df in enumerate(result):
                    if not df.empty:
                        all_data[i].append(df)

                if batch_size:
                    update_processed_count()
                    if processed_count % batch_size == 0:
                        print(f"Processed {processed_count}/{to_be_processed_count} items.")
                        for i, data_list in enumerate(all_data):
                            if data_list:
                                save_progress(pd.concat(data_list, ignore_index=True), output_files[i])
                                data_list.clear()  # Clear data after saving
            except Exception as e:
                print(f"Error processing item {itemid}: {e}")

    # Final save for any remaining data
    for i, data_list in enumerate(all_data):
        if data_list:
            save_progress(pd.concat(data_list, ignore_index=True), output_files[i])

def update_metadata(file_path=None, time=None):
    try:
        metadata_df = pd.read_csv(env.meta)
    except FileNotFoundError:
        metadata_df = pd.DataFrame()

    # Clears the time value for new entries this is intended behavior, This way there's never a false combination. The time will be set for all entries at once at the end.
    # The time is set for when MA_Bands starts evaluating. All other files have ids that don't exist in that file removed to prevent primary/foreign key conflicts.
    
    if file_path:
        data_filename = os.path.basename(file_path)
        new_entry = pd.DataFrame([{
            'name': data_filename,
            'date': pd.Timestamp.now().strftime('%Y-%m-%d')
        }])
        
        metadata_df = metadata_df[metadata_df['name'] != data_filename]
        metadata_df = pd.concat([metadata_df, new_entry], ignore_index=True)
            
    if time:
        if not metadata_df.empty:
            metadata_df['time'] = time
        else:
            print('failed to add time, file does not exist or is empty')

    metadata_df.to_csv(env.meta, index=False)

    print('Metadata updated!')
    return metadata_df

def list_to_delete(target_path):
    all_band_ids = set(pd.read_csv(env.band)['band_id'])
    existing_set = set(pd.read_csv(target_path)['band_id'])

    band_ids_to_delete = list(existing_set-all_band_ids)
    return band_ids_to_delete

def unique_columns(path):
    attribute_name = next(key for key, value in vars(env).items() if value == path)
    unique_columns = getattr(env, f"{attribute_name}_key")
    return unique_columns

def remove_dupes_and_deletions(file_path):
    """Removes duplicates from the CSV file based on unique columns defined in the file_paths dictionary, keeping last."""
    filename = os.path.basename(file_path)
    unique_cols = unique_columns(file_path)

    df = pd.read_csv(file_path)
    df_updated = df.drop_duplicates(subset=unique_cols, keep='last')
    if file_path != env.meta:
        ids_to_delete = list_to_delete(file_path)
        if file_path == env.simi:
            df_updated = df_updated[~df_updated['band_id'].isin(ids_to_delete) & ~df_updated['similar_id'].isin(ids_to_delete)]
        else:
            df_updated = df_updated[~df_updated['band_id'].isin(ids_to_delete)]
        df_updated.to_csv(file_path, mode='w', header=True, index=False)
    
    print(f"Duplicates removed and progress saved for {filename}.")

def Main_based_scrape(target_path):
    """Scrapes all ids existing in the main MA_bands, not in the target file"""
    all_band_ids = set(pd.read_csv(env.band)['band_id'])
    if not os.path.exists(target_path):
        band_ids_to_process = all_band_ids
    else:
        processed_set = set(pd.read_csv(target_path)['band_id'])
        band_ids_to_process = list(all_band_ids - processed_set)

    return band_ids_to_process

def get_time():
    est = pytz.timezone('US/Eastern')
    utc_now = datetime.now(pytz.utc)
    time = utc_now.astimezone(est)
    time = time.strftime("%H:%M")

    return time

def get_common_date():
    metadata = pd.read_csv(env.meta)
    filtered_metadata = metadata[metadata['name'] != 'MA_Bands.csv']
    unique_dates = filtered_metadata['date'].dropna().unique()
    
    if len(unique_dates) == 1:
        return env.simi
    else:
        return None