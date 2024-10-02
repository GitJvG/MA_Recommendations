import requests
import time
from bs4 import BeautifulSoup

def fetch(url, retries=5, delay_between_requests=0.05, cookies=None, headers=None):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, cookies=cookies)
            time.sleep(delay_between_requests)
            
            if response.status_code == 200:
                return response.text
            elif response.status_code == 429:
                print(f"Rate limit exceeded for {url}. Retrying...")
                sleep_time = 2 ** attempt  # Exponential backoff
                time.sleep(sleep_time)
            else:
                print(f"Failed to fetch data for {url}. Status code: {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"Request failed for {url}: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff on exception
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
        if len(cells) < len(column_extractors):  # Check if the row has enough cells
            continue

        row_data = {}
        for idx, extractor_info in enumerate(column_extractors):
            try:
                key = extractor_info['key']
                extractor = extractor_info['extractor']
                row_data[key] = extractor(cells[idx])  # Apply the extractor to the appropriate cell
            except Exception as e:
                print(f"Error extracting data for {key}: {e}")
                row_data[key] = None  # Handle cases where extraction might fail

        results.append(row_data)

    return results


def extract_href(cell):
    """Extracts the href attribute from a table cell."""
    return cell.find('a')['href'] if cell.find('a') else None

def extract_text(cell):
    """Extracts the text content from a table cell."""
    return cell.text.strip()

def get_dt(band_url, strings, headers, cookies, delay_between_requests=0.05):
    try:
        # Fetch the HTML content using the fetch function
        html_content = fetch(band_url, cookies=cookies, headers=headers, delay_between_requests=delay_between_requests)
        
        if html_content is None:
            return None  # Return early if fetching failed
        
        soup = BeautifulSoup(html_content, 'html.parser')

        if isinstance(strings, str):
            strings = [strings]
        
        results = {}
        
        for string in strings:
            dt_tag = soup.find('dt', string=string)
            if dt_tag:
                status = dt_tag.find_next('dd').text.strip()  # Get the text from the following 'dd' tag
                results[string] = status
            else:
                print(f"Element '{string}' not found.")
                results[string] = None
        
        return results
    except Exception as e:
        print(f"Error fetching status for {band_url}: {e}")
        return None

