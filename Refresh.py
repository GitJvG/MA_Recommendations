"""Just a lazy shorcut to execute incremental refreshes

If the dataset hasn't been refreshed in ~3-4 days
it may be better to do a full clean scrape using 
BandScraper.py and afterwards SimilarScraper.py"""

from Scripts.BandUpdtr import main as Band 
from Scripts.SimilarScraper import main as Sim 

Band() #Updates MA_Bands.csv and MA_Lyrics.csv
Sim() #Checks for changes in MA_Bands and scrapes the pages of new/changed bands.
try:
    from SQLpush import main as push
    push()
except ImportError:
    print('It is not supposed to work for you, dw')


