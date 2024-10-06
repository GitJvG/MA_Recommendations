from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
from app.models import UserBandPreference, Item, users as Users
from Scripts.utils import load_config
import random
from libreco.data import random_split

# Create a database engine
DATABASE_URI = load_config('SQL_Url')
ENGINE = create_engine(DATABASE_URI)
session = sessionmaker(bind=ENGINE)
SESSION = session()
MODEL_PATH ="Model"
model_name="wide_deep"

def load_data():
    # Load data from your tables
    user_band_preference_data = SESSION.query(UserBandPreference).all()
    user_dimensions = SESSION.query(Users).all()

    # User preferences
    users_preference = pd.DataFrame(
        [(pref.user_id, pref.band_id, pref.liked) for pref in user_band_preference_data],
        columns=['user', 'item', 'label']
    )
    users_preference['label'] = users_preference['label'].replace(0, -1)
    users_preference = users_preference.fillna(0)
    #Subset for faster calculations
    interacted_band_ids = set(users_preference['item'])

    #User dimensions
    user_dimensions = pd.DataFrame(
        [(dim.id, dim.username, dim.Birthyear, dim.gender, dim.nationality, dim.genre1, dim.genre2, dim.genre3) for dim in user_dimensions],
        columns=['user', 'username', 'birthyear', 'gender', 'nationality', 'ugenre1', 'ugenre2', 'ugenre3']
    )
    #Only query ID's until the subset details are needed for are defined.
    band_ids = SESSION.query(Item.item).filter(Item.item.notin_(interacted_band_ids)).all()
    band_ids = pd.DataFrame(band_ids, columns=['item'])
    

    #Add randomly selected negatives for new bands to be recommended.
    negative_samples = generate_negative_samples(users_preference, band_ids)
    #Complete list of user interactions + neg samples
    users = pd.concat([users_preference, negative_samples], ignore_index=True)
    #Add user dimensions to complete user interaction list
    users = users.merge(user_dimensions, on='user')

    #Only query details for interactions and negative samples
    detailed_band_data = SESSION.query(Item).filter(Item.item.in_(users['item'])).all()
    items = pd.DataFrame(
        [(band.item, band.band_name, band.country, band.status, band.genre1, band.genre2, 
          band.genre3, band.genre4, band.theme1, band.theme2, band.theme3, band.theme4, band.score) for band in detailed_band_data],
        columns=['item', 'band_name', 'country', 'status', 'igenre1', 'igenre2', 'igenre3', 'igenre4',
                 'theme1', 'theme2', 'theme3', 'theme4', 'score']
    )
    
    #Fillna, applied on whole dataframe because of the large amount of columns that could contain nulls
    items.fillna("missing", inplace=True)

    #Create one big dataset
    data = users.merge(items, on='item')
    print(data.info())

    train_data, eval_data = random_split(data, multi_ratios=[0.8, 0.2], seed=42)

    # Sparse columns (categorical with many unique values)
    sparse_col = [
        "nationality", "band_name", "country", "status",
        "ugenre1", "ugenre2", "ugenre3",
        "igenre1", "igenre2", "igenre3", "igenre4",
        "theme1", "theme2", "theme3", "theme4", "gender"
    ]
    
    # Dense columns (numerical with fewer unique values)
    dense_col = ["birthyear", "score"]  # Optional to derive 'age'

    # User columns (user attributes)
    user_col = [
        "birthyear", "gender", "nationality",
        "ugenre1", "ugenre2", "ugenre3"
    ]

    # Item columns (item attributes)
    item_col = [
        "band_name", "country", "status",
        "igenre1", "igenre2", "igenre3", "igenre4",
        "theme1", "theme2", "theme3", "theme4", "score"
    ]

    return train_data, user_col, item_col, sparse_col, dense_col, eval_data

def generate_negative_samples(users, items):
    """Generate negative samples for each user. For each user, select random bands they haven't interacted with and assign label=0."""
    negative_samples = []
    all_bands = set(items['item'])
    for user_id in users['user'].unique():
        interacted_bands = set(users[users['user'] == user_id]['item'])
        non_interacted_bands = all_bands - interacted_bands

        sampled_negative_bands = random.sample(non_interacted_bands, min(len(non_interacted_bands), 2 * len(interacted_bands)))
        
        for band in sampled_negative_bands:
            negative_samples.append((user_id, band, 0))  # label=0 for negative samples

    negative_samples_df = pd.DataFrame(negative_samples, columns=['user', 'item', 'label'])
    return negative_samples_df