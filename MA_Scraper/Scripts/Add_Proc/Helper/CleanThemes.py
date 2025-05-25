import unicodedata
from nltk.stem import WordNetLemmatizer, PorterStemmer, LancasterStemmer
import re
import pandas as pd

from MA_Scraper.Env import Env
env = Env.get_instance()
lemmatizer = WordNetLemmatizer()
stemmer = PorterStemmer()

def normalize_to_ascii(theme):
    normalized = unicodedata.normalize('NFD', theme)
    ascii_text = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
        
    return ascii_text

def basic_processing(theme):
    theme = theme.lower()
    theme = re.sub(r'\(.*?\)', '', theme) # removes anything between parenthesis
    theme = re.sub(r'\s?/\s', '/', theme) # Removes spaces before and after '/'

    theme = normalize_to_ascii(theme)
    theme = re.sub(r'[^\x20-\x7E]', '', theme) # Removes non-ASCII
    theme = re.sub(r'\b(of|the|a|an|to)\b', '', theme) # remove common words
    #theme = re.sub(r'-', ' ', theme)
    theme = re.sub(r'\s+', ' ', theme) # Reduce consecutive spaces to one space

    theme = re.sub(r';', ',', theme) # Replace semicolon with a comma. Metallum uses this for time related distinctions but that isn't an important distinction for me.
    theme = re.sub(r'/', ',', theme) # Don't care for hybrid theme or very specific details. Can break context but still worth it given the messy format.
    theme = re.sub(r'[()]+', '', theme).strip() # Removes remaining parenthesis
    theme = re.sub(r'\band\b', ',', theme) # Replace 'and' with a comma
    theme = re.sub(r'\s*,\s*', ',', theme)
    themes = []
    for theme in theme.split(','):
        if not theme:
            continue
        longest_word = max(theme.split(), key=len)
        if not longest_word:
            continue

        lemmatized_word = lemmatizer.lemmatize(longest_word)
        stemmed_word = stemmer.stem(lemmatized_word)
        themes.append(stemmed_word)

    theme = ','.join(themes) if themes else None
    return theme.strip() if theme else None