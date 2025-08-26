import json
import os 
project_root = os.path.abspath(os.path.dirname(__file__))

config_yaml = os.path.join(project_root, 'config.yaml')
config_json = os.path.join(project_root, 'config.json')

def dpath(file):
    return os.path.join(project_root, 'Datasets', file)

def load_config(attribute, config_file=config_json):
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
        value = config.get(attribute)
        if value is None:
            raise ValueError(f"Missing required configuration: {attribute}")
        return value
    except Exception as e:
        print(f"Error loading {config_file}: {e}")
        raise

class Env:
    _instance = None
    
    @staticmethod
    def get_instance():
        if Env._instance is None:
            Env._instance = Env()
        return Env._instance

    def __init__(self):
        if Env._instance is not None:
            raise Exception("This is a singleton!")
        
        try:
            self.head =         load_config('headers')
            self.cook =         load_config('cookies')
            self.fire =         load_config('Firefox_cookies.sqlite')

        except ValueError as e:
            print(f"Error: {e}")
            raise

        self.meta = dpath('metadata.csv')
        self.simi = dpath('MA_Similar.csv')
        self.disc = dpath('MA_Discog.csv')
        self.band = dpath('MA_Bands.csv')
        self.deta = dpath('MA_Details.csv')
        self.memb = dpath('MA_Member.csv')
        self.label = dpath('MA_Label.csv')
        self.reviews = dpath('MA_Reviews.csv')

        self.fband = dpath('band.csv')
        self.genre = dpath('genre.csv')
        self.prefix = dpath('prefix.csv')
        self.genres = dpath('genres.csv')
        self.band_logo = dpath('band_logo.csv')
        self.band_genres = dpath('band_genres.csv')
        self.band_prefixes = dpath('band_prefixes.csv')
        self.theme = dpath('theme.csv')
        self.dim_theme_dict = dpath('Temp/DIM_Theme_Dict.pkl')
        self.themes = dpath('themes.csv')
        self.candidates = dpath('candidates.csv')

        self.meta_key = ['name']
        self.simi_key = ['band_id', 'similar_id']
        self.disc_key = ['album_id', 'band_id']
        self.band_key = ['band_id']
        self.deta_key = ['band_id']
        self.memb_key = ['band_id', 'member_id']
        self.label_key = ['label_id']
        self.reviews_key = ['album_id', 'review_id']

        self.url_modi =     "https://www.metal-archives.com/archives/ajax-band-list/by/modified/selection/"
        self.url_band =     "https://www.metal-archives.com/browse/ajax-letter/json/1/l/"
        self.url_label =    "https://www.metal-archives.com/label/ajax-list/json/1/l/"
        self.url_reviews =  "https://www.metal-archives.com/reviews/1/1/"
        self.url_similar =  "https://www.metal-archives.com/band/ajax-recommendations/id/"
        self.url_disc1 =    "https://www.metal-archives.com/band/discography/id/"
        self.url_disc2 =    "/tab/all"
        self.url_deta =     "https://www.metal-archives.com/bands/id/"

        self.retries =      10
        self.delay =        0.3
        self.batch_size =   1000

        self.ytbackend =    "SCRAPE"
        # Backend for importing playlist data and embedding videos. Options: "YTDLP", "YTAPI" and "SCRAPE". 
        # YTAPI: requires own API key, free key has limited free recourses per day
        # YTDLP: No setup required and unlimited usage, same search results as YTAPI.
        # SCRAPE: Best search results as it includes playlists and embeds them as a video list that automatically plays all videos. 
