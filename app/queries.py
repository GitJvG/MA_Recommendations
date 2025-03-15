from sqlalchemy import func, and_, or_, exists
from .models import user, band, users, discography, similar_band, details, genre, genres, member, prefix, candidates, db
from app.cache_manager import cache_manager
from datetime import datetime
from app.YT import YT
from math import ceil
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

def Above_avg_albums(band_ids):
    avg_scores_subquery = db.session.query(
        discography.band_id,
        discography.name,
        discography.type,
        band.name.label('band_name'),
        band.genre,
        discography.review_score,
        discography.review_count,
        func.avg(discography.review_score * discography.review_count).over(
            partition_by=discography.band_id
        ).label('avg_album_score'),
        func.row_number().over(
            partition_by=discography.band_id,
            order_by=func.random()
        ).label('row_number')
    ) \
        .join(band, band.band_id == discography.band_id).filter(discography.band_id.in_(band_ids)).subquery()

    albums_above_avg = db.session.query(
        avg_scores_subquery.c.band_id,
        avg_scores_subquery.c.name,
        avg_scores_subquery.c.type,
        avg_scores_subquery.c.band_name,
        avg_scores_subquery.c.genre,
        avg_scores_subquery.c.review_score,
        avg_scores_subquery.c.review_count,
        avg_scores_subquery.c.avg_album_score,
        avg_scores_subquery.c.row_number,
        func.min(avg_scores_subquery.c.row_number).over(
            partition_by=avg_scores_subquery.c.band_id
        ).label('min_row_number')
    ).filter(
            avg_scores_subquery.c.review_score * avg_scores_subquery.c.review_count >= avg_scores_subquery.c.avg_album_score
            ).subquery()

    albums_with_avg_scores = db.session.query(
        albums_above_avg.c.band_id,
        albums_above_avg.c.name,
        albums_above_avg.c.type,
        albums_above_avg.c.band_name,
        albums_above_avg.c.genre,
    ) \
        .filter(
            albums_above_avg.c.row_number == albums_above_avg.c.min_row_number
        ).all()
    return albums_with_avg_scores

def Max_albums(band_ids):
    max_scores_subquery = db.session.query(
        discography.band_id,
        func.max(discography.review_score * discography.review_count).label('max_album_score')
    ) \
        .filter(discography.band_id.in_(band_ids)) \
        .filter(discography.review_score > 0) \
        .group_by(discography.band_id) \
        .subquery()

    top_albums = db.session.query(
        discography.band_id,
        discography.name,
        discography.type,
        band.name.label('band_name'),
        band.genre
    ) \
        .join(band, band.band_id == discography.band_id) \
        .join(max_scores_subquery, max_scores_subquery.c.band_id == discography.band_id) \
        .filter(discography.review_score * discography.review_count == max_scores_subquery.c.max_album_score) \
        .distinct(discography.band_id).all()
    
    return top_albums

def New_albums(min_year=datetime.today().year-1):
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
        .order_by(None).order_by(func.random()).limit(10).all()
    
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
    ).filter(Pop_bands.c.row_num == 1).order_by(None).order_by(func.random()).limit(5).all()

    final_query = query + top_albums
    print(query)
    print(top_albums)
    return final_query
