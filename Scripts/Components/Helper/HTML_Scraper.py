from bs4 import BeautifulSoup
from Env import Env
env = Env.get_instance()

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