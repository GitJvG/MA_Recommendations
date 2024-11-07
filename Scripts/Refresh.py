"""Incremental updater is only based on day number as of now, this will be updated later. Should work fine for the rest of the current month."""
from utils import remove_duplicates, Env
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
    csv_files = [env.band, env.simi, env.disc, env.deta, env.meta]
    for csv in csv_files:
        remove_duplicates(csv)

if __name__ == "__main__":
    refresh()
    remove_dupes()