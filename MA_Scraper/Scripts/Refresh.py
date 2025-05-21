"""Incremental updater scrapes based on year, month, and time. Last scraped time is only updated at the end of a successful refresh"""
from MA_Scraper.Scripts.utils import update_metadata, get_time, get_common_date
from MA_Scraper.Env import Env
from MA_Scraper.Scripts.Components.Helper.ModifiedUpdater import Modified_based_list
from MA_Scraper.Scripts.Components.List_Scraper import Parrallel_Alphabetical_List_Scraper
from MA_Scraper.Scripts.Components.SimilarScraper import refresh as ReSim
from MA_Scraper.Scripts.Components.AlbumScraper import refresh as ReAlb
from MA_Scraper.Scripts.Components.DetailScraper import refresh as ReDet

env = Env.get_instance()

def refresh(SQL=False):
    # Time handling is done at this level to ensure consistency between files on consecutive refreshes.
    # Time is set before all scraping, leading to some repeats on consecutive refreshes, this is done to ensure data-integrity and consistency.
    time = get_time()
    csv_files = [env.band, env.label, env.simi, env.disc, env.deta, env.meta, env.memb]
    Parrallel_Alphabetical_List_Scraper(env.url_band, type='band')
    Parrallel_Alphabetical_List_Scraper(env.url_label, type='label')

    # Use the same modified bands list for all files if all files share the same last scraping date
    common_date = get_common_date()
    if common_date:
        band_ids_to_scrape = Modified_based_list(common_date, False)
    else: band_ids_to_scrape = None

    ReSim(band_ids_to_scrape=band_ids_to_scrape)
    ReAlb(band_ids_to_scrape=band_ids_to_scrape)
    ReDet(band_ids_to_scrape=band_ids_to_scrape)
    for csv in csv_files: update_metadata(csv)
    update_metadata(time=time)
    if SQL:
        from MA_Scraper.Scripts.SQL import refresh_tables
        refresh_tables()

if __name__ == "__main__":
    refresh(SQL=True)