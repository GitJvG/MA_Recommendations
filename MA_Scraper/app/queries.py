from sqlalchemy import func
from MA_Scraper.app.models import user, band, users, discography, similar_band, details, genre, genres, member, prefix, candidates, db
from datetime import datetime

def get_band_genres_subquery():
    return db.session.query(
        band.band_id,
        func.string_agg(
            func.concat(
                func.upper(func.substr(genre.name, 1, 1)),
                func.substr(genre.name, 2)
            ), ', ').label('genre')
        ).join(genres, genres.band_id == band.band_id).join(genre, (genre.genre_id == genres.item_id) & (genre.type == genres.type)).group_by(band.band_id).subquery()

def Above_avg_albums(band_ids, picks_per_band=1):
    ranked_albums_subquery = db.session.query(
        discography.band_id,
        discography.name,
        discography.type,
        band.name.label('band_name'),
        band.genre,
        func.coalesce(discography.review_score * discography.review_count, 0).label('weighted_score'),
        func.avg(func.coalesce(discography.review_score * discography.review_count, 0)).over(
            partition_by=discography.band_id
        ).label("avg_weighted_score")
    ) \
    .join(band, band.band_id == discography.band_id) \
    .filter(discography.band_id.in_(band_ids)) \
    .filter(discography.type.in_(["Full-length", "Split", "EP"])) \
    .subquery()

    # Subquery to rank albums within each band based on weighted score (descending)
    ranked_albums_with_row_num = db.session.query(
        ranked_albums_subquery.c.band_id,
        ranked_albums_subquery.c.name,
        ranked_albums_subquery.c.type,
        ranked_albums_subquery.c.band_name,
        ranked_albums_subquery.c.genre,
        ranked_albums_subquery.c.weighted_score,
        ranked_albums_subquery.c.avg_weighted_score,
        func.row_number().over(
            partition_by=ranked_albums_subquery.c.band_id,
            order_by=ranked_albums_subquery.c.weighted_score.desc()
        ).label('rank')
    ).subquery()

    selected_albums = []
    for band_id in band_ids:
        # Get above-average albums for the current band
        above_avg_albums = db.session.query(
            ranked_albums_with_row_num.c.band_id,
            ranked_albums_with_row_num.c.name,
            ranked_albums_with_row_num.c.type,
            ranked_albums_with_row_num.c.band_name,
            ranked_albums_with_row_num.c.genre
        ).filter(
            ranked_albums_with_row_num.c.band_id == band_id,
            ranked_albums_with_row_num.c.weighted_score >= ranked_albums_with_row_num.c.avg_weighted_score
        ).limit(picks_per_band).all()

        num_above_avg = len(above_avg_albums)
        selected_albums.extend(above_avg_albums)

        if num_above_avg < picks_per_band:
            below_avg_needed = picks_per_band - num_above_avg

            below_avg_ranked = db.session.query(
                ranked_albums_subquery.c.band_id,
                ranked_albums_subquery.c.name,
                ranked_albums_subquery.c.type,
                ranked_albums_subquery.c.band_name,
                ranked_albums_subquery.c.genre,
                func.row_number().over(
                    partition_by=ranked_albums_subquery.c.band_id,
                    order_by=func.random()
                ).label('random_rank')
            ).filter(
                ranked_albums_subquery.c.band_id == band_id,
                ranked_albums_subquery.c.weighted_score < ranked_albums_subquery.c.avg_weighted_score
            ).subquery()

            below_avg_albums = db.session.query(
                below_avg_ranked.c.band_id,
                below_avg_ranked.c.name,
                below_avg_ranked.c.type,
                below_avg_ranked.c.band_name,
                below_avg_ranked.c.genre
            ).filter(below_avg_ranked.c.random_rank <= below_avg_needed).all()

            selected_albums.extend(below_avg_albums)

    return selected_albums

