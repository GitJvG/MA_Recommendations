"""Incremental updater scrapes based on year, month and day. It re-scrapes the last scraped day to ensure no modifications are missed. 
Because of this, it is recommended to only run this script periodically to reduce the % of scraping data you've already scraped.
This will be faster for you and less resource intensive for Metallum servers."""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import remove_dupes_and_deletions, update_metadata
from Env import Env
from Scripts.Components.BandScraper import Full_scrape
from Scripts.Components.SimilarScraper import refresh as ReSim
from Scripts.Components.AlbumScraper import refresh as ReAlb
from Scripts.Components.DetailScraper import refresh as ReDet

env = Env.get_instance()
csv_files = [env.band, env.simi, env.disc, env.deta, env.meta, env.memb]

def refresh():
    Full_scrape()
    ReSim()
    ReAlb()
    ReDet()

if __name__ == "__main__":
    #refresh()
    for csv in csv_files: remove_dupes_and_deletions(csv)
    for csv in csv_files: update_metadata(csv)