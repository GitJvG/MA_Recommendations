import os
import json
from dotenv import load_dotenv

load_dotenv()

def load_config(attribute):
    """Attribute as Cookies or Headers"""
    with open('config.json', 'r') as file:
        config = json.load(file)
        
    return config.get(attribute)

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
        self.cook = load_config('Cookies')
        self.head = load_config('Headers')
        self.meta = os.getenv('METADATA')
        self.simi = os.getenv('SIMBAN')
        self.disc = os.getenv('BANDIS')
        self.band = os.getenv('BANDPAR')
        self.deta = os.getenv('DETAIL')
        self.memb = os.getenv('MEMBER')
        self.url_modi= os.getenv('URLMODIFIED')
        self.url_band= os.getenv('URLBANDS')
        self.retries = load_config('Retries')
        self.delay = load_config('Delay')

env = Env.get_instance()