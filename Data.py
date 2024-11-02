from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
from app.models import UserBandPreference, Item, users as Users
from Scripts.utils import load_config
from libreco.data import random_split
import numpy as np

# Create a database engine
DATABASE_URI = load_config('SQL_Url')
ENGINE = create_engine(DATABASE_URI)
session = sessionmaker(bind=ENGINE)
SESSION = session()
MODEL_PATH ="Model"


def load_data():
    user_band_preference_data = SESSION.query(UserBandPreference).all()
    user_dimensions = SESSION.query(Users).all()

    # User preferences
    users_preference = pd.DataFrame(
        [(pref.user_id, pref.band_id, pref.liked, pref.remind_me) for pref in user_band_preference_data],
        columns=['user', 'item', 'liked', 'remind']
    )
    users_preference = users_preference.fillna(0)
    users_preference['label'] = ((users_preference['liked'] == 1) | (users_preference['remind'] == 1)).astype(int)
    users_preference = users_preference[['user', 'item', 'label']]

    #User dimensions
    user_dimensions = pd.DataFrame(
        [(dim.id, dim.username, dim.Birthyear, dim.gender, dim.nationality, dim.genre1, dim.genre2, dim.genre3) for dim in user_dimensions],
        columns=['user', 'username', 'birthyear', 'gender', 'nationality', 'ugenre1', 'ugenre2', 'ugenre3']
    )
    return users_preference, user_dimensions

def load_items():
    detailed_band_data = SESSION.query(Item).all()
    items = pd.DataFrame(
        [(band.item, band.band_name, band.country, band.status, band.genre1, band.genre2, 
          band.genre3, band.genre4, band.theme1, band.theme2, band.theme3, band.theme4, band.score) for band in detailed_band_data],
        columns=['item', 'band_name', 'country', 'status', 'igenre1', 'igenre2', 'igenre3', 'igenre4',
                 'theme1', 'theme2', 'theme3', 'theme4', 'score']
    )
    
    #Fillna, applied on whole dataframe because of the large amount of columns that could contain nulls
    items.fillna("missing", inplace=True)
    return items

def preprocess_item_features(items):
    """Preprocess item features to create the feature array for the model."""
    # Step 2: Prepare item features
    item_features = items[[ 
        "country", "status",
        "igenre1", "igenre2", "igenre3",
        "theme1", "theme2", "theme3", "score"
    ]]

    # Step 3: Combine genre and theme columns for unique one-hot encoding
    genres = item_features[['igenre1', 'igenre2', 'igenre3']].astype(str).agg(lambda x: ','.join(x), axis=1)
    themes = item_features[['theme1', 'theme2', 'theme3']].astype(str).agg(lambda x: ','.join(x), axis=1)

    combined = pd.DataFrame({
        'combined_genres': genres,
        'combined_themes': themes
    })

    # Step 4: One-hot encoding for all categorical features
    item_features_encoded = pd.get_dummies(
        item_features.assign(combined_genres=combined['combined_genres'], combined_themes=combined['combined_themes']),
        columns=['country', 'status', 'combined_genres', 'combined_themes'],
        drop_first=True  # Optional: drop the first category to avoid dummy variable trap
    )

    # Step 5: Drop original genre and theme columns since they're now encoded
    item_features_encoded = item_features_encoded.drop(columns=['igenre1', 'igenre2', 'igenre3', 'theme1', 'theme2', 'theme3'])
    item_features_array = item_features_encoded.to_numpy(dtype=np.float32)
    item_ids = items['item']
    item_ids = item_ids.to_numpy(dtype=np.float64)

    return item_features_array, item_ids

def save_processed_items():
    items = load_items()
    item_features_array, item_ids = preprocess_item_features(items)
    np.save('Preprocessed_sets/preprocessed_item_features.npy', item_features_array)
    np.save('Preprocessed_sets/preprocessed_item_ids.npy', item_ids)

def load_item_arrays():
    item_features_array = np.load('Preprocessed_sets/preprocessed_item_features.npy')
    item_ids = np.load('Preprocessed_sets/preprocessed_item_ids.npy')
    return item_features_array, item_ids

if __name__ == "__main__":
    save_processed_items()