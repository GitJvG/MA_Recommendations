"""Just a lazy shorcut to execute incremental refreshes

If the dataset hasn't been refreshed in ~3-4 days
it may be better to do a full clean scrape using 
BandScraper.py and afterwards SimilarScraper.py"""

from Scripts.BandUpdtr import main as Band
from Scripts.SimilarScraper import main as Sim

Band()
Sim()
try:
    from SQLpush import main as push
    push()
except ImportError:
    print('It is not supposed to work for you, dw')


