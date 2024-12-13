import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from app import create_app, db
from app.models import band as Band, genres as Genres, genre as Genre, themes as Themes, discography as Discog, \
                        theme as Theme, details as Details, user as User, users as Users, similar_band as Similar
import pandas as pd
import faiss
import numpy as np
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from datetime import datetime
from sqlalchemy import func
from collections import defaultdict
from Env import Env
env = Env.get_instance()

today = datetime.today()

def get_review_data():
    # Aggregate review counts and scores in the query itself
    review_subquery = db.session.query(
        Discog.band_id,
        func.sum(Discog.review_count).label('total_review_count'),
        func.percentile_cont(0.5).within_group(Discog.review_score).label('median_score')
    ).filter(Discog.reviews.isnot(None)) \
     .group_by(Discog.band_id).subquery()
    
    # Join with the main query to get additional details
    result = db.session.query(
        review_subquery.c.band_id,
        review_subquery.c.total_review_count,
        review_subquery.c.median_score
    ).all()

    # Return as DataFrame directly
    df = pd.DataFrame(result, columns=['band_id', 'review_count', 'median_score'])
    return df

def create_item():
    score_subquery = db.session.query(
    Similar.band_id,
    func.sum(func.distinct(Similar.score)).label('score')
    ).group_by(Similar.band_id).subquery()
    
    results = db.session.query(
        Band.band_id,
        Band.name.label('band_name'),
        Band.genre.label('band_genre'),
        Details.label,
        Details.country,
        Details.status,
        score_subquery.c.score,
        func.string_agg(func.distinct(Genre.name), ', ').label('genre_names'),
        func.string_agg(func.distinct(Theme.name), ', ').label('theme_names'),
    ).join(
        Details, Band.band_id == Details.band_id
    ).join(
        score_subquery, score_subquery.c.band_id == Band.band_id
    ).join(
        Genres, Band.band_id == Genres.band_id
    ).join(
        Genre, Genre.genre_id == Genres.item_id).filter(Genres.type == 'genre'
    ).join(
        Themes, Band.band_id == Themes.band_id
    ).join(
        Theme, Themes.theme_id == Theme.theme_id
    ).group_by(
        Band.band_id, Band.name, Band.genre, Details.label, Details.country, Details.status, score_subquery.c.score
    ).all()

    # Build the final data list
    data = [
        {
            'band_id': band.band_id,
            'band_name': band.band_name,
            'band_genre': band.band_genre,
            'b_label': band.label,
            'country': band.country,
            'genre_names': band.genre_names,
            'theme_names': band.theme_names,
            'status': band.status,
            'score': band.score,
        }
        for band in results
    ]

    dataframe = pd.DataFrame(data)
    reviews = get_review_data()
    merged_dataframe = pd.merge(dataframe, reviews, on='band_id', how='left')
    return merged_dataframe

def create_user():
    user_band_preference_data = db.session.query(Users).all()

    users_preference = pd.DataFrame(
        [(pref.user_id, pref.band_id, pref.liked, pref.remind_me, pref.liked_date, pref.remind_me_date) for pref in user_band_preference_data],
        columns=['user', 'band_id', 'liked', 'remind_me', 'liked_date', 'remind_me_date']
    )

    users_preference['label'] = (users_preference['liked'] == 1) | (users_preference['remind_me'] == 1).astype(int)
    users_preference['relevance'] = np.minimum(
    (today - users_preference['liked_date']).abs(),
    (today - users_preference['remind_me_date']).abs())

    users_preference = users_preference[['user', 'band_id', 'relevance', 'label']]

    return users_preference

def create_item_embeddings_with_faiss(item):
    categorical_columns = ['country', 'band_genre', 'theme_names', 'b_label', 'status', 'genre_names']
    numerical_columns = ['score']

    encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    categorical_embeddings = encoder.fit_transform(item[categorical_columns])

    scaler = StandardScaler()
    numerical_embeddings = scaler.fit_transform(item[numerical_columns])

    item_embeddings_dense = np.hstack([
        categorical_embeddings.astype('float32'),
        numerical_embeddings.astype('float32')
    ])

    dimension = item_embeddings_dense.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(item_embeddings_dense)

    return index, item_embeddings_dense

def generate_user_vector(user_id, users_preference, item_embeddings, item):
    user_prefs = users_preference[users_preference['user'] == user_id]
    liked_items = user_prefs[user_prefs['label'] == 1]['band_id'].values
    if len(liked_items) == 0:
        return []
    
    liked_embeddings = item_embeddings[item['band_id'].isin(liked_items)]

    user_vector = np.mean(liked_embeddings, axis=0)
    return user_vector

def generate_candidates(user_id, users_preference, index, itme, item_embeddings, k):
    # NOTE: Potential bottleneck due to searching large space and post-filtering.
    # Pre-filtering requires creating a faiss index for each user which seems less efficient.
    user_vector = generate_user_vector(user_id, users_preference, item_embeddings, itme)

    interacted_bands = users_preference[users_preference['user'] == user_id]['band_id'].values

    k = k + len(interacted_bands)

    distances, indices = index.search(user_vector.reshape(1, -1).astype('float32'), k)
    candidate_bands = itme.iloc[indices[0]]['band_id'].values

    filtered_candidates = [band for band in candidate_bands if band not in interacted_bands]

    return filtered_candidates

def generate_candidates_for_all_users(users_preference, index, item, item_embeddings, k=1000):
    candidate_list = []

    for user_id in users_preference['user'].unique():
        candidates = generate_candidates(user_id, users_preference, index, item, item_embeddings, k)
        for candidate in candidates:
            candidate_list.append({'user_id': user_id, 'band_id': candidate})

    candidate_df = pd.DataFrame(candidate_list)
    return candidate_df

def main():
    app = create_app()
    with app.app_context():
        create_item().to_csv('item.csv', index=False)
        item = pd.read_csv('item.csv')
        users_preference = create_user()
        index, item_embeddings = create_item_embeddings_with_faiss(item)
        candidate_frame = generate_candidates_for_all_users(users_preference, index, item, item_embeddings, 1000)
        candidate_frame.to_csv(env.candidates, index=False)

if __name__ == '__main__':
    main()