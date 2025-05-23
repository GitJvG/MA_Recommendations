from MA_Scraper.app import create_app, db
from MA_Scraper.app.models import Band, Genre, Hgenre, Discography, \
                        Theme, Users, Similar_band, Candidates, Member, Prefix
from MA_Scraper.Env import Env
from MA_Scraper.Scripts.SQL import refresh_tables
import pandas as pd
import faiss
from collections import defaultdict
import numpy as np
from datetime import datetime
from sqlalchemy import func, select, alias
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
    result = db.session.execute(select(
        Discography.band_id,
        func.sum(Discography.review_count).label('review_count'),
        func.percentile_cont(0.5).within_group(Discography.review_score).label('median_score')
    ).filter(Discography.reviews.isnot(None)) \
     .group_by(Discography.band_id)).all()
    
    df = pd.DataFrame(result, columns=['band_id', 'review_count', 'median_score'])
    return df

def get_filtered_band_members(band_ids):
    m_alias2 = alias(Member)
    shared_members_cte = (
        select(Member.member_id)
        .where(Member.band_id.in_(band_ids), Member.category.in_(['Current lineup', 'Past lineup'])).distinct()
    ).cte()

    result = (db.session.execute(
        select(Band.band_id, Member.member_id)
        .join(m_alias2, Band.band_id == m_alias2.c.band_id)
        .join(Member, onclause=Member.band_id == Band.band_id)
        .where(m_alias2.c.member_id.in_(select(shared_members_cte.c.member_id)), m_alias2.c.category.in_(['Current lineup', 'Past lineup']))
    ).all())

    band_members = defaultdict(set)
    for band_id, member_id in result:
        band_members[band_id].add(member_id)
    return band_members

def create_item():
    score_subquery = db.session.query(
    Similar_band.band_id,
    func.sum(func.distinct(Similar_band.score)).label('score')
    ).group_by(Similar_band.band_id).subquery()

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

def create_item_embeddings(item):
    categorical_columns = ['country', 'theme_names', 'b_label', 'status', 'genre_names', 'hybrid_genres', 'prefix_names']
    numerical_columns = ['score', 'review_count', 'median_score']

    categorical_embeddings = one_hot_encode(item, categorical_columns)

    numerical_embeddings = ((item[numerical_columns] - np.mean(item[numerical_columns], axis=0)) / np.std(item[numerical_columns], axis=0)).to_numpy()

    item_embeddings_dense = np.hstack([
        categorical_embeddings.astype('float32'),
        numerical_embeddings.astype('float32')
    ])

    return item_embeddings_dense

def cluster(array, min_cluster_size=None):
    min_cluster_size = int(len(array) * 0.05)
    if len(array) < min_cluster_size:
        return [np.mean(array, axis=0)]

    clusterer = HDBSCAN(min_cluster_size=min_cluster_size, min_samples=1, allow_single_cluster=True)
    cluster_labels = clusterer.fit_predict(array)

    vectors = []
    unique_clusters = np.unique(cluster_labels)
    
    for cluster_label in unique_clusters:
        if cluster_label != -1:
            cluster_items_embeddings = array[cluster_labels == cluster_label]
            if len(cluster_items_embeddings) > 0:
                vector = np.mean(cluster_items_embeddings, axis=0)
                vectors.append(vector)
    return vectors

def generate_user_vectors(liked_bands, item_embeddings_array, item_df, min_cluster_size=None):
    liked_embeddings_array = item_embeddings_array[item_df['band_id'].isin(liked_bands)]

    pca = PCA(n_components=0.90)
    pca = pca.fit(liked_embeddings_array)
    processed_embeddings_array = pca.transform(liked_embeddings_array)
    user_interest_vectors = cluster(processed_embeddings_array, min_cluster_size)

    print(f"user interest vectors {len(user_interest_vectors)}")
    if not user_interest_vectors:
        user_interest_vectors = np.mean(processed_embeddings_array, axis=0)

    user_interest_vectors = np.array(user_interest_vectors).astype('float32')
    return user_interest_vectors, pca

