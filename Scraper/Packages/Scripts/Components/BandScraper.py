import time
import os
import requests
from pandas import DataFrame
import json
import pandas as pd
from Scripts.utils import extract_url_id, update_metadata
from Env import Env
from Scripts.Components.Helper.HTML_Scraper import extract_href, extract_text
from bs4 import BeautifulSoup

env = Env.get_instance()
length = 500  # max number of bands in a single view

def make_request(url, params=None):
    r = requests.get(url, params=params, headers=env.head, cookies=env.cook)
    r.raise_for_status()
    return r.json()

def scrape_bands(letters='NBR A B C D E F G H I J K L M N O P Q R S T U V W X Y Z ~'.split()):
    def get_url(letter, start=0, length=length):
        payload = {
            'sEcho': 0,
            'iDisplayStart': start,
            'iDisplayLength': length
        }
        return make_request(env.url_band + letter, params=payload)

    column_names = ['NameLink', 'country', 'genre', 'status']
    data = DataFrame()
    # Retrieve the data
    for letter in letters:
        print('Current letter = ', letter)
        try:
            js = get_url(letter=letter, start=0, length=length)  # Get JSON directly here
            n_records = js['iTotalRecords']
            n_chunks = (n_records // length) + 1
            print('Total records = ', n_records)

            # Retrieve chunks
            for i in range(n_chunks):
                start = length * i
                end = min(start + length, n_records)
                print('Fetching band entries ', start, 'to ', end)

                for attempt in range(env.retries):
                    time.sleep(env.delay)
                    try:
                        js = get_url(letter=letter, start=start, length=length)  # Get JSON here as well

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
        data['url'] = data['NameLink'].apply(extract_href)
        data['name'] = data['NameLink'].apply(extract_text)
        data['band_id'] = data['url'].apply(extract_url_id)
        data = data[['url','name','country','genre','band_id']]
        return data
    else:
        print("No data retrieved.")
        return
    
def Full_scrape():
    data = scrape_bands()
    data.to_csv(env.band, index=False, mode='w')
    update_metadata(os.path.basename(env.band))
    print('Done!')
    
# Call the function
if __name__ == "__main__":
    Full_scrape()
