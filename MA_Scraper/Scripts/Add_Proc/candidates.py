from MA_Scraper.app import create_app, db
from MA_Scraper.app.models import Band, Genre, Hgenre, Discography as Discog, \
                        Theme, Users, Similar_band as Similar, Candidates, Member, Prefix
import pandas as pd
import faiss
from collections import defaultdict
import numpy as np
from datetime import datetime
from sqlalchemy import func
from MA_Scraper.Env import Env
from MA_Scraper.Scripts.SQL import refresh_tables
from hdbscan import HDBSCAN
from sklearn.decomposition import PCA

import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

env = Env.get_instance()

today = datetime.today()
faiss.omp_set_num_threads(8)

def one_hot_encode(df, columns):
    unique_categories = {col: np.unique(df[col]) for col in columns}
    category_to_index = {col: {category: idx for idx, category in enumerate(unique_categories[col])} 
                        for col in columns}
    encoded = []
    
    for col in columns:
        indices = np.array([category_to_index[col][val] for val in df[col]])

        one_hot = np.zeros((len(df), len(category_to_index[col])))
        one_hot[np.arange(len(df)), indices] = 1
        
        encoded.append(one_hot)
    
    return np.hstack(encoded)

def get_review_data():
    review_subquery = db.session.query(
        Discog.band_id,
        func.sum(Discog.review_count).label('total_review_count'),
        func.percentile_cont(0.5).within_group(Discog.review_score).label('median_score')
    ).filter(Discog.reviews.isnot(None)) \
     .group_by(Discog.band_id).subquery()
    
    result = db.session.query(
        review_subquery.c.band_id,
        review_subquery.c.total_review_count,
        review_subquery.c.median_score
    ).all()

    df = pd.DataFrame(result, columns=['band_id', 'review_count', 'median_score'])
    return df

def get_filtered_band_members(band_ids):
    members_of_target_bands = (
        db.session.query(Member.member_id)
        .join(Band, Band.band_id == Member.band_id)
        .filter(Band.band_id.in_(band_ids))
        .filter(Member.category.in_(['Current lineup', 'Past lineup']))
        .distinct()
        .all()
    )

    member_ids = {member_id for (member_id,) in members_of_target_bands}

    bands_with_shared_members = (
        db.session.query(Band.band_id)
        .join(Member, Band.band_id == Member.band_id)
        .filter(Member.member_id.in_(member_ids))
        .filter(Member.category.in_(['Current lineup', 'Past lineup']))
        .distinct()
        .all()
    )

    band_ids_with_shared_members = {band_id for (band_id,) in bands_with_shared_members}

    all_members_of_relevant_bands = (
        db.session.query(Band.band_id, Member.member_id)
        .join(Member, Band.band_id == Member.band_id)
        .filter(Band.band_id.in_(band_ids_with_shared_members))
        .filter(Member.category.in_(['Current lineup', 'Past lineup']))
        .all()
    )

    band_members = defaultdict(set)
    for band_id, member_id in all_members_of_relevant_bands:
        band_members[band_id].add(member_id)

    return band_members

def create_item():
    score_subquery = db.session.query(
    Similar.band_id,
    func.sum(func.distinct(Similar.score)).label('score')
    ).group_by(Similar.band_id).subquery()

    results = db.session.query(
        Band.band_id,
        Band.name.label('band_name'),
        Band.genre.label('band_genre'),
        Band.label,
        Band.country,
        Band.status,
        score_subquery.c.score,
        func.string_agg(func.distinct(Genre.name), ', ').label('genre_names'),
        func.string_agg(func.distinct(Hgenre.name), ', ').label('hybrid_genres'),
        func.string_agg(func.distinct(Theme.name), ', ').label('theme_names'),
        func.string_agg(func.distinct(Prefix.name), ', ').label('prefix_names')
    ).join(score_subquery, score_subquery.c.band_id == Band.band_id
    ).join(Band.genres, isouter=True
    ).join(Band.hgenres, isouter=True
    ).join(Band.themes, isouter=True
    ).join(Band.prefixes, isouter=True
    ).group_by(Band.band_id, Band.name, Band.genre, Band.label, Band.country, Band.status, score_subquery.c.score
    ).all()

    data = [
        {
            'band_id': band.band_id,
            'band_name': band.band_name,
            'band_genre': band.band_genre,
            'b_label': band.label,
            'country': band.country,
            'genre_names': band.genre_names,
            'hybrid_genres': band.hybrid_genres,
            'theme_names': band.theme_names,
            'prefix_names': band.prefix_names,
            'status': band.status,
            'score': band.score,
        }
        for band in results
    ]

    dataframe = pd.DataFrame(data)
    reviews = get_review_data()
    merged_dataframe = pd.merge(dataframe, reviews, on='band_id', how='left')

    merged_dataframe[['review_count', 'median_score']] = merged_dataframe[['review_count', 'median_score']].fillna(0)
    merged_dataframe[['prefix_names']] = merged_dataframe[['prefix_names']].fillna('Not available')
    merged_dataframe[['theme_names']] = merged_dataframe[['theme_names']].fillna('Not available')

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
    categorical_columns = ['country', 'theme_names', 'b_label', 'status', 'genre_names', 'hybrid_genres', 'prefix_names']
    numerical_columns = ['score', 'review_count', 'median_score']


    categorical_embeddings = one_hot_encode(item, categorical_columns)

    numerical_embeddings = ((item[numerical_columns] - np.mean(item[numerical_columns], axis=0)) / np.std(item[numerical_columns], axis=0)).to_numpy()

    item_embeddings_dense = np.hstack([
        categorical_embeddings.astype('float32'),
        numerical_embeddings.astype('float32')
    ])

    dimension = item_embeddings_dense.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(item_embeddings_dense)

    return index, item_embeddings_dense

