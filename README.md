
# Metal-Archives Scraper and Recommender

## Access Scraped Datasets
You can download the full set of scraped datasets from the link below:

[Access Datasets on Google Drive](https://drive.google.com/drive/folders/1-0A9nAbVMZq02pou3Uu5EoDh-3gTgCTx?usp=sharing)

Please check the entries in `metadata.csv` for information on when the datasets were last updated.

## Overview
This project contains a collection of scripts designed to scrape various parts of the Metal-Archives (MA) website.

## Recommendation model
Candidates are generated based on user feedback (liking, disliking or bookmarking bands) and item features with Faiss-CPU. For every user multiple vectors are made using HDBSCAN to allow for multiple diverse or even contradicting tastes. FAISS is used to find the most similar bands based on these clustered vectors. Additionally the average jaccard similarity is calculated for each band and is combined with the faiss distance before a final rerank is used to generate the final candidates. The recommendation model is implemented in `MA_Scraper/Scripts/Add_Proc/candidates.py`.

## Website
A website is designed to use the underlaying scraped datasets and recommendation model along with Youtube scraping and embedding to deliver a responsive and functional music exploration platform.
