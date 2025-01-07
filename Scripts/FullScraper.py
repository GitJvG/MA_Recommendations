from .Components import AlbumScraper, List_Scraper, SimilarScraper, DetailScraper
from Env import Env
env = Env.get_instance()

def FullScrape():
    List_Scraper.Parrallel_Alphabetical_List_Scraper(env.url_band)
    """BandScraper should take about 30 minutes"""
    print('Full list of bands scraped')
    AlbumScraper.main()
    """AlbumScraper may take up to 17 hours"""
    print('Full discography scraped')
    DetailScraper.main()
    """DetailScraper may take up to 17 hours"""
    print('Full details scraped')
    SimilarScraper.main()
    """SimilarScraper may take up to 17 hours"""
    print('Full Similar bands scraped')
    print('Done!')

if __name__ == "__main__":
    FullScrape()