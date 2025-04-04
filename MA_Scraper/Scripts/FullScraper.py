from MA_Scraper.Scripts.Components import AlbumScraper, List_Scraper, SimilarScraper, DetailScraper
from MA_Scraper.Env import Env
env = Env.get_instance()

def FullScrape():
    List_Scraper.Parrallel_Alphabetical_List_Scraper(env.url_band)
    List_Scraper.Parrallel_Alphabetical_List_Scraper(env.url_label)
    AlbumScraper.main()
    DetailScraper.main()
    SimilarScraper.main()
    print('Done!')

if __name__ == "__main__":
    FullScrape()