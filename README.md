# Metal-Archives Scraper

## Overview
This project contains a collection of scripts designed to scrape various parts of the Metal-Archives (MA) website. Each script targets specific sections of the website, and although the current setup is still evolving, the aim is to synchronize all datasets before merging scripts to simplify the process.

## Working Scrapers and Parsers

- **BandScraper/BandParser → `MA_Bands`**:  
  Scrapes data for:
  - Band URL
  - Band Name
  - Country
  - Genre
  - Status
  - Band ID

- **SimilarScraper → `MA_Similar`**:  
  Scrapes data for:
  - Band URL
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

- **ThemeScraper → `MA_Lyrics`**:  
  Scrapes data for:
  - Lyrical Themes
  - Band ID

## Supporting Scripts

- **BandUpdtr**:  
  Updates `MA_Bands` incrementally by checking the last scraped date (stored in `metadata.csv`) and fetching new bands from the recently added page on Metal-Archives.

- **HTML_Scraper**:  
  Contains utility functions for fetching and parsing HTML content that can be reused across various scrapers.

- **utils**:  
  A collection of basic utility functions.

## In Progress

- **Wrapping Script**:  
  A unified script that combines the functionality of individual scrapers for more streamlined data collection.

- **Dataset Updates**:  
  Bringing all scraped datasets up to date and making them available for use.

- **Improving Incremental Updates**:  
  Enhancing the incremental updating script for better efficiency and accuracy.

