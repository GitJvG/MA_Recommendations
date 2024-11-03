import time
import os
from datetime import datetime, timedelta
import requests
from pandas import DataFrame
import json
import pandas as pd
from Scripts.utils import load_config,save_progress
from Scripts.Components.HTML_Scraper import extract_href, extract_text
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv(".env", override=True)

BASEURL = 'https://www.metal-archives.com/browse/ajax-letter/json/1/l/'
URL_MODIFIED = 'https://www.metal-archives.com/archives/ajax-band-list/by/modified/selection/'
length = 500  # max number of bands in a single view

# Load environment variables
COOKIES = load_config('Cookies')
HEADERS = load_config('Headers')
METADATA_FILE = os.getenv('METADATA')
BANDSFILE = os.getenv('BANDPAR')
TEMPFILE = os.getenv('TEMPID')
LYRICS = os.getenv('BANLYR')

def make_request(url, params=None):
    r = requests.get(url, params=params, headers=HEADERS, cookies=COOKIES)
    r.raise_for_status()
    return r.json()

def scrape_bands(letters='NBR A B C D E F G H I J K L M N O P Q R S T U V W X Y Z'.split(), status=False):
    def get_url(letter, start=0, length=length):
        payload = {
            'sEcho': 0,
            'iDisplayStart': start,
            'iDisplayLength': length
        }
        return make_request(BASEURL + letter, params=payload)

    """Include or exclude status, I decided not to use status from this page as it is not displayed on the 'modified' page of metallum 
    and thus not easily updatable without going to each individual band page. Status will thus be scraped by DetailScraper which scrapes all data from the individual band pages."""
    column_names = ['NameLink', 'Country', 'Genre']
    if status:
        column_names.append('Status')
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

                        df_chunk = DataFrame(js['aaData'], columns=column_names)
                        # Append chunk to the main data DataFrame
                        data = pd.concat([data, df_chunk], ignore_index=True)
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

    if not data.empty:
        print('Parsing')
        data['NameLink'] = data['NameLink'].apply(lambda html: BeautifulSoup(html, 'html.parser'))
        data['Band URL'] = data['NameLink'].apply(extract_href)
        data['Band Name'] = data['NameLink'].apply(extract_text)
        data['Band ID'] = data['Band URL'].apply(extract_url_id)
        data = data.drop(columns=['NameLink'])

        data.to_csv(BANDSFILE, index=False)
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
    """Constructs urls for each yearmonth since last scraping"""
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
    return make_request(url, params=payload)

def Update_modified(url, last_scraped_day=None, is_final_month=False, rows_per_page=200):
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
        
        # Strip HTML tags directly where needed
        df['Soup'] = df['Band URL'].apply(lambda html: BeautifulSoup(html, 'html.parser'))
        df['Soup Country'] = df['Country'].apply(lambda html: BeautifulSoup(html, 'html.parser'))
        df['Country'] = df['Soup Country'].apply(extract_text)
        df['Band URL'] = df['Soup'].apply(extract_href)
        df['Band Name'] = df['Soup'].apply(extract_text)
        df['Country'] = df['Country']
        df['Band ID'] = df['Band URL'].apply(extract_url_id)
        df['Day'] = df['MonthDay'].str.extract(r'(\d{1,2})').astype(int)
        if is_final_month and df['Day'].min().item() < last_scraped_day:
            print(f"Reached a day ({df['Day'].min().item()}) lower than the last scraped day ({last_scraped_day}). Stopping.")
            scrape_more = False

        filtered_df = df if not is_final_month else df[df['Day'] >= last_scraped_day]

        if not filtered_df.empty:
            print(f"Adding {len(filtered_df)} records from page {page}.")
            all_records.append(filtered_df)

        page += 1

    if all_records:
        combined_df = pd.concat(all_records, ignore_index=True)
        combined_df = combined_df[['Band URL', 'Band Name', 'Country', 'Genre', 'Band ID']]
        return combined_df
    else:
        print("No records found.")
        return pd.DataFrame()

def updater():
    last_scraped_date = get_last_scraped_date(METADATA_FILE, os.path.basename(BANDSFILE))
    if last_scraped_date is None:
        print("Failed to retrieve the last scraped date.")
        return

    urls_to_scrape = determine_urls_to_scrape(last_scraped_date, URL_MODIFIED)
    
    # Loop through each URL and scrape data
    for i, url in enumerate(urls_to_scrape):
        is_final_month = (i == len(urls_to_scrape) - 1)
        last_scraped_day = last_scraped_date.day if is_final_month else None

        print(f"Fetching bands for URL: {url}")
        bands_df = Update_modified(url, last_scraped_day=last_scraped_day, is_final_month=is_final_month)

        if not bands_df.empty:
            print(f"New records added since last scrape (no duplicates): {len(bands_df)}")
            save_progress(bands_df[['Band ID']], TEMPFILE)
            save_progress(bands_df, BANDSFILE)
        else:
            print(f"No new records found for {url}.")

# Call the function
if __name__ == "__main__":
    updater()
