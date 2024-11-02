"""Incremental updater is only based on day number as of now, this will be updated later. Should work fine for the rest of the current month."""

from dotenv import load_dotenv
from utils import remove_duplicates
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

def refresh():
    TEMP = os.getenv('TEMPID')
    if os.path.exists(TEMP): #Deletes temp file created by BandUpdtr on the last run.
        os.remove(TEMP)  # Delete the file
        print(f"{TEMP} has been deleted.")
    else:
        print(f"{TEMP} does not exist.")

    from Scripts.Components.BandScraper import updater as Band_and_Themes 
    Band_and_Themes() #Updates both MA_Bands and MA_Lyrics. Together reduces the amount of requests needed. Also saves a list of edited Band IDs in Temp/MA_Changes.csv
    from Scripts.Components.SimilarScraper import refresh as ReSim 
    ReSim() #Fetches all similar band data on Band IDs in Temp/MA_Changes.csv
    from Scripts.Components.AlbumScraper import refresh as ReAlb
    ReAlb() #Fetches all discograpghy band data on Band IDs in Temp/MA_Changes.csv


    """Despite some efforts I keep getting duplicates, so for the time being this will do a second check and only keep the last entries."""
    csv_files = ['Datasets\MA_Bands.csv', 'Datasets\MA_Similar.csv', 'Datasets\MA_Discog.csv', 'Datasets\MA_Lyrics.csv', 'Datasets\metadata.csv']
    for csv in csv_files:
        remove_duplicates(csv)

if __name__ == "__main__":
    refresh()