import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

import pandas as pd
from Scripts.utils import Parallel_processing, Main_based_scrape
from Env import Env
from Scripts.Components.Helper.HTML_Scraper import fetch, parse_table, extract_text
from Scripts.Components.Helper.ModifiedUpdater import Modified_based_list
env = Env.get_instance()

BASEURL = 'https://www.metal-archives.com/band/discography/id/'
ENDURL = '/tab/all'

def parse_html(html, band_id):
    """Parses album data from the provided HTML, including the band ID."""
    column_extractors = [
        (0, extract_text),  # (Album Name)
        (1, extract_text),  # (Type)
        (2, extract_text),  # (Year)
        (3, extract_text),  # (Reviews)
    ]
    albums = parse_table(html, table_class='display discog', row_selector='tr', column_extractors=column_extractors)

    df_albums = pd.DataFrame(albums)
    df_albums['band_id'] = band_id
    return df_albums

def fetch_album_data(band_id):
    """Fetches album data for a given band ID and returns it as a DataFrame."""
    url = f"{BASEURL}{band_id}{ENDURL}"
    html_content = fetch(url, headers=env.head)
    
    if html_content:
        df = parse_html(html_content, band_id)
        df.columns = ['name', 'type', 'year', 'reviews', 'band_id']
        df['review_count'] = df['reviews'].str.extract(r'(\d+)(?=\s?\()')
        df['review_score'] = df['reviews'].str.extract(r'\((\d+)%\)')
        return df
    return pd.DataFrame(columns=['name', 'type', 'year', 'reviews', 'band_id', 'review_count', 'review_score'])

def refresh():
    # Complete false because many bands don't have any discog entries.
    band_ids_to_process = Modified_based_list(env.disc, complete=False)
    # Because discog currently doesn't have a reliable unique id combination (that could be de-duplicated afterwards), all to be processed ids are first deleted.
    df = pd.read_csv(env.disc)
    df = df[~df["band_id"].isin(band_ids_to_process)]
    df.to_csv(env.disc, index=False)

    Parallel_processing(band_ids_to_process, 200, env.disc, fetch_album_data)
    
def main():
    """Main function to process all band IDs."""
    band_ids_to_process = Main_based_scrape(env.disc)
    Parallel_processing(band_ids_to_process, 200, env.disc, fetch_album_data)

if __name__ == "__main__":
    print(fetch_album_data(1))

