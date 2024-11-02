import time
import os
from datetime import datetime, timedelta
import requests
from pandas import DataFrame
import json
import pandas as pd
from Scripts.utils import load_config,save_progress
from Scripts.Components.HTML_Scraper import parse_bands_data, get_dt
from dotenv import load_dotenv

load_dotenv(".env", override=True)

BASEURL = 'https://www.metal-archives.com'
RELURL = '/browse/ajax-letter/json/1/l/'
URL_MODIFIED = 'https://www.metal-archives.com/archives/ajax-band-list/by/modified/selection/'
length = 500  # max number of bands in a single view

# Load environment variables
PARSED = os.getenv('BANDPAR')
COOKIES = load_config('Cookies')
HEADERS = load_config('Headers')
METADATA_FILE = os.getenv('METADATA')
BANDSFILE = os.getenv('BANDPAR')
TEMPFILE = os.getenv('TEMPID')
LYRICS = os.getenv('BANLYR')

initials_column_mapping = {
    'Band URL': {'source_col': 'NameLink', 'is_url': True},
    'Band Name': {'source_col': 'NameLink', 'is_url': False},
    'Country': {'source_col': 'Country'},
    'Genre': {'source_col': 'Genre'},
    'Status': {'source_col': 'Status'}
}

updater_column_mapping = {
    'MonthDay': {'source_col': 'MonthDay'},
    'Band URL': {'source_col': 'Band URL', 'is_url': True},
    'Band Name': {'source_col': 'Band URL', 'is_url': False},
    'Country': {'source_col': 'Country'},
    'Genre': {'source_col': 'Genre'},
    'Date': {'source_col': 'Date'},
    'Submitter': {'source_col': 'Submitter', 'is_url': False}
}

def scrape_bands(letters='NBR A B C D E F G H I J K L M N O P Q R S T U V W X Y Z'.split()):
    def get_url(letter, start=0, length=length):
        payload = {
            'sEcho': 0,  # if not set, response text is not valid JSON
            'iDisplayStart': start,  # set start index of band names returned
            'iDisplayLength': length
        }
        r = requests.get(BASEURL + RELURL + letter, params=payload, headers=HEADERS, cookies=COOKIES)
        r.raise_for_status()  # Raise an error for bad HTTP responses
        return r

    # Data columns returned in the JSON object
    column_names = ['NameLink', 'Country', 'Genre', 'Status']
    data = DataFrame()  # for collecting the results

    # Retrieve the data
    for letter in letters:
        print('Current letter = ', letter)
        try:
            r = get_url(letter=letter, start=0, length=length)
            js = r.json()
            n_records = js['iTotalRecords']
            n_chunks = (n_records // length) + 1
            print('Total records = ', n_records)

            # Retrieve chunks
            for i in range(n_chunks):
                start = length * i
                end = min(start + length, n_records)
                print('Fetching band entries ', start, 'to ', end)

                for attempt in range(10):
                    time.sleep(3)  # Obeying robots.txt "Crawl-delay: 3"
                    try:
                        r = get_url(letter=letter, start=start, length=length)
                        js = r.json()
                        # Store response
                        df = DataFrame(js['aaData'])
                        data = pd.concat([data, df], ignore_index=True)
                        break  # Exit retry loop if successful
                    except json.JSONDecodeError:
                        print('JSONDecodeError on attempt ', attempt + 1, ' of 10.')
                        if attempt == 9:
                            print('Max attempts reached, skipping this chunk.')
                            break
                        continue
                    except requests.HTTPError as e:
                        print(f"HTTP error occurred: {e}")
                        break  # Exit the loop on HTTP error

        except requests.HTTPError as e:
            print(f"HTTP error occurred while fetching letter '{letter}': {e}")
            continue  # Skip to the next letter

    # Set informative names
    data.columns = column_names
    data.index = range(len(data))

    if not data.empty:
        print('Parsing')
        parsed_data = parse_bands_data(data, initials_column_mapping)
        parsed_data.to_csv(PARSED, index=False)
        print('Done!')
    else:
        print("No data retrieved.")

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
        'iDisplayStart': start,
        'iDisplayLength': length,
        'sSortDir_0': 'desc',
        '_': int(time.time() * 1000)
    }
    
    r = requests.get(url, params=payload, headers=HEADERS, cookies=COOKIES)
    print(f"Response Status Code: {r.status_code}")
    return r.json()

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
        
        # Parse the DataFrame using the shared function
        parsed_df = parse_bands_data(df, updater_column_mapping)
        
        parsed_df['Day'] = parsed_df['MonthDay'].str.extract(r'(\d{1,2})').astype(int)
        if is_final_month and parsed_df['Day'].min().item() < last_scraped_day:
            print(f"Reached a day ({parsed_df['Day'].min().item()}) lower than the last scraped day ({last_scraped_day}). Stopping.")
            scrape_more = False

        filtered_df = parsed_df if not is_final_month else parsed_df[parsed_df['Day'] >= last_scraped_day]

        if not filtered_df.empty:
            print(f"Adding {len(filtered_df)} records from page {page}.")
            all_records.append(filtered_df)
        
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

def updater():
    last_scraped_date = get_last_scraped_date(METADATA_FILE, os.path.basename(BANDSFILE))
    if last_scraped_date is None:
        print("Failed to retrieve the last scraped date.")
        return

    # Loop through both 'created' and 'modified' URLs
    for url_base in [URL_MODIFIED]:
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

# Call the function
if __name__ == "__main__":
    scrape_bands()
