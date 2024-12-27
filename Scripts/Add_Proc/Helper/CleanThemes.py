import sys
import os
import unicodedata
from nltk.stem import WordNetLemmatizer
import re

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(project_root)
from Env import Env
env = Env.get_instance()
lemmatizer = WordNetLemmatizer()

def normalize_to_ascii(theme):
    normalized = unicodedata.normalize('NFD', theme)
    ascii_text = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
        
    return ascii_text

def lemmatize_string(theme):
    return ' '.join([lemmatizer.lemmatize(word) for word in theme.split()])


def basic_processing(themes):
    theme = themes.lower()
    theme = re.sub(r'\(.*?\)', '', theme) # removes anything between parenthesis
    theme = re.sub(r'\s?/\s', '/', theme) # Removes spaces before and after '/'

    theme = normalize_to_ascii(theme)
    theme = re.sub(r'[^\x20-\x7E]', '', theme) # Removes non-ASCII
    theme = re.sub(r'\b(of|the|a|an|to)\b', '', theme) # remove common words
    theme = re.sub(r'\s+', ' ', theme) # Reduce consecutive spaces to one space

    theme = re.sub(r';', ',', theme) # Replace semicolon with a comma. Metallum uses this for time related distinctions but that isn't an important distinction for me.
    theme = re.sub(r'/', ',', theme) # Don't care for hybrid theme or very specific details. Can break context but still worth it given the messy format.
    theme = re.sub(r'[()]+', '', theme).strip() # Removes remaining parenthesis
    theme = re.sub(r'\band\b', ',', theme) # Replace 'and' with a comma
    theme = re.sub(r'\s*,\s*', ',', theme)
    theme = lemmatize_string(theme)

    return theme.strip() if theme else None
