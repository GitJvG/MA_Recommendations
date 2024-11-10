import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from datetime import datetime
from Env import Env

env = Env.get_instance()

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

def Parallel_processing(items_to_process, batch_size, output_files, function, **kwargs):
    """Wrapping function for multithreading, supports functions that have multiple dataframe outputs as long as multiple output_files are provided in order of returned dataframes."""
    # Ensure `output_files` is a list, even if only one file is passed
    if not isinstance(output_files, list):
        output_files = [output_files]
    
    # Initialize a list of lists, each one to collect data for an output file
    all_data = [[] for _ in output_files]
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
                result = future.result()  # Get result(s) from the function
                
                update_processed_count()
                
                # If function returns a single DataFrame, wrap it in a tuple for consistency
                if isinstance(result, pd.DataFrame):
                    result = (result,)
                
                # Append each result DataFrame to the corresponding list in all_data
                for i, df in enumerate(result):
                    if not df.empty:
                        all_data[i].append(df)

                # Intermediate saving for each batch
                if processed_count % batch_size == 0:
                    for i, data_list in enumerate(all_data):
                        if data_list:
                            save_progress(pd.concat(data_list, ignore_index=True), output_files[i])
                            data_list.clear()  # Clear data after saving
            except Exception as e:
                print(f"Error processing band ID {band_id}: {e}")

    # Final save for any remaining data
    for i, data_list in enumerate(all_data):
        if data_list:
            save_progress(pd.concat(data_list, ignore_index=True), output_files[i])

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

def list_to_delete(target_path):
    all_band_ids = set(pd.read_csv(env.band)['Band ID'])
    existing_set = set(pd.read_csv(target_path)['Band ID'])

    band_ids_to_delete = list(existing_set-all_band_ids)
    return band_ids_to_delete

def remove_dupes_and_deletions(file_path):
    """Removes duplicates from the CSV file based on unique columns defined in the file_paths dictionary, keeping last."""
    filename = os.path.basename(file_path)
    
    if filename not in file_paths:
        print(f"No unique columns defined for {filename}. Skipping.")
        return

    df = pd.read_csv(file_path)
    
    unique_columns = file_paths[filename]
    df_updated = df.drop_duplicates(subset=unique_columns, keep='last')

    ids_to_delete = list_to_delete(file_path)
    df_updated = df_updated[~df_updated['Band ID'].isin(ids_to_delete)]
    df_updated.to_csv(file_path, mode='w', header=True, index=False)
    
    print(f"Duplicates removed and progress saved for {filename}.")

def Main_based_scrape(target_path):
    """Scrapes all ids existing in the main MA_bands, not in the target file"""
    all_band_ids = set(pd.read_csv(env.band)['Band ID'])
    processed_set = set(pd.read_csv(target_path)['Band ID'])

    band_ids_to_process = list(all_band_ids - processed_set)

    return band_ids_to_process