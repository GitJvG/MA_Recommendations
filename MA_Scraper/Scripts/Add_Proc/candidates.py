from MA_Scraper.app import create_app, db
from MA_Scraper.app.models import band as Band, genre as Genre, hgenre as Hgenre, themes as Themes, discography as Discog, \
                        theme as Theme, details as Details, user as User, users as Users, similar_band as Similar, candidates, member as Member
import pandas as pd
import faiss
from collections import defaultdict
import numpy as np
from datetime import datetime
from sqlalchemy import func, and_
from MA_Scraper.Env import Env
from MA_Scraper.Scripts.SQL import refresh_tables
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
        Details.label,
        Details.country,
        Details.status,
        score_subquery.c.score,
        func.string_agg(func.distinct(Genre.name), ', ').label('genre_names'),
        func.string_agg(func.distinct(Hgenre.name), ', ').label('hybrid_genres'),
        func.string_agg(func.distinct(Theme.name), ', ').label('theme_names')
    ).join(score_subquery, score_subquery.c.band_id == Band.band_id
    ).join(Details, Band.band_id == Details.band_id
    ).join(Band.genres, isouter=True
    ).join(Band.hgenres, isouter=True
    ).join(Themes, Band.band_id == Themes.band_id
    ).join(Theme, Themes.theme_id == Theme.theme_id
    ).group_by(Band.band_id, Band.name, Band.genre, Details.label, Details.country, Details.status, score_subquery.c.score
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
            'status': band.status,
            'score': band.score,
        }
        for band in results
    ]

    dataframe = pd.DataFrame(data)
    reviews = get_review_data()
    merged_dataframe = pd.merge(dataframe, reviews, on='band_id', how='left')
    # Fill entries without reviews, 0 makes sense in this case.
    merged_dataframe[['review_count', 'median_score']] = merged_dataframe[['review_count', 'median_score']].fillna(0)

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
    categorical_columns = ['country', 'band_genre', 'theme_names', 'b_label', 'status', 'genre_names', 'hybrid_genres']
    numerical_columns = ['score', 'review_count', 'median_score']


    categorical_embeddings = one_hot_encode(item, categorical_columns)

    # Standardscaling numerical cols
    numerical_embeddings = ((item[numerical_columns] - np.mean(item[numerical_columns], axis=0)) / np.std(item[numerical_columns], axis=0)).to_numpy()

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

def generate_candidates(user_id, users_preference, index, item, item_embeddings, k):
    user_vector = generate_user_vector(user_id, users_preference, item_embeddings, item)
    interacted_bands = users_preference[users_preference['user'] == user_id]['band_id'].values
    k2 = min(k + len(interacted_bands), k * 2)
    distances, indices = index.search(user_vector.reshape(1, -1).astype('float32'), k2)
    faiss_candidate_bands = item.iloc[indices[0]]['band_id'].values
    remaining_candidates = list(faiss_candidate_bands)
    for band in faiss_candidate_bands:
        if band in interacted_bands:
            if len(remaining_candidates) > k2*3:
                remaining_candidates.remove(band)
            else:
                break

    liked_bands = users_preference[(users_preference['user'] == user_id) & (users_preference['label'] == 1)]['band_id'].values
    if len(liked_bands) > 1:
        liked_bands_list = [int(band_id) for band_id in liked_bands]
        band_members = get_filtered_band_members(liked_bands_list)
        jaccard_dict = get_jaccard(band_members, liked_bands_list)

        jaccard_candidates = defaultdict(lambda: {'total': 0, 'count': 0}) #default dictionary to store total and count
        for liked_band in liked_bands:
            for candidate_band, score in jaccard_dict.get(liked_band, {}).items():
                jaccard_candidates[candidate_band]['total'] += score
                jaccard_candidates[candidate_band]['count'] += 1

        remaining_candidates.extend(list(jaccard_candidates.keys()))
        remaining_candidates = list(set(remaining_candidates))

        combined_scores = []
        for candidate_band in remaining_candidates:
            faiss_rank = remaining_candidates.index(candidate_band) if candidate_band in remaining_candidates else float('inf')
            total_jaccard = jaccard_candidates[candidate_band]['total']
            count = jaccard_candidates[candidate_band]['count']
            avg_jaccard = total_jaccard / count if count > 0 else 0
            combined_scores.append((candidate_band, faiss_rank + (1 - avg_jaccard) * 1000))

        combined_scores.sort(key=lambda x: x[1])
        final_candidates = [band for band, _ in combined_scores]
    else:
        final_candidates = remaining_candidates[:k]

    return final_candidates[:k]

def generate_candidates_for_all_users(users_preference, index, item, item_embeddings, k=1000):
    candidate_list = []

    for user_id in users_preference['user'].unique():
        candidates = generate_candidates(user_id, users_preference, index, item, item_embeddings, k)
        for candidate in candidates:
            candidate_list.append({'user_id': user_id, 'band_id': candidate})

    candidate_df = pd.DataFrame(candidate_list)
    return candidate_df

def verify_candidate_member_overlap(candidates_csv_path, users_preference):
    candidates_df = pd.read_csv(candidates_csv_path)
    results = []

    for user_id in candidates_df['user_id'].unique():
        user_candidates = candidates_df[candidates_df['user_id'] == user_id]['band_id'].tolist()
        print(user_candidates)
        liked_bands = users_preference[users_preference['user'] == user_id][users_preference['label'] == 1]['band_id'].tolist()
        liked_bands_int = [int(band_id) for band_id in liked_bands]

        if len(liked_bands_int) > 1:
            band_members = get_filtered_band_members(liked_bands_int)
            jaccard_dict = get_jaccard(band_members)

            overlap_count = 0
            for candidate_band in user_candidates:
                for liked_band in liked_bands_int:
                    if liked_band in jaccard_dict:
                        if candidate_band in jaccard_dict[liked_band]:
                            if jaccard_dict[liked_band][candidate_band] > 0:
                                overlap_count += 1
                                break

            overlap_percentage = (overlap_count / len(user_candidates)) * 100 if user_candidates else 0
            results.append({'user_id': user_id, 'overlap_percentage': overlap_percentage})
        else:
            results.append({'user_id': user_id, 'overlap_percentage': 0})

def main(k=200):
    app = create_app()
    with app.app_context():
        item = create_item()
        users_preference = create_user()
        index, item_embeddings = create_item_embeddings_with_faiss(item)
        candidate_frame = generate_candidates_for_all_users(users_preference, index, item, item_embeddings, k)
        candidate_frame.to_csv(env.candidates, index=False)

def complete_refresh(k=200):
    main(k)
    refresh_tables([candidates])

if __name__ == '__main__':
    main()