"""Script to further process genres and themes. It also generates candidates for website users."""
from MA_Scraper.Scripts.Add_Proc.ThemeDict import update_pickle as Theme_Anchors
from MA_Scraper.Scripts.Add_Proc.DIM_Theme import main as theme_main
from MA_Scraper.Scripts.Add_Proc.DIM_GenrePrefix import main as genre_main
from MA_Scraper.Scripts.Add_Proc.candidates import main as canidates

def main():
    Theme_Anchors() # Scans Details dataset for new themes, performs analysis and creates theme anchors with fuzzy matching.
    theme_main() # Generates theme.csv based on the updated pickle and indexes themes for each band into themes.csv
    genre_main() # Generates genre.csv and genres.csv
    canidates() # Generate user-specific candidates

if __name__ == '__main__':
    main()