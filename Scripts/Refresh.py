"""Incremental updater scrapes based on year, month, and time. Last scraped time is only updated at the end of a successful refresh"""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Scripts.utils import remove_dupes_and_deletions, update_metadata, get_time, get_common_date
from Env import Env
from Scripts.Components.Helper.ModifiedUpdater import Modified_based_list
from Scripts.Components.List_Scraper import Parrallel_Alphabetical_List_Scraper
from Scripts.Components.SimilarScraper import refresh as ReSim
from Scripts.Components.AlbumScraper import refresh as ReAlb
from Scripts.Components.DetailScraper import refresh as ReDet

env = Env.get_instance()

def refresh():
    # Time handling is done at this level to ensure consistency between files on consecutive refreshes.
    # Time is set before all scraping, leading to some repeats on consecutive refreshes, this is done to ensure data-integrity and consistency.
    time = get_time()
    csv_files = [env.band, env.label, env.simi, env.disc, env.deta, env.meta, env.memb]
    Parrallel_Alphabetical_List_Scraper(env.url_band)
    Parrallel_Alphabetical_List_Scraper(env.url_label)

    # Use the same modified bands list for all files if all files share the same last scraping date
    common_date = get_common_date()
    if common_date:
        band_ids_to_scrape = Modified_based_list(common_date, False)
    else: band_ids_to_scrape = None

    ReSim(band_ids_to_scrape=band_ids_to_scrape)
    ReAlb(band_ids_to_scrape=band_ids_to_scrape)
    ReDet(band_ids_to_scrape=band_ids_to_scrape)
    for csv in csv_files: remove_dupes_and_deletions(csv)
    for csv in csv_files: update_metadata(csv)
    # Only updating time when everything succesfully refreshed.
    update_metadata(time=time)

if __name__ == "__main__":
    refresh()