def generate_user_vectors(user_id, users_preference, item_embeddings_array, item_df, min_cluster_size=None):
    user_prefs = users_preference[users_preference['user'] == user_id]
    liked_items = user_prefs[user_prefs['label'] == 1]['band_id'].values
    if len(liked_items) == 0:
        return []

    liked_embeddings_array = item_embeddings_array[item_df['band_id'].isin(liked_items)]

    pca = PCA(n_components=None)
    pca.fit(liked_embeddings_array)

    explained_variance_ratio = pca.explained_variance_ratio_
    cumulative_explained_variance = np.cumsum(explained_variance_ratio)
    n_components = np.argmax(cumulative_explained_variance >= 0.90)

    user_pca = PCA(n_components=n_components)
    user_pca.fit(liked_embeddings_array)
    try:
        processed_embeddings_array = user_pca.transform(liked_embeddings_array)
    except Exception as e:
        print(f"PCA failed for user {user_id}: {e}. Using original embeddings.")
        processed_embeddings_array = liked_embeddings_array

    
    min_cluster_size = int(len(processed_embeddings_array) * 0.05)
    if len(processed_embeddings_array) < min_cluster_size:
        return [np.mean(processed_embeddings_array, axis=0)]

    try:
        clusterer = HDBSCAN(min_cluster_size=min_cluster_size, min_samples=1, allow_single_cluster=True)
        cluster_labels = clusterer.fit_predict(processed_embeddings_array)
    except Exception as e:
        print(f"HDBSCAN clustering failed for user {user_id}: {e}. Returning single average as fallback.")
        return [np.mean(processed_embeddings_array, axis=0)]

    user_interest_vectors = []
    unique_clusters = np.unique(cluster_labels)
    
    processed_embeddings_array = user_pca.transform(liked_embeddings_array)
    for cluster_label in unique_clusters:
        if cluster_label != -1:
            cluster_items_embeddings = processed_embeddings_array[cluster_labels == cluster_label]
            if len(cluster_items_embeddings) > 0:
                interest_vector = np.mean(cluster_items_embeddings, axis=0)
                interest_vector = user_pca.inverse_transform(interest_vector).reshape(1, -1).flatten()
                user_interest_vectors.append(interest_vector)

    print(f"User shape before clustering", processed_embeddings_array.shape)
    print(f"unique_clusters {len(unique_clusters)}")
    print(f"user interest vectors {len(user_interest_vectors)}")
    if not user_interest_vectors:
        return [np.mean(processed_embeddings_array, axis=0)]

    return user_interest_vectors

def get_jaccard(band_members, liked_bands):
    candidate_bands = set(band_members.keys()) - set(liked_bands)
    jaccard_dict = defaultdict(dict)

    for liked_band in liked_bands:
        if liked_band not in band_members:
            continue
        members1 = band_members[liked_band]

        for candidate_band in candidate_bands:
            if candidate_band not in band_members:
                continue
            members2 = band_members[candidate_band]

            intersection = len(members1 & members2)
            union = len(members1 | members2)
            jaccard = intersection / union if union != 0 else 0

            jaccard_dict[liked_band][candidate_band] = jaccard

    return jaccard_dict

