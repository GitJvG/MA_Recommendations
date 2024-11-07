import pandas as pd
from Scripts.utils import Parallel_processing, Env, Main_based_scrape
from Scripts.Components.HTML_Scraper import fetch, extract_href, extract_text, parse_table # Import your fetch function
from Scripts.Components.ModifiedUpdater import Modified_based_scrape

# Load environment variables
env = Env.get_instance()

def parse_similar_artists(html, band_id):
    """Parses similar artists from the provided HTML."""
    column_extractors = [
        (0, extract_href),  # First column Similar Artist ID
        (3, extract_text),  # Fourth column (Score)
    ]
    results = parse_table(html, table_id='artist_list', row_selector='tr', column_extractors=column_extractors)
    for result in results:
        if result[0]:  # Accessing the first column which is 'Similar Artist ID'
            result[0] = result[0].split('/')[-1]  # Extracting the ID from the URL
        result['Band ID'] = band_id

    return results

def scrape_band_data(band_id):
    url = f'https://www.metal-archives.com/band/ajax-recommendations/id/{band_id}'
    html_content = fetch(url, headers=env.head)

    if html_content:
        if "No similar artist has been recommended yet" in html_content:
            return pd.DataFrame(columns=['Similar Artist ID', 'Score', 'Band ID'])  # Return an empty DataFrame with the correct columns
        similar_artists = parse_similar_artists(html_content, band_id)

        df = pd.DataFrame(similar_artists)
        df.columns = ['Similar Artist ID', 'Score', 'Band ID']
        return df
    return pd.DataFrame(columns=['Similar Artist ID', 'Score', 'Band ID'])

def refresh():
    Modified_based_scrape(env.simi, scrape_band_data, complete=False)
    
def main():
    band_ids_to_process = Main_based_scrape(env.simi)
    Parallel_processing(band_ids_to_process, 200, env.simi, scrape_band_data)

if __name__ == "__main__":
    main()