def index_faiss(dense):
    dimension = dense.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(dense)

    return index

def get_jaccard(liked_bands):
    band_members = get_filtered_band_members(liked_bands)
    liked_bands = set(liked_bands) & set(band_members.keys())
    
    candidate_bands = set(band_members.keys()) - set(liked_bands)
    jaccard_candidates = defaultdict(lambda: {'total': 0, 'count': 0})

    for liked_band in liked_bands:
        members = band_members[liked_band]

        for candidate_band in candidate_bands:
            members2 = band_members[candidate_band]

            intersection = len(members & members2)
            union = len(members | members2)
            jaccard = intersection / union if union != 0 else 0
        
            jaccard_candidates[candidate_band]['total'] += jaccard
            jaccard_candidates[candidate_band]['count'] += 1

    return jaccard_candidates

def generate_candidates(index, item_df, interacted_bands, liked_bands, user_vectors, k):
    disliked_bands = set(interacted_bands) - set(liked_bands)
    
    if user_vectors.size == 0:
        return []
    k_per_cluster = k // len(user_vectors)

    distances_batch, faiss_indices_batch = index.search(user_vectors, k_per_cluster)
    valid_indices = faiss_indices_batch[faiss_indices_batch != -1]
    valid_distances = distances_batch[faiss_indices_batch != -1]

    temp_df = pd.DataFrame({
        'band_id': item_df.iloc[valid_indices]['band_id'].values,
        'faiss_distance': valid_distances
    })

    min_distances_df = temp_df.loc[temp_df.groupby('band_id')['faiss_distance'].idxmin()]
    faiss_list = min_distances_df[['band_id', 'faiss_distance']].to_dict(orient='records')

    candidates = [info['band_id'] for info in faiss_list]
    faiss_distance_lookup = {info['band_id']: info['faiss_distance'] for info in faiss_list}

    jaccard_candidates = get_jaccard(liked_bands)
    candidates.extend(list(jaccard_candidates.keys()))
    candidates = list(set(candidates))

    combined_scores = []
    max_faiss_dist = max(d['faiss_distance'] for d in faiss_list)

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
    candidates = [candidate for candidate in candidates if candidate not in disliked_bands]

    known_candidates_re_ranked = []
    new_candidates_re_ranked = []

    for band_id in candidates:
        if band_id in interacted_bands:
            known_candidates_re_ranked.append(band_id)
        else:
            new_candidates_re_ranked.append(band_id)

    faiss_pool = []

    faiss_pool.extend(new_candidates_re_ranked[:int(k*0.8)])
    faiss_pool.extend(known_candidates_re_ranked[:int(k*0.2)])

    return faiss_pool

def main(min_cluster_size=None, k=400):
    app = create_app()
    with app.app_context():
        item = create_item()
        users_preference = create_user()
        item_embeddings = create_item_embeddings(item)

        candidate_list = []
        for user_id in users_preference[users_preference['label'] == 1]['user'].unique():
            interacted_bands = users_preference[users_preference['user'] == user_id]['band_id'].unique().astype(int).tolist()
            liked_bands = users_preference[(users_preference['user'] == user_id) & (users_preference['label'] == 1)]['band_id'].unique().astype(int).tolist()
            user_vectors, pca = generate_user_vectors(liked_bands, item_embeddings, item, min_cluster_size)
            item_embeddings = pca.transform(item_embeddings)
            index = index_faiss(item_embeddings)
            candidates = generate_candidates(index, item, interacted_bands, liked_bands, user_vectors, k)
            for candidate in candidates:
                candidate_list.append({'user_id': user_id, 'band_id': candidate})

        candidate_df = pd.DataFrame(candidate_list)
        candidate_df.to_csv(env.candidates, index=False)

def complete_refresh(min_cluster_size=None, k=400):
    main(min_cluster_size, k)
    refresh_tables([Candidates])

if __name__ == '__main__':
    complete_refresh(min_cluster_size=10)