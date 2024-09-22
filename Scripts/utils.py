import pandas as pd
import os
import json
from dotenv import load_dotenv
load_dotenv()

def update_metadata(data_filename):
    metadata_path = os.getenv('METADATA')
    new_entry = pd.DataFrame([{
        'Filename': data_filename,
        'Date': pd.Timestamp.now().strftime('%Y-%m-%d')
    }])

    #Read or create metadata file
    try:
        metadata_df = pd.read_csv(metadata_path)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        metadata_df = pd.DataFrame(columns=['Filename', 'Date'])

    # Remove any existing entry with the same Filename
    metadata_df = metadata_df[metadata_df['Filename'] != data_filename]
    metadata_df = pd.concat([metadata_df, new_entry], ignore_index=True)
    metadata_df.to_csv(metadata_path, index=False)

    return metadata_df

def load_cookies(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)