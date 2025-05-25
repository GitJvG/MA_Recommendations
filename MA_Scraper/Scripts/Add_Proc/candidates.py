from MA_Scraper.app import create_app, db
from MA_Scraper.app.models import Band, Genre, Hgenre, Discography, \
                        Theme, Users, Similar_band, Candidates, Member, Prefix
from MA_Scraper.Env import Env
from MA_Scraper.Scripts.SQL import refresh_tables
import pandas as pd
import faiss
from collections import defaultdict
import numpy as np
from sqlalchemy import func, select, case, cast, Date
from hdbscan import HDBSCAN
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

env = Env.get_instance()

faiss.omp_set_num_threads(8)

def split_one_hot_encode(df, multi_value_cols):
    df_result = df.copy()

    for col in multi_value_cols:
        df_result[col] = df_result[col].replace('Not available', '').astype(str)
        df_result[f'{col}_list'] = df_result[col].str.split(',').apply(
            lambda x: [item.strip() for item in x if item.strip()]
        )
        df_exploded_part = df_result[['band_id', f'{col}_list']].explode(f'{col}_list')
    
        exploded_ohe = pd.get_dummies(df_exploded_part[f'{col}_list'], prefix=col, dtype=int)
        df_temp = pd.concat([df_exploded_part[['band_id']], exploded_ohe], axis=1)
        df_aggregated_ohe = df_temp.groupby('band_id').max().reset_index()
        df_result = pd.merge(df_result, df_aggregated_ohe, on='band_id', how='left').fillna(0)
        df_result = df_result.drop(columns=[col, f'{col}_list'])
    
    return df_result

def create_item():
    reviews = select(
        Discography.band_id,
        func.sum(Discography.review_count).label('review_count'),
        func.percentile_cont(0.5).within_group(Discography.review_score).label('median_score')
        ).filter(Discography.reviews.isnot(None)
        ).group_by(Discography.band_id).cte()

    results = db.session.execute(select(
        Band.band_id,
        Band.name.label('band_name'),
        Band.label.label('b_label'),
        Band.country,
        Band.status,
        func.coalesce(reviews.c.review_count, 0).label('review_count'),
        func.coalesce(reviews.c.median_score, 0).label('median_score'),
        func.coalesce(func.sum((Similar_band.score)), 0).label('score'),
        func.string_agg(func.distinct(Genre.name), ', ').label('genre_names'),
        func.coalesce(func.string_agg(func.distinct(Theme.name), ', '), 'Not available').label('theme_names'),
        func.coalesce(func.string_agg(func.distinct(Prefix.name), ', '), 'Not available').label('prefix_names')
    ).join(reviews, onclause=reviews.c.band_id == Band.band_id, isouter=True
    ).join(Band.outgoing_similarities
    ).join(Band.genres, isouter=True
    ).join(Band.hgenres, isouter=True
    ).join(Band.themes, isouter=True
    ).join(Band.prefixes, isouter=True
    ).group_by(Band.band_id, Band.name, Band.genre, Band.label, Band.country, Band.status,
               reviews.c.review_count, reviews.c.median_score)).all()

    dataframe = pd.DataFrame(results)
    return dataframe

def create_user():
    user_band_preference_data = db.session.execute(select(
        Users.user_id.label('user'),
        Users.band_id,
        case(((Users.liked == True) | (Users.remind_me == True), 1),else_=0).label('label'),
        func.least(func.abs(func.current_date() - cast(Users.liked_date, Date)),
            func.abs(func.current_date() - cast(Users.remind_me_date, Date)).label('relevance'))
        )).all()

    users_preference = pd.DataFrame(user_band_preference_data)
    return users_preference

def create_item_embeddings(item):
    multi_valued_categorical_cols = ['prefix_names', 'genre_names']
    single_value_categorical_cols = ['country', 'b_label', 'status']
    numerical_columns = ['score', 'review_count', 'median_score']

    processed_df = split_one_hot_encode(item, multi_valued_categorical_cols)
    final_categorical_df = pd.get_dummies(processed_df, columns=single_value_categorical_cols, dtype=int)

    numerical_embeddings = ((item[numerical_columns] - np.mean(item[numerical_columns], axis=0)) / np.std(item[numerical_columns], axis=0)).to_numpy()

    categorical_columns = [col for col in final_categorical_df.columns if col not in numerical_columns and col not in ['theme_names', 'band_id', 'band_name']]
    categorical_embeddings = final_categorical_df[categorical_columns].to_numpy()

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

    pca = PCA(n_components=0.95)
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

