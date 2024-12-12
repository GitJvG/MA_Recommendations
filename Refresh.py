from Scripts.Refresh import refresh as Refresh_Source_Datasets
from DataScripts.M_Datasets import main as Refresh_Processed_Datasets
from DataScripts.SQL import refresh_tables as Push_To_Sql

def main():
    Refresh_Source_Datasets()
    Refresh_Processed_Datasets()
    Push_To_Sql()

if __name__ == '__main__':
    main()