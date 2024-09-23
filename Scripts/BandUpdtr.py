# Incrementally updates MA_Bands
import time
import pandas as pd
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
from HTML_Scraper import get_dt
from utils import update_metadata, load_config, save_progress

load_dotenv(".env", override=True)

# Constants
URL = 'https://www.metal-archives.com/archives/ajax-band-list/by/created/json/1/1/'
METADATA_FILE = os.getenv('METADATA')
BANDSFILE = (os.getenv('BANDPAR'))
COOKIES = load_config('Cookies')
HEADERS = load_config('Headers')
TEMPFILE = (os.getenv('TEMPID'))
LYRICS = (os.getenv('BANLYR'))

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
            return date.day
    
    except Exception as e:
        print(f"Error: {e}")
    
    # Return a default day if not found (Refreshes all bands on the page with 0)
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
    r = requests.get(URL, params=payload, headers=HEADERS, cookies=COOKIES)
    print("Response Status Code:", r.status_code)
    return r.json()

def clean_html_column(column):
    return column.apply(lambda x: BeautifulSoup(x, 'html.parser').get_text())

def main():
    #Main function to fetch, filter, and display recently added bands.
    last_scraped_day = get_scrape_day(METADATA_FILE, os.path.basename(BANDSFILE))
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
        lambda url: pd.Series(get_dt(url, ["Status:", "Themes:"], HEADERS, COOKIES))
    )
    new_records_df.loc[:, 'Status'] = result_df['Status:']

    # Create a separate DataFrame for Themes
    themes_df = new_records_df[['Band ID']].copy()
    themes_df['Themes:'] = result_df['Themes:']

    save_progress(themes_df, LYRICS)

    new_records_df = new_records_df.drop(columns=['Date', 'Submitter', 'Day', 'MonthDay'])

    # Reorder the columns to match the existing CSV
    new_records_df = new_records_df[['Band URL', 'Band Name', 'Country', 'Genre', 'Status', 'Band ID']]
    new_records_df[['Band ID', 'Band URL']].to_csv(TEMPFILE, index=False)

    # Print and save new records
    if not new_records_df.empty:
        print("New records added since last scrape (no duplicates):")
        save_progress(new_records_df, BANDSFILE)
    else:
        print("No new records added since last scrape or no new unique records.")
    update_metadata(os.path.basename(BANDSFILE))
    print('Done!')
if __name__ == "__main__":
    main()
