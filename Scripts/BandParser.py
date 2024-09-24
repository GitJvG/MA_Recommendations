import pandas as pd
from bs4 import BeautifulSoup

def extract_url_id(url):
    return url.split('/')[-1]  # ID is the last part of the URL

def parse(destination, data=pd.DataFrame):
    band_urls = []
    band_names = []
    band_countries = []
    band_genres = []
    band_statuses = []

    # Iterate through each row in the DataFrame
    for index, row in data.iterrows():
        # Parse the 'NameLink' column which contains the URL and band name
        name_link_html = row['NameLink']
        soup = BeautifulSoup(name_link_html, 'html.parser')
        
        # Extract the URL and band name
        band_url = soup.find('a')['href']
        band_name = soup.find('a').text.strip()
        
        # Append the extracted values to the lists
        band_urls.append(band_url)
        band_names.append(band_name)
        
        # Append other columns (Country, Genre, Status) directly
        band_countries.append(row['Country'])
        band_genres.append(row['Genre'])
        
        # For 'Status', we want to extract the text from the HTML tags
        status_html = row['Status']
        status_soup = BeautifulSoup(status_html, 'html.parser')
        band_status = status_soup.text.strip()
        
        band_statuses.append(band_status)

    # Create a new DataFrame with the parsed data
    parsed_data = pd.DataFrame({
        'Band URL': band_urls,
        'Band Name': band_names,
        'Country': band_countries,
        'Genre': band_genres,
        'Status': band_statuses
    })

    # Add a new column with extracted IDs
    parsed_data['Band ID'] = parsed_data['Band URL'].apply(extract_url_id)
    parsed_data.to_csv(destination, index=False)
    print("Data parsing and ID extraction complete!")
