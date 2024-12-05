import json
import yaml

def load_config(attribute, config_file='config.json'):
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

with open("config.yaml", "r") as file:
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
            self.binary = load_config('binary_exception')
            self.ternary = load_config('ternary_exception')
            self.unwanted = load_config('Unwanted_genre_words')
            self.genre = load_config('genre')
            self.prefix = load_config('prefix')
            self.genres = load_config('genres')
            self.theme = load_config('theme')
            self.dim_theme_dict = load_config("DIM_Theme_Dict")
            self.themes = load_config("themes")
            self.candidates = load_config('candidates')
            
        except ValueError as e:
            print(f"Error: {e}")
            raise
        self.meta = yaml_conf['paths']['METADATA']
        self.simi = yaml_conf['paths']['MA_SIMILAR']
        self.disc = yaml_conf['paths']['MA_DISCOG']
        self.band = yaml_conf['paths']['MA_BANDS']
        self.deta = yaml_conf['paths']['MA_DETAILS']
        self.memb = yaml_conf['paths']['MA_MEMBER']

        self.meta_key = yaml_conf['keys'][self.meta]
        self.simi_key = yaml_conf['keys'][self.simi]
        self.disc_key = yaml_conf['keys'][self.disc]
        self.band_key = yaml_conf['keys'][self.band]
        self.deta_key = yaml_conf['keys'][self.deta]
        self.memb_key = yaml_conf['keys'][self.memb]