import pandas as pd
import os
import json
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

load_dotenv()
CONFIG = os.getenv('CONFIG')
metadata_path = os.getenv('METADATA')

def load_config(attribute):
    """Attribute as Cookies or Headers"""
    with open('config.json', 'r') as file:
        config = json.load(file)
        
    return config.get(attribute)

def replace_records(old_records, new_records, column):
    filtered_old_records = old_records[~old_records[column].isin(new_records[column])]
    updated_records = pd.concat([filtered_old_records, new_records], ignore_index=True)
    
    return updated_records
    
def save_progress(new_data, output_file):
    df_new = pd.DataFrame(new_data)
    
    try:
        df_existing = pd.read_csv(output_file)
        df_updated = replace_records(df_existing, df_new, 'Band ID')
        df_updated.to_csv(output_file, mode='w', header=True, index=False)
    
    except FileNotFoundError:
        df_new.to_csv(output_file, mode='w', header=True, index=False)

    print(f"Progress saved to {output_file}")


def process_band_ids(band_ids_to_process, batch_size, output_file, function, **kwargs):
    all_band_data = []  # This will now hold DataFrames
    processed_count = 0
    lock = Lock()

    def update_processed_count():
        nonlocal processed_count
        with lock:
            processed_count += 1
            print(f"Processed {processed_count} band IDs.")
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_band_id = {executor.submit(function, band_id, **kwargs): band_id for band_id in band_ids_to_process}

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
        save_progress(pd.concat(all_band_data, ignore_index=True), output_file)  # Final save

def update_metadata(data_filename):
    new_entry = pd.DataFrame([{
        'Filename': data_filename,
        'Date': pd.Timestamp.now().strftime('%Y-%m-%d')
    }])

    try:
        metadata_df = pd.read_csv(metadata_path)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        metadata_df = pd.DataFrame(columns=['Filename', 'Date'])

    # Remove any existing entry with the same Filename
    metadata_df = replace_records(metadata_df, new_entry, 'Filename')
    metadata_df.to_csv(metadata_path, index=False)

    return metadata_df

import pandas as pd
import os

def check_and_remove_duplicates(file_path, unique_columns):
    df = pd.read_csv(file_path)

    # Check for duplicates
    initial_count = len(df)
    df_deduplicated = df.drop_duplicates(subset=unique_columns, keep='last')
    final_count = len(df_deduplicated)

    # Save the updated DataFrame back to the CSV
    df_deduplicated.to_csv(file_path, index=False)

    print(f"Processed {file_path}: {initial_count - final_count} duplicates removed.")

def distinct(file_paths):
    """Check and remove duplicates for the specified CSV files and their unique columns."""
    for file_name, unique_columns in file_paths.items():
        if os.path.exists(file_name):
            check_and_remove_duplicates(file_name, unique_columns)
        else:
            print(f"File {file_name} does not exist.")
