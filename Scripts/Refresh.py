"""Incremental updater scrapes based on year, month and day. It re-scrapes the last scraped day to ensure no modifications are missed. 
Because of this, it is recommended to only run this script periodically to reduce the % of scraping data you've already scraped.
This will be faster for you and less resource intensive for Metallum servers."""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Scripts.utils import remove_dupes_and_deletions, update_metadata, get_time
from Env import Env
from Scripts.Components.BandScraper import Full_scrape
from Scripts.Components.SimilarScraper import refresh as ReSim
from Scripts.Components.AlbumScraper import refresh as ReAlb
from Scripts.Components.DetailScraper import refresh as ReDet

env = Env.get_instance()


def refresh():
    # Time handling is done at this level to ensure consistency between files on consecutive refreshes.
    # Time is set before all scraping, leading to some repeats on consecutive refreshes, this is done to ensure data-integrity and consistency.
    time = get_time()
    csv_files = [env.band, env.simi, env.disc, env.deta, env.meta, env.memb]
    Full_scrape()
    ReSim()
    ReAlb()
    ReDet()
    for csv in csv_files: remove_dupes_and_deletions(csv)
    for csv in csv_files: update_metadata(csv)
    # Only updating time when everything succesfully refreshed.
    update_metadata(time=time)

if __name__ == "__main__":
    refresh()
