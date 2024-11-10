from Scripts.utils import extract_url_id, get_last_scraped_date
from Env import Env
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import requests
import os
import pandas as pd

env = Env.get_instance()

def make_request(url, params=None):
    r = requests.get(url, params=params, headers=env.head, cookies=env.cook)
    r.raise_for_status()
    return r.json()

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

def fetch_bands_page(url, start=0, sEcho=1):
    payload = {
        'sEcho': sEcho,
        'iDisplayStart': start,
        'sSortDir_0': 'desc',
        '_': int(time.time() * 1000)
    }
    return make_request(url, params=payload)


def Modified_Set(url, last_scraped_day=None, is_final_month=False):
    """Returns set of band ids that have been modified since last scraping date"""
    page = 1
    band_ids = set()

    while True:
        # The page always display 200 regardless of what iDisplayLength is passed
        start_index = (page - 1) * 200
        data = fetch_bands_page(url, start=start_index)
        records = data.get('aaData', [])

        if not records:
            print(f"No more records found on page {page}.")
            break

        # Extract Band IDs with minimal processing
        for record in records:
            month_day, band_html = record[0], record[1]
            band_url = BeautifulSoup(band_html, 'html.parser').a['href']
            band_id = extract_url_id(band_url)
            
            # Check day filtering if in final month mode
            day = int(month_day.split()[1])
            if is_final_month and day < last_scraped_day:
                print(f"Reached a day ({day}) lower than the last scraped day ({last_scraped_day}). Stopping.")
                return band_ids  # Return set early if final day reached

            band_ids.add(band_id)

        print(f"Processed page {page}, total unique IDs so far: {len(band_ids)}")
        page += 1

    return band_ids

def Update_list(output_path):
    last_scraped_date = get_last_scraped_date(env.meta, os.path.basename(output_path))
    if last_scraped_date is None:
        print("Failed to retrieve the last scraped date.")
        return

    urls_to_scrape = determine_urls_to_scrape(last_scraped_date, env.url_modi)
    
    # Loop through each URL and scrape data
    for i, url in enumerate(urls_to_scrape):
        is_final_month = (i == len(urls_to_scrape) - 1)
        last_scraped_day = last_scraped_date.day if is_final_month else None

        print(f"Fetching bands for URL: {url}")
        bands_ids = Modified_Set(url, last_scraped_day=last_scraped_day, is_final_month=is_final_month)
    
    return list(bands_ids)

def Modified_based_list(target_path, complete = False):
    band_ids_to_process = Update_list(target_path)

    if complete:
        all_band_ids = set(pd.read_csv(env.band)['Band ID'])
        processed_set = set(pd.read_csv(target_path)['Band ID'])
        missing_ids = all_band_ids - processed_set
        band_ids_to_process = list(set(band_ids_to_process).union(missing_ids))

    # Proceed with parallel processing on the final list of IDs
    print(f"Total bands to refresh for {target_path}: {len(band_ids_to_process)}")
    return band_ids_to_process
