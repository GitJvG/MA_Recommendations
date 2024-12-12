import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

import pandas as pd
from Scripts.utils import Parallel_processing, Main_based_scrape
from Env import Env
from Scripts.Components.Helper.HTML_Scraper import fetch, extract_href, extract_text, parse_table # Import your fetch function
from Scripts.Components.Helper.ModifiedUpdater import Modified_based_list

env = Env.get_instance()

def parse_similar_artists(html, band_id):
    """Parses similar artists from the provided HTML."""
    column_extractors = [
        (0, extract_href),  # First column similar_id
        (3, extract_text),  # Fourth column (score)
    ]
    results = parse_table(html, table_id='artist_list', row_selector='tr', column_extractors=column_extractors)
    for result in results:
        if result[0]:  # Accessing the first column which is 'similar_id'
            result[0] = result[0].split('/')[-1]  # Extracting the ID from the URL
        result['band_id'] = band_id

    return results

def scrape_band_data(band_id):
    url = f'https://www.metal-archives.com/band/ajax-recommendations/id/{band_id}'
    html_content = fetch(url, headers=env.head)

    if html_content:
        if "No similar artist has been recommended yet" in html_content:
            return pd.DataFrame(columns=['similar_id', 'score', 'band_id'])  # Return an empty DataFrame with the correct columns
        similar_artists = parse_similar_artists(html_content, band_id)

        df = pd.DataFrame(similar_artists)
        df.columns = ['similar_id', 'score', 'band_id']
        return df
    return pd.DataFrame(columns=['similar_id', 'score', 'band_id'])

def refresh():
    band_ids_to_process = Modified_based_list(env.simi, complete=False)
    Parallel_processing(band_ids_to_process, 200, env.simi, scrape_band_data)
    
def main():
    band_ids_to_process = Main_based_scrape(env.simi)
    Parallel_processing(band_ids_to_process, 200, env.simi, scrape_band_data)

if __name__ == "__main__":
    main()