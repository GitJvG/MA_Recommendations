"""Incremental updater is only based on day number as of now, this will be updated later. Should work fine for the rest of the current month."""
from utils import remove_duplicates, Env
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

env = Env.get_instance()

def refresh():
       
    from Scripts.Components.BandScraper import scrape_bands
    scrape_bands()
    from Scripts.Components.SimilarScraper import refresh as ReSim 
    ReSim() #Fetches all similar band data on Band IDs in Temp/MA_Changes.csv
    from Scripts.Components.AlbumScraper import refresh as ReAlb
    ReAlb() #Fetches all discograpghy band data on Band IDs in Temp/MA_Changes.csv
    from Scripts.Components.DetailScraper import refresh as ReDet
    ReDet()

    csv_files = ['Datasets/MA_Bands.csv', 'Datasets/MA_Similar.csv', 'Datasets/MA_Discog.csv', 'Datasets/MA_Details.csv', 'Datasets/metadata.csv']
    for csv in csv_files:
        remove_duplicates(csv)

if __name__ == "__main__":
    refresh()