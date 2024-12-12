import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from DataScripts.ThemeDict import update_pickle
from DataScripts.DIM_Theme import main as theme_main
from DataScripts.DIM_GenrePrefix import main as genre_main

def main():
    update_pickle() # Scans Details dataset for new themes, performs analysis and creates theme anchors with fuzzy matching.
    theme_main() # Generates theme.csv based on the updated pickle and indexes themes for each band into themes.csv
    genre_main() # Generates genre.csv and genres.csv

if __name__ == '__main__':
    main()