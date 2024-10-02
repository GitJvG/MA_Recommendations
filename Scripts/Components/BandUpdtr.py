# Incrementally updates MA_Bands & MA_Lyrics
import time
import pandas as pd
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
from Scripts.Components.HTML_Scraper import get_dt
from Scripts.utils import load_config, save_progress

load_dotenv(".env", override=True)

# Constants
URL_ADDED = 'https://www.metal-archives.com/archives/ajax-band-list/by/created/selection/'
URL_MODIFIED = 'https://www.metal-archives.com/archives/ajax-band-list/by/modified/selection/'
METADATA_FILE = os.getenv('METADATA')
BANDSFILE = os.getenv('BANDPAR')
COOKIES = load_config('Cookies')
HEADERS = load_config('Headers')
TEMPFILE = os.getenv('TEMPID')
LYRICS = os.getenv('BANLYR')

def extract_url_id(url):
    return url.split('/')[-1]

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

def determine_urls_to_scrape(last_scraped_date, url_base):
    current_date = datetime.now()
    urls_to_scrape = []

    # Loop over each month from last scraped date to current date
    while last_scraped_date <= current_date:
        formatted_month = last_scraped_date.strftime('%Y-%m')
        url = f"{url_base}{formatted_month}"
        urls_to_scrape.append(url)
        last_scraped_date = (last_scraped_date.replace(day=1) + timedelta(days=32)).replace(day=1)

    return urls_to_scrape

def fetch_bands_page(url, length=200, start=0, sEcho=1):
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
        '_': int(time.time() * 1000)
    }
    r = requests.get(url, params=payload, headers=HEADERS, cookies=COOKIES)
    print(f"Response Status Code: {r.status_code}")
    return r.json()

def clean_html_column(column):
    return column.apply(lambda x: BeautifulSoup(x, 'html.parser').get_text())

def display_bands_until_last_scraped_day(url, last_scraped_day=None, is_final_month=False, rows_per_page=200):
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
        
        df = pd.DataFrame(records, columns=['MonthDay', 'Band URL', 'Country', 'Genre', 'Date', 'Submitter'])
        df[['Country', 'Genre', 'Band Name']] = df[['Country', 'Genre', 'Band URL']].apply(clean_html_column)
        df['Band URL'] = df['Band URL'].apply(lambda x: BeautifulSoup(x, 'html.parser').find('a')['href'])
        df['Day'] = df['MonthDay'].str.extract(r'(\d{1,2})').astype(int)

        if is_final_month and df['Day'].min().item() < last_scraped_day:
            print(f"Reached a day ({df['Day'].min().item()}) lower than the last scraped day ({last_scraped_day}). Stopping.")
            scrape_more = False

        filtered_df = df if not is_final_month else df[df['Day'] >= last_scraped_day]

        if not filtered_df.empty:
            print(f"Adding {len(filtered_df)} records from page {page}.")
            all_records.append(filtered_df)
        else:
            print(f"No records found after filtering on page {page}.")
        
        page += 1

    if all_records:
        combined_df = pd.concat(all_records, ignore_index=True)
        return combined_df
    else:
        print("No records found.")
        return pd.DataFrame()

def process_combined_data(df):
    df['Band ID'] = df['Band URL'].apply(extract_url_id)
    
    result_df = df['Band URL'].apply(
        lambda url: pd.Series(get_dt(url, ["Status:", "Themes:"], HEADERS, COOKIES))
    )
    df.loc[:, 'Status'] = result_df['Status:']

    themes_df = df[['Band ID']].copy()
    themes_df['Themes:'] = result_df['Themes:']
    save_progress(themes_df, LYRICS)

    df = df.drop(columns=['Date', 'Submitter', 'MonthDay'])
    df = df[['Band URL', 'Band Name', 'Country', 'Genre', 'Status', 'Band ID']]
    save_progress(df[['Band ID']], TEMPFILE)

    if not df.empty:
        print(f"New records added since last scrape (no duplicates): {len(df)}")
        save_progress(df, BANDSFILE)
    else:
        print("No new records added since last scrape or no new unique records.")
    print('Done!')

def main():
    last_scraped_date = get_last_scraped_date(METADATA_FILE, os.path.basename(BANDSFILE))
    if last_scraped_date is None:
        print("Failed to retrieve the last scraped date.")
        return

    # Loop through both 'created' and 'modified' URLs
    for url_base in [URL_ADDED, URL_MODIFIED]:
        print(f"Processing data for URL base: {url_base}")

        # Determine URLs to scrape (from the last scraped date to the current month)
        urls_to_scrape = determine_urls_to_scrape(last_scraped_date, url_base)
    
        # Loop through each URL and scrape data
        for i, url in enumerate(urls_to_scrape):
            is_final_month = (i == len(urls_to_scrape) - 1)
            last_scraped_day = last_scraped_date.day if is_final_month else None

            print(f"Fetching bands for URL: {url}")
            bands_df = display_bands_until_last_scraped_day(url, last_scraped_day=last_scraped_day, is_final_month=is_final_month)

            if not bands_df.empty:
                process_combined_data(bands_df)
            else:
                print(f"No new records found for {url}.")

if __name__ == "__main__":
    main()
