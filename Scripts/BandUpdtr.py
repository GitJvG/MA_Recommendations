# Incrementally updates MA_Bands
import time
import pandas as pd
import requests
from datetime import datetime
from utils import load_cookies
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
load_dotenv()
from utils import update_metadata
from HTML_Scraper import get_dt

# Constants
URL = 'https://www.metal-archives.com/archives/ajax-band-list/by/created/json/1/1/'
metadata_file = os.getenv('METADATA')
BANDSFILE = (os.getenv('BANDPAR'))
BANDS = os.path.basename(BANDSFILE)
existing_bands_df = pd.read_csv(BANDSFILE)
cookies = load_cookies('Cookies.json')
TEMPFILE = (os.getenv('TEMPID'))
LYRICS = (os.getenv('BANLYR'))

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

def extract_url_id(url):
    return url.split('/')[-1]
    
def get_scrape_day(file_path, filename):
    #Load the last scraped date for a specific file from the metadata CSV and return the day of the month.
    try:
        df = pd.read_csv(file_path)      
        # Find the row where the Filename matches the provided filename
        file_info = df[df['Filename'] == filename]
        
        if not file_info.empty:
            # Extract the date string
            date_str = file_info.iloc[0]['Date']
            date = datetime.strptime(date_str, '%Y-%m-%d')
            # Return the day of the month
            return date.day
    
    except Exception as e:
        print(f"Error: {e}")
    
    # Return a default day (e.g., 0) if not found
    return 0

def get_recently_added_page(length=550, total=550, sEcho=1):
    #Fetch all recently added bands in a single request.
    payload = {
        'sEcho': sEcho,
        'iColumns': 6,
        'sColumns': '',
        'iDisplayStart': 0,
        'iDisplayLength': length,
        'mDataProp_0': 0,
        'mDataProp_1': 1,
        'mDataProp_2': 2,
        'mDataProp_3': 3,
        'mDataProp_4': 4,
        'mDataProp_5': 5,
        'iSortCol_0': 4,
        'sSortDir_0': 'desc',
        'iSortingCols': 1,
        'bSortable_0': True,
        'bSortable_1': True,
        'bSortable_2': True,
        'bSortable_3': True,
        'bSortable_4': True,
        'bSortable_5': True,
        '_': int(time.time() * 1000)  # Use current timestamp for the request
    }
    r = requests.get(URL, params=payload, headers=headers, cookies=cookies)
    print("Response Status Code:", r.status_code)
    print("Response Content:", r.text)  # Print raw response content
    return r.json()

def clean_html_column(column):
    return column.apply(lambda x: BeautifulSoup(x, 'html.parser').get_text())

def main():
    #Main function to fetch, filter, and display recently added bands.
    # Get the last scraped day
    last_scraped_day = get_scrape_day(metadata_file, BANDS)
    print(f"Last scraped day: {last_scraped_day}")

    # Fetch new data
    data = get_recently_added_page()
    records = data.get('aaData', [])

    # Convert to DataFrame
    df = pd.DataFrame(records, columns=['MonthDay', 'Band URL', 'Country', 'Genre', 'Date', 'Submitter'])
    df[['Country', 'Genre', 'Band Name']] = df[['Country', 'Genre', 'Band URL']].apply(clean_html_column)
    df['Band URL'] = df['Band URL'].apply(lambda x: BeautifulSoup(x, 'html.parser').find('a')['href'])
    df['Day'] = df['MonthDay'].str.extract(r'(\d{1,2})').astype(int)
    df['Band ID'] = df['Band URL'].apply(extract_url_id)
    new_records_df = df[df['Day'] >= last_scraped_day]

    # Fetch the status & lyric themes for new/updated records
    result_df = new_records_df['Band URL'].apply(
        lambda url: pd.Series(get_dt(url, ["Status:", "Themes:"], headers, cookies))
    )
    new_records_df['Status'] = result_df['Status:']

    # Create a separate DataFrame for Themes
    themes_df = new_records_df[['Band ID']].copy()
    themes_df['Themes:'] = result_df['Themes:']

    if os.path.exists(LYRICS): #Only export lyrics if file exists.
        existing_df = pd.read_csv(LYRICS)
    # Merge the existing data with the new data on 'Band ID'
        merged_df = pd.concat([existing_df, themes_df]).drop_duplicates(subset='Band ID', keep='last')
        merged_df.to_csv(LYRICS, index=False)

    new_records_df = new_records_df.drop(columns=['Date', 'Submitter', 'Day', 'MonthDay'])

    # Reorder the columns to match the existing CSV
    new_records_df = new_records_df[['Band URL', 'Band Name', 'Country', 'Genre', 'Status', 'Band ID']]
    new_records_df[['Band ID', 'Band URL']].to_csv(TEMPFILE)
    # Remove duplicates based on Band ID (overwrite logic)
    for band_id in new_records_df['Band ID']:
        existing_bands_df = existing_bands_df[existing_bands_df['Band ID'] != band_id]

    updated_bands_df = pd.concat([existing_bands_df, new_records_df], ignore_index=True)

    # Print and save new records
    if not new_records_df.empty:
        print("New records added since last scrape (no duplicates):")
        updated_bands_df.to_csv(BANDSFILE, index=False)
    else:
        print("No new records added since last scrape or no new unique records.")

    print('Updating Metadata')
    update_metadata(os.path.basename(BANDS))
    print('Done!')
if __name__ == "__main__":
    main()
