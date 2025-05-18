from sqlalchemy import func, select
from MA_Scraper.app import db, create_app
from MA_Scraper.app.models import user, band, users, discography, similar_band, details, genre, BandGenres, BandPrefixes, BandHgenres, member, prefix, candidates, db
from datetime import datetime

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
    limit1 = int(query_limit / 2)
    limit2 = query_limit - limit1

    genre_cte_stmt = (select(band.band_id,
            func.string_agg(genre.name, ', ').label('genre')
        ).join(band.genres)
        .group_by(band.band_id)).cte('genre_cte_stmt')
    
    recent_albums_ranked_by_year = (
        select(
            discography.band_id,
            discography.album_id,
            discography.name.label('album_name'),
            discography.type.label('album_type'),
            discography.year.label('album_year'),
            discography.review_score,
            discography.review_count,
            band.name.label('band_name'),
            func.row_number().over(partition_by=discography.band_id,order_by=discography.year.desc()).label("rank_by_year")
        ).join(discography.band).where(discography.year >= min_year,
            discography.type.in_(['Full-length', 'EP', 'Split', 'Demo']))).cte('recent_albums_ranked_by_year')
    
    latest_albums_ranked = (select(
            recent_albums_ranked_by_year,
            func.row_number().over(partition_by=recent_albums_ranked_by_year.c.band_id,order_by=(recent_albums_ranked_by_year.c.review_score * recent_albums_ranked_by_year.c.review_count).desc()).label("rank_by_score"),
            func.max(recent_albums_ranked_by_year.c.review_score * recent_albums_ranked_by_year.c.review_count).over(partition_by=recent_albums_ranked_by_year.c.band_id).label('max_album_score')
        ).where(recent_albums_ranked_by_year.c.review_score > 0)).cte('latest_albums_ranked')

    first_branch_results = db.session.execute(
        select(
            latest_albums_ranked.c.band_id,
            latest_albums_ranked.c.album_name.label('name'),
            latest_albums_ranked.c.album_type.label('type'),
            latest_albums_ranked.c.band_name,
            genre_cte_stmt.c.genre
        )
        .join(genre_cte_stmt, genre_cte_stmt.c.band_id == latest_albums_ranked.c.band_id)
        .where(latest_albums_ranked.c.rank_by_score == 1)
        .order_by(None).order_by(func.random()).limit(limit2)
    ).all()
     
    selected_band_ids = [row.band_id for row in first_branch_results]

    band_scores = (select(similar_band.band_id,
        func.sum(similar_band.score).label("total_score")
        ).group_by(similar_band.band_id)).cte('band_scores')

    second_results = db.session.execute(
        select(
             recent_albums_ranked_by_year.c.band_id,
             recent_albums_ranked_by_year.c.album_name.label('name'),
             recent_albums_ranked_by_year.c.album_type.label('type'),
             recent_albums_ranked_by_year.c.band_name,
             genre_cte_stmt.c.genre
        )
        .join(band_scores, recent_albums_ranked_by_year.c.band_id == band_scores.c.band_id, isouter=True)
        .join(genre_cte_stmt, genre_cte_stmt.c.band_id == recent_albums_ranked_by_year.c.band_id)
        .where(recent_albums_ranked_by_year.c.rank_by_year == 1, band_scores.c.total_score > 0, recent_albums_ranked_by_year.c.band_id.notin_(selected_band_ids))
        .order_by(None).order_by(func.random()).limit(limit1)
    ).all()

    final_combined_results = first_branch_results + second_results
    return final_combined_results
