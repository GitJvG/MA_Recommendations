import time
import requests
from pandas import DataFrame
import json
import pandas as pd
from Scripts.utils import update_metadata
from BandParser import parse
from utils import load_cookies
import os
from dotenv import load_dotenv

load_dotenv()

BASEURL = 'https://www.metal-archives.com'
RELURL = '/browse/ajax-letter/json/1/l/'
length = 500  # max number of bands in a single view

# Load environment variables
raw_dump = os.getenv('BANDRAW')
parsed_dump = os.getenv('BANDPAR')

# Load cookies from json to bypass cloudflare
cookies = load_cookies('Cookies.json')

# Set headers
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
}

def scrape_bands(letters='NBR A B C D E F G H I J K L M N O P Q R S T U V W X Y Z'.split(), raw_dump=None, parsed_dump=None):
    def get_url(letter, start=0, length=length):
        payload = {
            'sEcho': 0,  # if not set, response text is not valid JSON
            'iDisplayStart': start,  # set start index of band names returned
            'iDisplayLength': length  # only response lengths of 500 work
        }
        r = requests.get(BASEURL + RELURL + letter, params=payload, headers=headers, cookies=cookies)
        return r

    # Data columns returned in the JSON object
    column_names = ['NameLink', 'Country', 'Genre', 'Status']
    data = DataFrame()  # for collecting the results

    # Retrieve the data
    for letter in letters:
        print('Current letter = ', letter)
        r = get_url(letter=letter, start=0, length=length)
        js = r.json()
        n_records = js['iTotalRecords']
        n_chunks = int(n_records / length) + 1
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
                except json.JSONDecodeError:
                    print('JSONDecodeError on attempt ', attempt, ' of 10.')
                    print('Retrying...')
                    continue
                break

    # Set informative names
    data.columns = column_names
    data.index = range(len(data))

    print('Writing band data to csv file:', raw_dump)
    data.to_csv(raw_dump, index=False)
    print('Updating Metadata')
    update_metadata(os.path.basename(raw_dump))
    print('Parsing')
    parse(parsed_dump, pd.read_csv(raw_dump))
    print('Updating Metadata')
    update_metadata(os.path.basename(parsed_dump))
    print('Done!')

# Call the function
if __name__ == "__main__":
    scrape_bands(raw_dump=raw_dump, parsed_dump=parsed_dump)