def generate_candidates(user_id, users_preference, index, item_df, item_embeddings_array, min_cluster_size, k):
    user_vectors = generate_user_vectors(user_id, users_preference, item_embeddings_array, item_df, min_cluster_size)
    interacted_bands = users_preference[users_preference['user'] == user_id]['band_id'].unique()
    interacted_bands = [int(x) for x in interacted_bands]
    #k2 = min(k + len(interacted_bands) * 2, k * 5)
    if not user_vectors:
        return []
    k_per_cluster = k // len(user_vectors)
    print(f"k_per_clusters {k_per_cluster}")
    all_faiss_results = []
    for user_vector in user_vectors:
        distances, faiss_indices = index.search(user_vector.reshape(1, -1).astype('float32'), k_per_cluster)
        for i in range(len(faiss_indices[0])):
            band_id = item_df.iloc[faiss_indices[0][i]]['band_id']
            distance = distances[0][i]
            all_faiss_results.append({'band_id': band_id, 'faiss_distance': distance})

    unique_candidates = {}
    for res in all_faiss_results:
        band_id = res['band_id']
        distance = res['faiss_distance']
        if band_id not in unique_candidates or distance < unique_candidates[band_id]['faiss_distance']:
            unique_candidates[band_id] = res

    faiss_list = list(unique_candidates.values())
    candidates = [info['band_id'] for info in faiss_list]
    faiss_distance_lookup = {info['band_id']: info['faiss_distance'] for info in faiss_list}

    band_members = get_filtered_band_members(interacted_bands)
    jaccard_dict = get_jaccard(band_members, interacted_bands)

    jaccard_candidates = defaultdict(lambda: {'total': 0, 'count': 0})
    for liked_band in interacted_bands:
        for candidate_band, score in jaccard_dict.get(liked_band, {}).items():
            jaccard_candidates[candidate_band]['total'] += score
            jaccard_candidates[candidate_band]['count'] += 1

    candidates.extend(list(jaccard_candidates.keys()))
    candidates = list(set(candidates))

    combined_scores = []
    max_faiss_dist = max(d['faiss_distance'] for d in faiss_list) if faiss_list else 1.0

    for candidate_band in candidates:
        faiss_dist = faiss_distance_lookup.get(candidate_band, float('inf'))
        faiss_normalized = min(faiss_dist / max_faiss_dist, 1.0)

        total_jaccard = jaccard_candidates[candidate_band]['total']
        count = jaccard_candidates[candidate_band]['count']
        avg_jaccard = total_jaccard / count if count > 0 else 0

        score = (faiss_normalized * 0.8) + ((1 - avg_jaccard) * 0.2)
        combined_scores.append({'band_id': candidate_band, 'score': score})


    combined_scores.sort(key=lambda x: x['score'])
    candidates = [item['band_id'] for item in combined_scores]

    known_candidates_re_ranked = []
    new_candidates_re_ranked = []

    for band_id in candidates:
        if band_id in interacted_bands:
            known_candidates_re_ranked.append(band_id)
        else:
            new_candidates_re_ranked.append(band_id)

    faiss_pool = []
    num_interacted_to_add = max(0, k - len(new_candidates_re_ranked))

    faiss_pool.extend(new_candidates_re_ranked)
    faiss_pool.extend(known_candidates_re_ranked[:num_interacted_to_add])

    return faiss_pool[:k]

def generate_candidates_for_all_users(users_preference, index, item, item_embeddings, min_cluster_size, k=1000):
    candidate_list = []

    for user_id in users_preference['user'].unique():
        candidates = generate_candidates(user_id, users_preference, index, item, item_embeddings, min_cluster_size, k)
        for candidate in candidates:
            candidate_list.append({'user_id': user_id, 'band_id': candidate})

    candidate_df = pd.DataFrame(candidate_list)
    return candidate_df

def main(min_cluster_size=None, k=400):
    app = create_app()
    with app.app_context():
        item = create_item()
        users_preference = create_user()
        index, item_embeddings = create_item_embeddings_with_faiss(item)
        candidate_frame = generate_candidates_for_all_users(users_preference, index, item, item_embeddings, min_cluster_size, k)
        candidate_frame.to_csv(env.candidates, index=False)

def complete_refresh(min_cluster_size=None, k=400):
    main(min_cluster_size, k)
    refresh_tables([Candidates])

if __name__ == '__main__':
    main()