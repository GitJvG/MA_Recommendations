# Incrementally updates MA_Bands & MA_Lyrics
import time
import pandas as pd
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
from HTML_Scraper import get_dt
from utils import load_config, save_progress

load_dotenv(".env", override=True)

# Constants
URL_ADDED = 'https://www.metal-archives.com/archives/ajax-band-list/by/created/'
URL_MODIFIED = 'https://www.metal-archives.com/archives/ajax-band-list/by/modified/'
METADATA_FILE = os.getenv('METADATA')
BANDSFILE = (os.getenv('BANDPAR'))
COOKIES = load_config('Cookies')
HEADERS = load_config('Headers')
TEMPFILE = (os.getenv('TEMPID'))
LYRICS = (os.getenv('BANLYR'))

def extract_url_id(url):
    return url.split('/')[-1]

def get_scrape_day(file_path, filename):
    # Load the last scraped date for a specific file from the metadata CSV and return the day of the month.
    try:
        df = pd.read_csv(file_path)
        file_info = df[df['Filename'] == filename]
        if not file_info.empty:
            date_str = file_info.iloc[0]['Date']
            date = datetime.strptime(date_str, '%Y-%m-%d')
            return date.day
    except Exception as e:
        print(f"Error: {e}")
    return 0  # Default day (refreshes all bands on the page with 0)

def fetch_bands_page(url, length=200, start=0, sEcho=1):
    # Generalized function to fetch bands data (either 'added' or 'modified')
    payload = {
        'sEcho': sEcho,
        'iColumns': 6,
        'sColumns': '',
        'iDisplayStart': start,
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
        '_': int(time.time() * 1000)  # Use current timestamp
    }
    r = requests.get(url, params=payload, headers=HEADERS, cookies=COOKIES)
    print(f"Response Status Code: {r.status_code}")
    return r.json()

def clean_html_column(column):
    return column.apply(lambda x: BeautifulSoup(x, 'html.parser').get_text())

def display_bands_until_last_scraped_day(url, rows_per_page=200):
    """Generalized function to fetch bands (added/modified) until the last scraped day."""

    last_scraped_day = get_scrape_day(METADATA_FILE, os.path.basename(BANDSFILE))
    print(f"Last scraped day from metadata: {last_scraped_day}")
    
    page = 1
    scrape_more = True
    all_records = []

    while scrape_more:
        start_index = (page - 1) * rows_per_page
        data = fetch_bands_page(url, length=rows_per_page, start=start_index)
        records = data.get('aaData', [])

        if not records:
            print(f"No more records found on page {page}.")
            break
        
        # Convert the records to a DataFrame and clean the HTML content
        df = pd.DataFrame(records, columns=['MonthDay', 'Band URL', 'Country', 'Genre', 'Date', 'Submitter'])
        df[['Country', 'Genre', 'Band Name']] = df[['Country', 'Genre', 'Band URL']].apply(clean_html_column)
        df['Band URL'] = df['Band URL'].apply(lambda x: BeautifulSoup(x, 'html.parser').find('a')['href'])
        
        # Extract the day from the MonthDay column
        df['Day'] = df['MonthDay'].str.extract(r'(\d{1,2})').astype(int)

        # Check if any of the day numbers are lower than the last scraped day
        if df['Day'].min().item() < last_scraped_day:
            print(f"Reached a day ({df['Day'].min().item()}) lower than the last scraped day ({last_scraped_day}). Stopping.")
            scrape_more = False

        filtered_df = df[df['Day'] >= last_scraped_day]

        if not filtered_df.empty:
            print(f"Adding {len(filtered_df)} records from page {page}.")
            all_records.append(filtered_df)
        else:
            print(f"No records found after filtering on page {page}.")
        
        page += 1  # Move to the next page

    if all_records:
        # Combine all records into a single DataFrame
        combined_df = pd.concat(all_records, ignore_index=True)
        return combined_df
    else:
        print("No records found.")
        return pd.DataFrame()  # Return empty DataFrame if no records

def process_combined_data(df):
    df['Band ID'] = df['Band URL'].apply(extract_url_id)
    
    # Fetch the status & lyric themes for new/updated records
    result_df = df['Band URL'].apply(
        lambda url: pd.Series(get_dt(url, ["Status:", "Themes:"], HEADERS, COOKIES))
    )
    df.loc[:, 'Status'] = result_df['Status:']

    # Create a separate DataFrame for Themes
    themes_df = df[['Band ID']].copy()
    themes_df['Themes:'] = result_df['Themes:']
    save_progress(themes_df, LYRICS)

    df = df.drop(columns=['Date', 'Submitter', 'MonthDay'])

    df = df[['Band URL', 'Band Name', 'Country', 'Genre', 'Status', 'Band ID']]
    #Save bands to temp file for other updating scripts.
    save_progress(df[['Band ID']], TEMPFILE)

    # Print and save new records
    if not df.empty:
        print(f"New records added since last scrape (no duplicates):{len(df)}")
        save_progress(df, BANDSFILE)
    else:
        print("No new records added since last scrape or no new unique records.")
    print('Done!')

def main():
    # Fetch and process records from both the 'added' and 'modified' URLs
    print("Fetching recently added bands:")
    added_bands_df = display_bands_until_last_scraped_day(URL_ADDED)

    print("Fetching recently modified bands:")
    modified_bands_df = display_bands_until_last_scraped_day(URL_MODIFIED)

    # Combine both DataFrames if they are not empty
    if not added_bands_df.empty or not modified_bands_df.empty:
        combined_df = pd.concat([added_bands_df, modified_bands_df], ignore_index=True)
        process_combined_data(combined_df)

if __name__ == "__main__":
    main()
