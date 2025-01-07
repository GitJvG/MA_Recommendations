from .Components import AlbumScraper, List_Scraper, SimilarScraper, DetailScraper
from Env import Env
env = Env.get_instance()

def FullScrape():
    List_Scraper.Parrallel_Alphabetical_List_Scraper(env.url_band)
    print('Full list of bands scraped')

    List_Scraper.Parrallel_Alphabetical_List_Scraper(env.url_label)
    print('Full list of labels scraped')
    
    """The following scrapers may take up to 17 hours EACH as of 2025-01"""
    print('Starting discography scrape, this and the following scrapers combined may take several days to complete')
    AlbumScraper.main()
    print('Full discography scraped')

    DetailScraper.main()
    print('Full details scraped')

    SimilarScraper.main()
    print('Full Similar bands scraped')

    print('Done!')

if __name__ == "__main__":
    FullScrape()