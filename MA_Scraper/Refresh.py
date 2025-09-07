from MA_Scraper.Scripts.Refresh import refresh as Refresh_Source_Datasets
from MA_Scraper.Scripts.M_Datasets import main as Refresh_Processed_Datasets
from MA_Scraper.Scripts.SQL import refresh_tables as Push_To_Sql
from MA_Scraper.Scripts.Add_Proc.candidates import main as canidates
from MA_Scraper.models import Candidates

def main():
    Refresh_Source_Datasets()
    Refresh_Processed_Datasets()
    Push_To_Sql()
    
    canidates()
    Push_To_Sql([Candidates])

if __name__ == '__main__':
    main()