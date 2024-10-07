import time
import requests
from pandas import DataFrame
import json
import pandas as pd
from Scripts.Components.BandParser import parse
from Scripts.utils import load_config
import os
from dotenv import load_dotenv

load_dotenv()

BASEURL = 'https://www.metal-archives.com'
RELURL = '/browse/ajax-letter/json/1/l/'
length = 500  # max number of bands in a single view

# Load environment variables
PARSED = os.getenv('BANDPAR')
COOKIES = load_config('Cookies')
HEADERS = load_config('Headers')

def scrape_bands(letters='NBR A B C D E F G H I J K L M N O P Q R S T U V W X Y Z'.split()):
    def get_url(letter, start=0, length=length):
        payload = {
            'sEcho': 0,  # if not set, response text is not valid JSON
            'iDisplayStart': start,  # set start index of band names returned
            'iDisplayLength': length  # only response lengths of 500 work
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
        parse(PARSED, data)  # Ensure you pass the correct DataFrame here
        print('Done!')
    else:
        print("No data retrieved.")

# Call the function
if __name__ == "__main__":
    scrape_bands()
