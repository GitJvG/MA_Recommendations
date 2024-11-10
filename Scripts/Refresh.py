"""Incremental updater scrapes based on year, month and day. It re-scrapes the last scraped day to ensure no modifications are missed. 
Because of this, it is recommended to only run this script periodically to reduce the % of scraping data you've already scraped.
This will be faster for you and less resource intensive for Metallum servers."""
from utils import remove_dupes_and_deletions
from Env import Env
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Scripts.Components.BandScraper import scrape_bands
from Scripts.Components.SimilarScraper import refresh as ReSim
from Scripts.Components.AlbumScraper import refresh as ReAlb
from Scripts.Components.DetailScraper import refresh as ReDet

env = Env.get_instance()

def refresh():
    scrape_bands()
    ReSim()
    ReAlb()
    ReDet()

def remove_dupes():
    # Removes dupes, keeping last, and entries that have been deleted since last scrape. 
    # (all modified entries are appended to the original file) 
    csv_files = [env.band, env.simi, env.disc, env.deta, env.meta, env.memb]
    for csv in csv_files:
        remove_dupes_and_deletions(csv)

if __name__ == "__main__":
    refresh()
    remove_dupes()