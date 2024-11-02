from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
from app.models import UserBandPreference, Item, users as Users
from Scripts.utils import load_config
import faiss
import numpy as np
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Create a database engine
DATABASE_URI = load_config('SQL_Url')
ENGINE = create_engine(DATABASE_URI)
session = sessionmaker(bind=ENGINE)
SESSION = session()

# Load user band preference and user dimension data from the database
user_band_preference_data = SESSION.query(UserBandPreference).all()
user_dimensions_data = SESSION.query(Users).all()

# User preferences DataFrame
users_preference = pd.DataFrame(
    [(pref.user_id, pref.band_id, pref.liked) for pref in user_band_preference_data],
    columns=['user', 'item', 'label']
)
users_preference['label'] = users_preference['label'].replace(0, -1)

# User dimensions DataFrame
user_dimensions = pd.DataFrame(
    [(dim.id, dim.username, dim.Birthyear, dim.gender, dim.nationality, dim.genre1, dim.genre2, dim.genre3) for dim in user_dimensions_data],
    columns=['user', 'username', 'birthyear', 'gender', 'nationality', 'ugenre1', 'ugenre2', 'ugenre3']
)

# Prepare item DataFrame. Limit to items with score > 50.
detailed_band_data = SESSION.query(Item).filter(Item.score > 50).all()
items = pd.DataFrame(
    [(band.item, band.band_name, band.country, band.status, band.genre1, band.genre2, 
      band.genre3, band.genre4, band.theme1, band.theme2, band.theme3, band.theme4, band.score) for band in detailed_band_data],
    columns=['item', 'band_name', 'country', 'status', 'igenre1', 'igenre2', 'igenre3', 'igenre4',
             'theme1', 'theme2', 'theme3', 'theme4', 'score']
)

# Function to create item embeddings
def create_item_embeddings(items):
    categorical_columns = ['country', 'igenre1', 'igenre2', 'theme1', 'theme2']
    numerical_columns = ['score']

    encoder = OneHotEncoder(handle_unknown='ignore')
    categorical_embeddings = encoder.fit_transform(items[categorical_columns])

    scaler = StandardScaler()
    numerical_embeddings = scaler.fit_transform(items[numerical_columns].values.reshape(-1, 1))

    item_embeddings_dense = np.hstack([
        categorical_embeddings.toarray().astype('float32'),
        numerical_embeddings.astype('float32')
    ])

    return item_embeddings_dense

# Generate item embeddings
item_embeddings = create_item_embeddings(items)

# Build FAISS index
dimension = item_embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(item_embeddings)

# Function to generate a user vector based on preferences
def generate_user_vector(user_id, user_dimensions, users_preference):
    user_prefs = users_preference[users_preference['user'] == user_id]
    liked_items = user_prefs[user_prefs['label'] == 1]['item'].values
    if len(liked_items) == 0:
        return None  # No preferences to generate a vector from

    liked_embeddings = item_embeddings[items['item'].isin(liked_items)]
    user_vector = np.mean(liked_embeddings, axis=0)
    return user_vector

# Function to generate candidate items for a user
def generate_candidates(user_id, k=1000):
    user_vector = generate_user_vector(user_id, user_dimensions, users_preference)
    if user_vector is None:
        return []  # No candidates if no user preferences

    user_vector = user_vector.reshape(1, -1).astype('float32')
    distances, indices = index.search(user_vector, k)
    candidate_items = items.iloc[indices[0]]['item'].values
    return candidate_items

# Generate candidates for each user
def generate_candidates_for_all_users(k=3000):
    candidate_list = []

    # Loop through all users in the user_dimensions DataFrame
    for user_id in user_dimensions['user'].unique():
        candidates = generate_candidates(user_id, k)
        for candidate in candidates:
            candidate_list.append({'user_id': user_id, 'item_id': candidate})

    # Convert to DataFrame
    candidate_df = pd.DataFrame(candidate_list)

    return candidate_df