def get_filtered_band_members(band_ids):
    bands_with_shared_members_cte = (select(Band.band_id)
        .join(Band.members)
        .where(Member.band_id.in_(band_ids), Member.category.in_(['Current lineup', 'Past lineup'])).distinct()
    ).cte()

    result = db.session.execute(
        select(Member.band_id, Member.member_id)
        .where(Member.band_id.in_(select(bands_with_shared_members_cte.c.band_id)), Member.category.in_(['Current lineup', 'Past lineup'])).distinct()
    ).all()

    band_members = defaultdict(set)
    for band_id, member_id in result:
        band_members[band_id].add(member_id)
    return band_members

def get_jaccard(liked_bands):
    band_members = get_filtered_band_members(liked_bands)
    liked_bands = set(liked_bands) & set(band_members.keys())

    union_of_liked_members = set()
    for band_id in liked_bands:
        union_of_liked_members.update(band_members[band_id])

    candidate_bands = set(band_members.keys()) - liked_bands
    jaccard_scores = []

    for candidate_band_id in candidate_bands:
        members_of_candidate_band = band_members[candidate_band_id]

        intersection_size = len(members_of_candidate_band.intersection(union_of_liked_members))
        union_size = len(members_of_candidate_band.union(union_of_liked_members))
        
        jaccard = intersection_size / union_size if union_size != 0 else 0.0
        jaccard_scores[candidate_band_id] = jaccard
    
    jaccard_scores = pd.DataFrame(jaccard_scores, columns=['band_id', 'jaccard_score'])
    return jaccard_scores

def generate_candidates(index, item_df, interacted_bands, liked_bands, user_vectors, k):
    disliked_bands = set(interacted_bands) - set(liked_bands)
    
    if user_vectors.size == 0:
        return []
    k_per_cluster = k // len(user_vectors) + 2

    distances_batch, faiss_indices_batch = index.search(user_vectors, k_per_cluster)
    valid_indices = faiss_indices_batch[faiss_indices_batch != -1]
    valid_distances = distances_batch[faiss_indices_batch != -1]

    df = pd.DataFrame({
        'band_id': item_df.iloc[valid_indices]['band_id'].values,
        'faiss_distance': valid_distances
    })

    min_distances_df = df.loc[df.groupby('band_id')['faiss_distance'].idxmin()]
    jaccard_scores_df = get_jaccard(liked_bands)
    combined_candidates_df = pd.merge(min_distances_df, jaccard_scores_df, on='band_id', how='outer')
    combined_candidates_df = combined_candidates_df[~combined_candidates_df['band_id'].isin(list(disliked_bands))]

    max_faiss_dist = combined_candidates_df['faiss_distance'].max()
    combined_candidates_df['jaccard_score'] = combined_candidates_df['jaccard_score'].fillna(0.0)
    combined_candidates_df['faiss_normalized'] = np.minimum(combined_candidates_df['faiss_distance'] / max_faiss_dist, 1.0)
    combined_candidates_df['score'] = (combined_candidates_df['faiss_normalized'] * 0.8) + \
                                      ((1 - combined_candidates_df['jaccard_score']) * 0.2)
    combined_candidates_df = combined_candidates_df.sort_values(by='score', ascending=True).reset_index(drop=True)
    
    num_new_to_take = int(k * 0.8)
    num_known_to_take = k - num_new_to_take

    combined_candidates_df['is_known'] = combined_candidates_df['band_id'].isin(list(interacted_bands))
    new_candidates = combined_candidates_df[~combined_candidates_df['is_known']].head(num_new_to_take)['band_id'].tolist()
    known_candidates = combined_candidates_df[combined_candidates_df['is_known']].head(num_known_to_take)['band_id'].tolist()

    return new_candidates + known_candidates

def main(min_cluster_size=None, k=400):
    app = create_app()
    with app.app_context():
        item = create_item()
        item_embeddings = create_item_embeddings(item)
        users_preference = create_user()

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