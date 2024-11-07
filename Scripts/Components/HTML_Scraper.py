import requests
import time
from bs4 import BeautifulSoup
from utils import Env
env = Env.get_instance()

def fetch(url, retries=env.retries, delay_between_requests=env.delay, headers=env.head):
    session = requests.Session()
    session.headers.update(headers)
    session.cookies.update(env.cook)
    
    for attempt in range(retries):
        try:
            response = session.get(url)
            time.sleep(delay_between_requests)
            
            # Check if the response is successful
            if response.status_code == 200:
                return response.text  # Successful response
            else:
                # Retry on any non-200 status code with exponential backoff
                print(f"Retrying {url} due to status code {response.status_code}. Attempt {attempt + 1}")
                sleep_time = 2 ** attempt  # Exponential backoff
                time.sleep(sleep_time)
        except requests.RequestException as e:
            # Retry on request exceptions as well
            print(f"Request failed for {url}: {e}. Attempt {attempt + 1}")
            time.sleep(2 ** attempt)  # Exponential backoff on exception
    
    # If all retries are exhausted
    print(f"Failed to retrieve {url}.")
    return None

def parse_table(html, table_id=None, table_class=None, row_selector='tr', column_extractors=None):
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    # Find the table by ID or class
    if table_id:
        table = soup.find('table', {'id': table_id})
    elif table_class:
        table = soup.find('table', {'class': table_class})
    else:
        table = soup.find('table')  # Fallback to the first table if neither ID nor class is provided

    if not table:
        return results  # Return empty list if table not found

    # Extract rows based on the provided row selector
    rows = table.find('tbody').find_all(row_selector)
    for row in rows:
        cells = row.find_all('td')
        if len(cells) < max(col[0] for col in column_extractors) + 1:  # Check if the row has enough cells
            continue

        row_data = {}
        for idx, (col_index, extractor) in enumerate(column_extractors):
            try:
                row_data[idx] = extractor(cells[col_index])  # Apply the extractor to the appropriate cell
            except Exception as e:
                print(f"Error extracting data for index {col_index}: {e}")
                row_data[idx] = None  # Handle cases where extraction might fail

        results.append(row_data)

    return results

def extract_href(soup):
    link = soup.find('a')
    return link['href'] if link else None

def extract_text(soup):
    return soup.get_text(strip=True)