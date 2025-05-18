from sqlalchemy import func, select
from MA_Scraper.app import db, create_app
from MA_Scraper.app.models import Band, Discography, Similar_band, Genre, db
from datetime import datetime

def Top_albums(band_ids, picks_per_band=1):
    ranked_albums_subquery = select(
        Band.band_id,
        Discography.name,
        Discography.type,
        Band.name.label('band_name'),
        Band.genre,
        func.coalesce(Discography.review_score * Discography.review_count, 0).label('weighted_score'),
    ).join(Discography.band).where(Discography.band_id.in_(band_ids), Discography.type.in_(["Full-length", "Split", "EP", "Demo", "Single"])).cte("ranked_albums_subquery")

    ranked_albums_with_row_num = (select(
        ranked_albums_subquery,
        func.row_number().over(
            partition_by=ranked_albums_subquery.c.band_id,
            order_by=ranked_albums_subquery.c.weighted_score.desc()).label('rank')
    )).cte("ranked_albums_with_row_num")

    selected_albums = db.session.execute(select(
            ranked_albums_with_row_num.c.band_id,
            ranked_albums_with_row_num.c.name,
            ranked_albums_with_row_num.c.type,
            ranked_albums_with_row_num.c.band_name,
            ranked_albums_with_row_num.c.genre
        )
        .where(ranked_albums_with_row_num.c.rank <= picks_per_band)).all()

    return selected_albums

def New_albums(query_limit=10, min_year=datetime.today().year-1):
    limit1 = int(query_limit / 2)
    limit2 = query_limit - limit1

    genre_cte_stmt = (select(Band.band_id,
            func.string_agg(Genre.name, ', ').label('genre')
        ).join(Band.genres)
        .group_by(Band.band_id)).cte('genre_cte_stmt')
    
    recent_albums_ranked_by_year = (
        select(
            Discography.band_id,
            Discography.album_id,
            Discography.name,
            Discography.type,
            Discography.year.label('album_year'),
            Discography.review_score,
            Discography.review_count,
            Band.name.label('band_name'),
            func.row_number().over(partition_by=Discography.band_id,order_by=Discography.year.desc()).label("rank_by_year")
        ).join(Discography.band).where(Discography.year >= min_year,
            Discography.type.in_(['Full-length', 'EP', 'Split', 'Demo']))).cte('recent_albums_ranked_by_year')
    
    latest_albums_ranked = (select(
            recent_albums_ranked_by_year,
            func.row_number().over(partition_by=recent_albums_ranked_by_year.c.band_id,order_by=(recent_albums_ranked_by_year.c.review_score * recent_albums_ranked_by_year.c.review_count).desc()).label("rank_by_score"),
            func.max(recent_albums_ranked_by_year.c.review_score * recent_albums_ranked_by_year.c.review_count).over(partition_by=recent_albums_ranked_by_year.c.band_id).label('max_album_score')
        ).where(recent_albums_ranked_by_year.c.review_score > 0)).cte('latest_albums_ranked')

    first_branch_results = db.session.execute(
        select(
            latest_albums_ranked.c.band_id,
            latest_albums_ranked.c.name,
            latest_albums_ranked.c.type,
            latest_albums_ranked.c.band_name,
            genre_cte_stmt.c.genre
        )
        .join(genre_cte_stmt, genre_cte_stmt.c.band_id == latest_albums_ranked.c.band_id)
        .where(latest_albums_ranked.c.rank_by_score == 1)
        .order_by(None).order_by(func.random()).limit(limit1)
    ).all()
    
    selected_band_ids = [row.band_id for row in first_branch_results]

    band_scores = (select(Similar_band.band_id,
        func.sum(Similar_band.score).label("total_score")
        ).group_by(Similar_band.band_id)).cte('band_scores')

    second_results = db.session.execute(
        select(
             recent_albums_ranked_by_year.c.band_id,
             recent_albums_ranked_by_year.c.name,
             recent_albums_ranked_by_year.c.type,
             recent_albums_ranked_by_year.c.band_name,
             genre_cte_stmt.c.genre
        )
        .join(band_scores, recent_albums_ranked_by_year.c.band_id == band_scores.c.band_id, isouter=True)
        .join(genre_cte_stmt, genre_cte_stmt.c.band_id == recent_albums_ranked_by_year.c.band_id)
        .where(recent_albums_ranked_by_year.c.rank_by_year == 1, band_scores.c.total_score > 50, recent_albums_ranked_by_year.c.band_id.notin_(selected_band_ids))
        .order_by(None).order_by(func.random()).limit(limit2)
    ).all()

    print(first_branch_results)
    print(second_results)

    final_combined_results = first_branch_results + second_results
    return final_combined_results
