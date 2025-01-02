
# Metal-Archives Scraper and Recommender

## Access Scraped Datasets
You can download the full set of scraped datasets from the link below:

[Access Datasets on Google Drive](https://drive.google.com/drive/folders/1-0A9nAbVMZq02pou3Uu5EoDh-3gTgCTx?usp=sharing)

Please check the entries in `metadata.csv` for information on when the datasets were last updated.

## Overview
This project contains a collection of scripts designed to scrape various parts of the Metal-Archives (MA) website. The aim is to create a wrapper script that can scrape and parse just about anything from MA.

## Scrapers

- **BandScraper → `MA_Bands.csv`**:  
  Scrapes data for:
  - Band URL
  - Band Name
  - Country
  - Genre
  - Band ID
    - optionally Status

- **SimilarScraper → `MA_Similar.csv`**:  
  Scrapes data for:
  - Similar Band ID
  - Similarity Score
  - Band ID

- **AlbumScraper → `MA_Discog.csv`**:  
  Scrapes data for:
  - Album Name
  - Type
  - Year
  - Review_Count
  - Review_Score
  - Band ID

- **DetailScraper → `MA_Details.csv, MA_Member.csv`**:  
Scrapes data for:
- **`MA_Details.csv`**  
   - Country of origin  
   - Location  
   - Status  
   - Formed in  
   - Genre  
   - Themes  
   - Label  
   - Years active  
   - Band ID  

- **`MA_Member.csv`**  
   - band_id  
   - member_id  
   - name  
   - role  
   - category

## Supporting Scripts

- **Refresh**:  
  Updates all final datasets incrementally by checking the last scraped datetime (stored in `metadata.csv`) and fetching new/modified bands from the recently modified page on Metal-Archives.

- **FullScraper**:  
  Fully scrapes Metallum from scratch. Starts by quickly scraping all bands and some basic data after which it scrapes corresponding band specific pages: Similar bands, Band details & Band discography.
  - Note: The initial basic data scraping is much more efficient and only takes about 17 minutes, the band specific page scraping takes about 16 hours for each distinct page. All in all it could take up to 48.5 hours to scrape all of metallum on these topics.

## Recommendation model
Candidates are generated based on user feedback and item features with Faiss-CPU. At it's core this is a Approximate nearest neighbor model. To further improve recommendations a deep-ranking model should be added to rank the generated candidates. The recommendation model is implemented in `Scripts/Add_Proc/candidates.py`.
