import pandas as pd
from MA_Scraper.Scripts.utils import Parallel_processing, Main_based_scrape, fetch
from MA_Scraper.Env import Env
from MA_Scraper.Scripts.Components.Helper.HTML_Scraper import extract_href, extract_text, parse_table
from MA_Scraper.Scripts.Components.Helper.ModifiedUpdater import Modified_based_list

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
    url = f'{env.url_similar}{band_id}'
    html_content = fetch(url, headers=env.head)

    if html_content:
        if "No similar artist has been recommended yet" in html_content:
            return pd.DataFrame(columns=['similar_id', 'score', 'band_id'])  # Return an empty DataFrame with the correct columns
        similar_artists = parse_similar_artists(html_content, band_id)

        df = pd.DataFrame(similar_artists)
        df.columns = ['similar_id', 'score', 'band_id']
        return df
    return pd.DataFrame(columns=['similar_id', 'score', 'band_id'])

def refresh(band_ids_to_scrape=None):
    band_ids_to_process = Modified_based_list(env.simi, complete=False, band_ids_to_process=band_ids_to_scrape)
    Parallel_processing(band_ids_to_process, env.batch_size, env.simi, scrape_band_data)
    
def main():
    band_ids_to_process = Main_based_scrape(env.simi, False)
    Parallel_processing(band_ids_to_process, env.batch_size, env.simi, scrape_band_data)

if __name__ == "__main__":
    main()