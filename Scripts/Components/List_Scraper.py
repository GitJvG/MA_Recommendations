import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

import time
import requests
from pandas import DataFrame
import json
import pandas as pd
from Scripts.utils import extract_url_id, Parallel_processing, fetch
from Env import Env
from Scripts.Components.Helper.HTML_Scraper import extract_href, extract_text
from bs4 import BeautifulSoup

env = Env.get_instance()
letters = 'NBR A B C D E F G H I J K L M N O P Q R S T U V W X Y Z ~'.split()

def make_request(url, params=None):
    r = requests.get(url, params=params, headers=env.head, cookies=env.cook)
    r.raise_for_status()
    return r.json()

def parse_bands(data):
    data['namelink'] = data['namelink'].apply(lambda html: BeautifulSoup(html, 'html.parser'))
    data['url'] = data['namelink'].apply(extract_href)
    data['name'] = data['namelink'].apply(extract_text)
    data['band_id'] = data['url'].apply(extract_url_id)
    data = data[['name','country','genre','band_id']]
    return data

def parse_labels(data):
    data['namelink'] = data['namelink'].apply(lambda html: BeautifulSoup(html, 'html.parser'))
    data['url'] = data['namelink'].apply(extract_href)
    data['name'] = data['namelink'].apply(extract_text)
    data['label_id'] = data['url'].apply(extract_url_id)
    data['genre'] = data['genre'].apply(lambda html: BeautifulSoup(html, 'html.parser')).apply(extract_text)
    data['status'] = data['status'].apply(lambda html: BeautifulSoup(html, 'html.parser')).apply(extract_text)
    data['country'] = data['country'].apply(lambda html: BeautifulSoup(html, 'html.parser')).apply(extract_text)

    data = data[['label_id', 'name','country','genre', 'status']]
    return data

mapping = {
        env.url_band: {"csv": env.band, "parser": parse_bands, "columns": ['namelink', 'country', 'genre', 'status'], "length": 500},
        env.url_label: {"csv": env.label, "parser": parse_labels, "columns": ['edit', 'namelink', 'genre', 'status', 'country', 'website', 'shopping'], "length": 200},
    }

def scrape_json(url, letters=letters):
    column_names = mapping[url]["columns"]
    length = mapping[url]["length"]
    def get_url(letter, start=0, length=length):
        payload = {
            'sEcho': 0,
            'iDisplayStart': start,
            'iDisplayLength': length
        }
        return fetch(url + letter, delay_between_requests=1, type='json', params=payload)

    data = DataFrame()

    for letter in letters:
        try:
            js = get_url(letter=letter, start=0, length=length)
            n_records = js['iTotalRecords']
            n_chunks = (n_records // length) + 1

            # Retrieve chunks
            for i in range(n_chunks):
                start = length * i
                end = min(start + length, n_records)
                print(f'Fetching entries {start} to {end}/{n_records} for letter: {letter}')

                for attempt in range(env.retries):
                    time.sleep(env.delay)
                    try:
                        js = get_url(letter=letter, start=start, length=length)

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

        return data

def Alphabetical_List_Scraper(letters=letters, **kwargs):
    if kwargs['url']: 
        url = kwargs['url']
    else:
        print('missing mandatory url kwarg')
        return
    if not url in mapping:
        print('Error: Invalid url was passed. Only pass the bands or labels alphabetical list urls.')
        return
        
    data = scrape_json(url=url, letters=letters)

    if data.empty:
        print('An empty dataframe was received before parsing.')
        return
    
    parser = mapping[url]["parser"]
    data = parser(data)

    return data

def Parrallel_Alphabetical_List_Scraper(url=env.url_band, letters=letters, batch_size=False, output=None):
    if not output:
        output = mapping[url]["csv"]
    Parallel_processing(items_to_process=letters, 
                        batch_size=batch_size,
                        output_files=output,
                        function=Alphabetical_List_Scraper,
                        url=url
    )
    
if __name__ == "__main__":
    Parrallel_Alphabetical_List_Scraper(env.url_label)
