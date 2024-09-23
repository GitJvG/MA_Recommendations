"""Just a lazy shorcut to execute incremental refreshes

If the dataset hasn't been refreshed in ~3-4 days
it may be better to do a full clean scrape using 
BandScraper.py and afterwards SimilarScraper.py"""

from dotenv import load_dotenv
from utils import distinct
import os
load_dotenv()

file_paths = {
    os.getenv('BANDPAR'): ['Band ID'],                       # Unique by Band ID
    os.getenv('SIMBAN'): ['Band ID', 'Similar Artist ID'],  # Unique by Band ID & Similar Artist ID
    os.getenv('BANDIS'): ['Album Name', 'Type', 'Year', 'Band ID'],  # Unique by Album Name, Type, Year, Band ID
    os.getenv('BANLYR'): ['Band ID'],                        # Unique by Band ID
}

from BandUpdtr import main as Band_Themes 
Band_Themes() #Updates both MA_Bands and MA_Lyrics. Together reduces the amount of requests needed. Also saves a list of edited Band IDs in Temp/MA_Changes.csv
from SimilarScraper import refresh as ReSim 
ReSim() #Fetches all similar band data on Band IDs in Temp/MA_Changes.csv
from AlbumScraper import refresh as ReAlb
ReAlb() #Fetches all discograpghy band data on Band IDs in Temp/MA_Changes.csv
TEMP = os.getenv('TEMPID')
if os.path.exists(TEMP): #Deletes temp file created by BandUpdtr
    os.remove(TEMP)  # Delete the file
    print(f"{TEMP} has been deleted.")
else:
    print(f"{TEMP} does not exist.")
distinct(file_paths)
