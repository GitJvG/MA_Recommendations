import json
import yaml
import os 
project_root = os.path.abspath(os.path.dirname(__file__))
config_yaml = os.path.join(project_root, 'config.yaml')
config_json = os.path.join(project_root, 'config.json')

def load_config(attribute, config_file=config_json):
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
        value = config.get(attribute)
        if value is None:
            raise ValueError(f"Missing required configuration: {attribute}")
        return value
    except FileNotFoundError:
        raise FileNotFoundError(f"The configuration file '{config_file}' was not found. Please create config.json following the format of the template.")
    except json.JSONDecodeError:
        raise ValueError(f"Error decoding the JSON in the configuration file '{config_file}'. Please create config.json following the format of the template.")
    except Exception as e:
        print(f"Error loading {config_file}: {e}")
        raise

with open(config_yaml, "r") as file:
    yaml_conf = yaml.safe_load(file)

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
            self.head = load_config('headers')
            self.cook = load_config('cookies')
            self.fire = load_config('Firefox_cookies.sqlite')

        except ValueError as e:
            print(f"Error: {e}")
            raise
        self.meta = yaml_conf['paths']['METADATA']
        self.simi = yaml_conf['paths']['MA_SIMILAR']
        self.disc = yaml_conf['paths']['MA_DISCOG']
        self.band = yaml_conf['paths']['MA_BANDS']
        self.deta = yaml_conf['paths']['MA_DETAILS']
        self.memb = yaml_conf['paths']['MA_MEMBER']
        self.label = yaml_conf['paths']['MA_LABEL']
        self.reviews = yaml_conf['paths']['MA_REVIEWS']

        self.meta_key = yaml_conf['keys'][self.meta]
        self.simi_key = yaml_conf['keys'][self.simi]
        self.disc_key = yaml_conf['keys'][self.disc]
        self.band_key = yaml_conf['keys'][self.band]
        self.deta_key = yaml_conf['keys'][self.deta]
        self.memb_key = yaml_conf['keys'][self.memb]
        self.label_key = yaml_conf['keys'][self.label]
        self.reviews_key = yaml_conf['keys'][self.reviews]

        self.url_modi = yaml_conf['urls']['MODIFIED']
        self.url_band = yaml_conf['urls']['BANDS']
        self.url_label = yaml_conf['urls']['LABELS']
        self.url_reviews = yaml_conf['urls']['REVIEWS']
        self.retries = yaml_conf['scraper']['RETRIES']
        self.delay = yaml_conf['scraper']['DELAY']
        self.batch_size = yaml_conf['scraper']['BATCH_SIZE']

        self.genre = yaml_conf['paths']['GENRE']
        self.hgenre = yaml_conf['paths']['HGENRE']
        self.prefix = yaml_conf['paths']['PREFIX']
        self.genres = yaml_conf['paths']['GENRES']
        self.theme = yaml_conf['paths']['THEME']
        self.dim_theme_dict = yaml_conf['paths']['DIM_THEME_DICT']
        self.themes = yaml_conf['paths']['THEMES']
        self.candidates = yaml_conf['paths']['CANDIDATES']

        self.binary = yaml_conf['word_processing']['BINARY_EXCEPTION']
        self.ternary = yaml_conf['word_processing']['TERNARY_EXCEPTION']
        self.unwanted = yaml_conf['word_processing']['UNWANTED_GENRE_WORDS']

        self.ytbackend = yaml_conf['website']['YOUTUBE_BACKEND']