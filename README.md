# Metal-Archives Scraper

## Access Scraped Datasets
You can download the full set of scraped datasets from the following link:
[Access Datasets on Google Drive](https://drive.google.com/drive/folders/1aycZqvoVg2mDFkfQNaDga9_aistGJ-8T?usp=drive_link)

## Overview
This project contains a collection of scripts designed to scrape various parts of the Metal-Archives (MA) website. The aim is to create a wrapper script that can scrape and parse just about anything from MA.

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

- **Refresh**:  
  Updates all final datasets incrementally by checking the last scraped date (stored in `metadata.csv`) and fetching new 
  bands from the recently added page on Metal-Archives.
  -NOTE: Something doesn't work properly which causes duplicates. For the time being I've added a duplicates removing 
  function at the end, this is only a temporary fix.
  -NOTE: This script only checks the first recently added page on Metal-Archives. For this reason datasets should be kept up 
  to date as incremental updates won't see changes made longer than 3~5 days ago. I'll work on this eventually.

- **HTML_Scraper & utils**:  
  A collection of basic utility functions and functions for fetching and parsing HTML content.

## In Progress

- **Refresh**:
  Fixing the duplicates causing bug

- **Datasets**:
  Automated updating of the public datasets

## Future

- **Refresh**:
Rework the script so it can work for datasets that haven't been updated for more than a 3~5 days.

