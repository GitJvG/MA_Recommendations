"""Generates candidates for the more in-depth Two-tower model to process
This script reduces the to be considered bands from ~200k to a thousand per user."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
from app.models import UserBandPreference, Item, users as Users
from Scripts.utils import load_config
import faiss
import numpy as np
from sklearn.preprocessing import OneHotEncoder

# Create a database engine
DATABASE_URI = load_config('SQL_Url')
ENGINE = create_engine(DATABASE_URI)
session = sessionmaker(bind=ENGINE)
SESSION = session()
MODEL_PATH ="Model"
model_name="wide_deep"

user_band_preference_data = SESSION.query(UserBandPreference).all()
user_dimensions = SESSION.query(Users).all()

# User preferences DataFrame
users_preference = pd.DataFrame(
    [(pref.user_id, pref.band_id, pref.liked) for pref in user_band_preference_data],
    columns=['user', 'item', 'label']
)
users_preference['label'] = users_preference['label'].replace(0, -1)

# User dimensions DataFrame
user_dimensions = pd.DataFrame(
    [(dim.id, dim.username, dim.Birthyear, dim.gender, dim.nationality, dim.genre1, dim.genre2, dim.genre3) for dim in user_dimensions],
    columns=['user', 'username', 'birthyear', 'gender', 'nationality', 'ugenre1', 'ugenre2', 'ugenre3']
)

# Prepare item DataFrame (you may need to query your items as needed)
detailed_band_data = SESSION.query(Item).filter(Item.score > 50).all()
items = pd.DataFrame(
    [(band.item, band.band_name, band.country, band.status, band.genre1, band.genre2, 
      band.genre3, band.genre4, band.theme1, band.theme2, band.theme3, band.theme4, band.score) for band in detailed_band_data],
    columns=['item', 'band_name', 'country', 'status', 'igenre1', 'igenre2', 'igenre3', 'igenre4',
             'theme1', 'theme2', 'theme3', 'theme4', 'score']
)

def create_item_embeddings(items):
    # Convert categorical features to one-hot encodings
    feature_columns = ['country', 'igenre1', 'igenre2',
                       'theme1', 'theme2', 'score']
    
    # Create a OneHotEncoder instance
    encoder = OneHotEncoder(handle_unknown='ignore')  # Set sparse=True to avoid memory issues during fitting
    
    # Fit and transform the specified columns
    item_embeddings = encoder.fit_transform(items[feature_columns])
    
    # Convert the sparse matrix to a dense NumPy array
    item_embeddings_dense = item_embeddings.toarray().astype('float32')
    
    return item_embeddings_dense

# Example usage
item_embeddings = create_item_embeddings(items)

# Display the shape of the item embeddings to understand how many features we've created
print("Shape of item embeddings:", item_embeddings.shape)

# Build FAISS index
dimension = item_embeddings.shape[1]  # Number of features (dimensions)
index = faiss.IndexFlatL2(dimension)  # Using L2 distance

# Add item embeddings to the index
index.add(item_embeddings)  

def generate_user_vector(user_id, user_dimensions, users_preference):
    """Create a user vector based on their preferences."""
    user_prefs = users_preference[users_preference['user'] == user_id]
    # Create a simple vector based on liked bands; you may want to create a more sophisticated vector
    liked_items = user_prefs[user_prefs['label'] == 1]['item'].values
    if len(liked_items) == 0:
        return None  # No preferences to generate a vector from
    
    # Get embeddings for liked items (this assumes your embeddings correspond to item indices)
    liked_embeddings = item_embeddings[items['item'].isin(liked_items)]
    user_vector = np.mean(liked_embeddings, axis=0)  # Average embedding of liked items
    return user_vector

def generate_candidates(user_id, k=5):
    """Generate candidate items for a user using FAISS."""
    user_vector = generate_user_vector(user_id, user_dimensions, users_preference)
    if user_vector is None:
        return []  # No candidates if no user preferences
    
    user_vector = user_vector.reshape(1, -1).astype('float32')  # Reshape for FAISS
    distances, indices = index.search(user_vector, k)  # Search for k nearest neighbors
    candidate_items = items.iloc[indices[0]]['item'].values  # Get candidate item IDs
    return candidate_items

# Example of generating candidates for a specific user
user_id=1
candidates = generate_candidates(user_id, k=1000)
print(f"Candidate items for user {user_id}:", candidates)
