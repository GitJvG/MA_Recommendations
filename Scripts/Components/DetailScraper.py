# Incrementally updates MA_Bands & MA_Lyrics
import pandas as pd
from Scripts.Components.Helper.HTML_Scraper import fetch
from Scripts.utils import Parallel_processing, Main_based_scrape
from Env import Env
from bs4 import BeautifulSoup
from Scripts.Components.Helper.ModifiedUpdater import Modified_based_list

env = Env.get_instance()

def fetch_band_stats(soup, band_id):
    """Helper function to extract band stats (general information) from the soup."""
    band_stats = soup.find('div', id='band_stats')
    results = {}
    
    # Loop through all dt elements to collect data
    for dt in band_stats.find_all('dt'):
        key = dt.text.strip().replace(':', '')
        value = dt.find_next('dd').text.strip()  # Get the corresponding dd text
        
        # Clean up the value further
        value = ' '.join(value.split())  # Replace multiple spaces/newlines with a single space
        results[key] = value  # Store the result in the dictionary
    
    # Add the band ID to the results dictionary
    results['Band ID'] = band_id
    return results

def fetch_band_members(soup, band_id):
    """Helper function to extract band members data from the soup."""
    members_section = soup.find('div', id='band_tab_members')
    members = []

    # Only process specific categories (skipping 'Complete lineup')
    for section_id, category in [
        ('band_tab_members_current', 'Current lineup'),
        ('band_tab_members_past', 'Past members'),
        ('band_tab_members_live', 'Live musicians')
    ]:
        section = members_section.find('div', id=section_id)
        
        if section:
            for row in section.select('tr.lineupRow'):
                member_link = row.find('a')
                member_name = row.find('a').text.strip()
                role = row.find_all('td')[1].text.strip()
                
                member_url = member_link['href']
                member_id = member_url.split('/')[-1]  # Get the last part of the URL
                    
                role = row.find_all('td')[1].text.strip()
                    
                # Clean up the role text
                role = ' '.join(role.split())
                    
                    # Add the member details to the list
                members.append({
                    'Band ID': band_id,
                    'Member ID': member_id,
                    'Name': member_name,
                    'Role': role,
                    'Category': category  # Store category as per section
                })

    # Convert the list of members to a DataFrame
    members_df = pd.DataFrame(members)
    return members_df
    
def get_band_data(band_id):
    """Main function to fetch band data, using helper functions."""
    band_url = f'https://www.metal-archives.com/bands/id/{band_id}'
    try:
        html_content = fetch(band_url, headers=env.head)
        
        if html_content is None:
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')

        band_stats = fetch_band_stats(soup, band_id)
        band_df = pd.DataFrame([band_stats])
        members_df = fetch_band_members(soup, band_id)

        return band_df, members_df

    except Exception as e:
        print(f"Error fetching band data for {band_url}: {e}")
        return None
    
def main():
    band_ids_to_process = set(Main_based_scrape(env.deta) + Main_based_scrape(env.memb))
    Parallel_processing(band_ids_to_process, 500, [env.deta, env.memb], get_band_data)

def refresh():
    # Complete = true because all band ids in main should at least have a profile
    band_ids_to_process = Modified_based_list(env.deta, complete=True)
    Parallel_processing(band_ids_to_process, 500, [env.deta, env.memb], get_band_data)
