import time
import httpx
from pandas import DataFrame
import json
import pandas as pd
from MA_Scraper.Scripts.utils import extract_url_id, Parallel_processing, fetch
from MA_Scraper.Env import Env
from MA_Scraper.Scripts.Components.Helper.HTML_Scraper import extract_href, extract_text
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
import warnings
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

env = Env.get_instance()
alphabet = 'NBR A B C D E F G H I J K L M N O P Q R S T U V W X Y Z ~'.split()
label_letters = ['!', '"', '(', '%2E', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '[', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 
         'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '|', '¡', 'ä', 'å', 'æ', 'é', 'ñ', 'ö', 'ü', 'ć', 'č', 'ş', 'š', 
         'ž', 'γ', 'ν', 'σ', 'φ', 'ω', 'а', 'б', 'в', 'г', 'д', 'ж', 'з', 'и', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ч', 
         'ш', 'і', 'آ', 'ව', 'อ', 'ᛉ', 'オ', 'コ', '六', '反', '古', '大', '天', '帝', '朱', '殺', '没', '酒', '金', '麦', 'ꔅ', '열', '토', ' 呪']

def parse_bands(data):
    data['namelink'] = data['namelink'].apply(lambda html: BeautifulSoup(html, 'html.parser'))
    data['url'] = data['namelink'].apply(extract_href)
    data['name'] = data['namelink'].apply(extract_text)
    data['status'] = data['status'].apply(lambda html: BeautifulSoup(html, 'html.parser')).apply(extract_text)
    data['band_id'] = data['url'].apply(extract_url_id)
    data = data[['name','country','genre','status','band_id']]
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

def scrape_json(url, letters=alphabet):
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

    if isinstance(letters, (list, tuple)):
        letters = letters
    else:
        letters = [letters]

    for letter in letters:
        try:
            js = get_url(letter=letter, start=0, length=length)
            n_records = js['iTotalRecords']
            n_chunks = (n_records // length) + 1

            for i in range(n_chunks):
                start = length * i
                end = min(start + length, n_records)
                print(f'Fetching entries {start} to {end}/{n_records} for letter: {letter}')

                for attempt in range(env.retries):
                    time.sleep(env.delay)
                    try:
                        js = get_url(letter=letter, start=start, length=length)
                        df_chunk = DataFrame(js['aaData'], columns=column_names)
                        data = pd.concat([data, df_chunk], ignore_index=True)
                        break

                    except json.JSONDecodeError:
                        print('JSONDecodeError on attempt ', attempt + 1, ' of 10.')
                        if attempt == 9:
                            print('Max attempts reached, skipping this chunk.')
                            break
                        continue
                    except httpx.HTTPError as e:
                        print(f"HTTP error occurred: {e}")
                        break

        except httpx.HTTPError as e:
            print(f"HTTP error occurred while fetching letter '{letter}': {e}")
            continue

        return data

def Alphabetical_List_Scraper(letters=alphabet, **kwargs):
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

def Parrallel_Alphabetical_List_Scraper(url=env.url_band, letters=alphabet, batch_size=False, output=None, type=None):
    if not output:
        output = mapping[url]["csv"]

    if type:
        if type == 'band':
            letters = alphabet
        if type == 'label':
            letters = label_letters
    Parallel_processing(items_to_process=letters, 
                        batch_size=batch_size,
                        output_files=output,
                        function=Alphabetical_List_Scraper,
                        url=url
    )