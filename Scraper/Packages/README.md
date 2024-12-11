# Metal-Archives Scraper

## Access Scraped Datasets
You can download the full set of scraped datasets from the link below:

[Access Datasets on Google Drive](https://drive.google.com/drive/u/4/folders/1--6NBR1G9zF5A1Gc1Mbfemd7igncyvbM)

Please check the entries in `metadata.csv` for information on when the datasets were last updated.

## Overview
This project contains a collection of scripts designed to scrape various parts of the Metal-Archives (MA) website. The aim is to create a wrapper script that can scrape and parse just about anything from MA.

## Working Scrapers

- **BandScraper/BandParser → `MA_Bands`**:  
  Scrapes data for:
  - Band URL
  - Band Name
  - Country
  - Genre
  - Band ID
    - optionally Status

- **SimilarScraper → `MA_Similar`**:  
  Scrapes data for:
  - Similar Band ID
  - Similarity Score
  - Band ID

- **AlbumScraper → `MA_Discog`**:  
  Scrapes data for:
  - Album Name
  - Type
  - Year
  - Number of Reviews
  - Band ID

- **DetailScraper → `MA_Details`**:  
  Scrapes data for:
  - Country of origin
  - Location
  - Status
  - Formed in
  - Genre
  - Themes
  - Current label
  - Years active
  - Band ID
  - Last label

## Supporting Scripts

- **Refresh**:  
  Updates all final datasets incrementally by checking the last scraped date (stored in `metadata.csv`) and fetching new/modified bands from the recently added/modified page on Metal-Archives.

- **FullScraper**:  
  Fully scrapes Metallum from scratch. Starts by quickly scraping all bands and some basic data after which it scrapes corresponding band specific pages: Similar bands, Band details & Band discography.
  - Note: The initial basic data scraping is much more efficient and only takes about 17 minutes, the band specific page scraping takes about 16 hours for each distinct page. All in all it could take up to 48.5 hours to scrape all of metallum on these topics.

## In Progress

- **Data analysis**:
  Exploring, cleaning and transforming the data and creating a basic model that can predict what bands you might like given you like x band.
  
- **Optimizing scrapers**:
  Looking into options to speed up the scrapers and make the incremental refreshing more reliable. A particular issue seems to be the deletion of bands from mettalum, this currently isn't handled well resulting in datasets that aren't perfectly in sync with eachother and data on removed bands.

  



