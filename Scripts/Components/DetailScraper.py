import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

import pandas as pd
from Scripts.utils import Parallel_processing, Main_based_scrape, fetch, extract_url_id
from Env import Env
from bs4 import BeautifulSoup
from Scripts.Components.Helper.ModifiedUpdater import Modified_based_list

env = Env.get_instance()

def fetch_band_stats(soup, band_id):
    """Helper function to extract band stats (general information) from the soup."""
    band_stats = soup.find('div', id='band_stats')
    results = {}
    dt = band_stats.find_all('dt')
    for dt in dt[:-2] + dt[-1:]: # all but label
        key = dt.text.strip().replace(':', '')
        value = dt.find_next('dd').text.strip()
        
        # Clean up the value further
        value = ' '.join(value.split())
        results[key] = value

    label_dd = band_stats.find_all('dd')[-2] # just the label
    link = label_dd.find('a')

    results['label'] = link.text.strip() if link else ''
    results['label_id'] = extract_url_id(link['href']) if link else ''

    # Add the band ID to the results dictionary
    results['band_id'] = band_id

    results = pd.DataFrame([results])
    results.columns = ['country','location','status','year_formed','genre','themes',
                       'years_active','label','label_id','band_id']
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
                member_id = member_url.split('/')[-1]
                role = ' '.join(role.split())

                members.append({
                    'band_id': band_id,
                    'member_id': member_id,
                    'name': member_name,
                    'role': role,
                    'category': category
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

        band_df = fetch_band_stats(soup, band_id)
        members_df = fetch_band_members(soup, band_id)

        return band_df, members_df

    except Exception as e:
        print(f"Error fetching band data for {band_url}: {e}")
        return None
    
def main():
    band_ids_to_process = set(Main_based_scrape(env.deta) + Main_based_scrape(env.memb))
    Parallel_processing(band_ids_to_process, env.batch_size, [env.deta, env.memb], get_band_data)

def refresh(band_ids_to_scrape=None):
    # Complete = true because all band ids in main should at least have a profile
    band_ids_to_process = Modified_based_list(env.deta, complete=True, band_ids_to_process=band_ids_to_scrape)
    Parallel_processing(band_ids_to_process, env.batch_size, [env.deta, env.memb], get_band_data)

if __name__ == "__main__":
    main()