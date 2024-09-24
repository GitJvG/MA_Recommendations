"""Incremental updater is only based on day number as of now, this will be updated later. Should work fine for the rest of the current month."""

from dotenv import load_dotenv
import os
load_dotenv()

from BandUpdtr import main as Band_and_Themes 
Band_and_Themes() #Updates both MA_Bands and MA_Lyrics. Together reduces the amount of requests needed. Also saves a list of edited Band IDs in Temp/MA_Changes.csv
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
