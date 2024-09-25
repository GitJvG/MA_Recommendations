# Metal-Archives Scraper

## Access Scraped Datasets
You can download the full set of scraped datasets from the link below:

[Access Datasets on Google Drive](https://drive.google.com/drive/u/4/folders/1--6NBR1G9zF5A1Gc1Mbfemd7igncyvbM)

Please check the entries in `metadata.csv` for information on when the datasets were last updated.

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
  Updates all final datasets incrementally by checking the last scraped date (stored in `metadata.csv`) and fetching new/modified bands from the recently added/modified page on Metal-Archives.

  **NOTES**:  
  - In the current state it will only work for the remainder of September. A fix will be implemented soon.

- **HTML_Scraper & utils**:  
  A collection of basic utility functions and functions for fetching and parsing HTML content.

## In Progress

- **Data analysis**
  Exploring, cleaning and transforming the data and creating a basic model that can predict what bands you might like given you like x band.

- **Mass scraping wrapper**
  Whilst the current scripts allow you to scrape nearly all masterdata on bands, there is no wrapper script that executes them all in the right order.

- **Clearer script hierarchy
  I aim to present two wrapper scripts: one that scrapes everything and one that can do incremental updates on your datasets after you've done a full scrape/imported the public datasets from google drive.
  The scripts for scraping individual sections will remain available but should be less prominent.
  