def Max_albums(band_ids, type_filter=False):
    query = db.session.query(
        discography.band_id,
        discography.name,
        discography.type,
        func.row_number()
            .over(
                partition_by=discography.band_id,
                order_by=(discography.review_score * discography.review_count).desc()
            ).label('rank')
    ) \
    .filter(discography.band_id.in_(band_ids)) \
    .filter(discography.review_score > 0) \

    if type_filter:
        query = query.filter(discography.type.in_(["Full-length", "Split", "EP", "Demo"]))

    ranked_albums_subquery = query.subquery()

    top_albums = db.session.query(
        ranked_albums_subquery.c.band_id,
        ranked_albums_subquery.c.name,
        ranked_albums_subquery.c.type,
        band.name.label('band_name'),
        band.genre
    ) \
    .join(band, band.band_id == ranked_albums_subquery.c.band_id) \
    .filter(ranked_albums_subquery.c.rank == 1) \
    .all()

    return top_albums

def New_albums(query_limit=10, min_year=datetime.today().year-1):
    limit1 = int(query_limit/2)
    limit2 = query_limit - limit1
    genre_subq = get_band_genres_subquery()

    latest_years_subquery = db.session.query(
        discography.band_id,
        discography.album_id,
        func.max(discography.review_score * discography.review_count).over(partition_by=discography.band_id).label('max_album_score'),
        func.row_number().over(partition_by=discography.band_id,
        order_by=(discography.review_score * discography.review_count).desc()).label("row_num")
    ).filter(discography.year >= min_year) \
    .filter(discography.review_score > 0) \
    .filter(discography.type.in_(['Full-length', 'Demo', 'EP', 'Split'])).order_by((discography.review_score * discography.review_count).desc()).subquery()

    subquery = db.session.query(
        latest_years_subquery.c.band_id,
        latest_years_subquery.c.album_id,
        latest_years_subquery.c.max_album_score
    ).filter(latest_years_subquery.c.row_num == 1) \
    .order_by(latest_years_subquery.c.max_album_score.desc(), func.random()).limit(150).subquery()

    query = db.session.query(
        subquery.c.band_id,
        discography.name,
        discography.type,
        band.name.label('band_name'),
        genre_subq.c.genre
    ).join(subquery, 
           (discography.band_id == subquery.c.band_id) & 
           (discography.album_id == subquery.c.album_id)) \
        .join(band, band.band_id == subquery.c.band_id) \
        .join(genre_subq, genre_subq.c.band_id == band.band_id) \
        .order_by(None).order_by(func.random()).limit(limit2).all()
    
    selected_band_ids = [vband[0] for vband in query]

    band_scores = db.session.query(
        similar_band.band_id,
        func.sum(similar_band.score).label("total_score")
    ).group_by(similar_band.band_id).subquery()

    Pop_bands = db.session.query(
        band.band_id,
        discography.name,
        discography.type,
        band.name.label('band_name'),
        genre_subq.c.genre,
        func.row_number().over(
            partition_by=band.band_id,
            order_by=discography.year.desc()
        ).label("row_num"),
        band_scores.c.total_score
    ).join(band_scores, band.band_id == band_scores.c.band_id, isouter=True) \
    .join(discography, band.band_id == discography.band_id) \
    .join(genre_subq, genre_subq.c.band_id == band.band_id) \
    .filter(discography.year >= min_year) \
    .filter(discography.type.in_(['Full-length', 'EP'])) \
    .filter(~discography.band_id.in_(selected_band_ids)) \
    .filter(band_scores.c.total_score > 0) \
    .order_by(band_scores.c.total_score.desc()) \
    .limit(150).subquery()

    top_albums = db.session.query(
        Pop_bands.c.band_id,
        Pop_bands.c.name,
        Pop_bands.c.type,
        Pop_bands.c.band_name,
        Pop_bands.c.genre
    ).filter(Pop_bands.c.row_num == 1).order_by(None).order_by(func.random()).limit(limit1).all()

    final_query = query + top_albums
    return final_query
