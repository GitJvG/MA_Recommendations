from flask import Blueprint, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_
from .models import user, band, users, discography, similar_band, details, genre, genres, member, prefix, candidates, db
from app.utils import render_with_base, Like_bands, liked_bands
import random
import asyncio
import aiohttp
from datetime import datetime
from app.YT import YT
from math import ceil

main = Blueprint('main', __name__)

from .auth import auth as auth_blueprint
from .extension import extension as extension_blueprint
main.register_blueprint(auth_blueprint)
main.register_blueprint(extension_blueprint)

def liked(current_user):
    if current_user.is_authenticated:
        liked_bands_set = liked_bands(current_user.id)
    else:
        liked_bands_set = set()
    return liked_bands_set

def get_band_data(band_id):
    band_data = db.session.query(
        band.band_id,
        band.name.label('band_name'),
        genre.name.label('genre_name')
    ) \
    .join(genres, genres.band_id == band.band_id) \
    .filter(genres.type == 'genre') \
    .join(genre, genres.item_id == genre.genre_id) \
    .filter(band.band_id == band_id) \
    .all()

    if band_data:
        vgenres = [data.genre_name.title() for data in band_data]
        vgenres_string = ', '.join(vgenres)

        # Return the band data without `liked` status
        return {
            "band_id": band_data[0].band_id,
            "name": band_data[0].band_name,
            "genre": vgenres_string,
        }

    return None

@main.route('/', methods=['GET'])
def index():
    return render_with_base('index.html')

@main.route('/ajax/featured')
def featured():
    if not hasattr(featured, "_cache"):
        featured._cache = {"date": None, "data": None}

    today = datetime.today().date()
    random.seed(today.year * 10000 + today.month * 100 + today.day)

    if featured._cache["date"] == today and featured._cache["data"]:
        result = featured._cache["data"]
        for vband in result:
            vband["liked"] = vband["band_id"] in liked(current_user)
        random.shuffle(result)
        return jsonify(result)

    bands_2024 = db.session.query(band.band_id).join(discography).filter(discography.year == 2024).all()
    band_ids_2024 = [band[0] for band in bands_2024]

    bands_with_scores = db.session.query(
        band.band_id,
        func.sum(similar_band.score).label('total_score')
    ).join(similar_band, band.band_id == similar_band.band_id).filter(band.band_id.in_(band_ids_2024)) \
        .group_by(band.band_id).order_by(func.sum(similar_band.score).desc()).all()
    
    top_bands = bands_with_scores[:min(len(bands_with_scores), 200)]
    selected_bands = random.sample(top_bands, min(20, len(top_bands)))

    result = []
    for vband in selected_bands:
        band_data = get_band_data(vband.band_id)
        if band_data:
            band_data["liked"] = vband.band_id in liked(current_user)
            result.append(band_data)

    featured._cache["date"] = today
    featured._cache["data"] = result

    return jsonify(result)

@main.route('/ajax/recommended')
def recommended():
    if current_user.is_authenticated:
        if not hasattr(recommended, "_cache"):
            recommended._cache = {"date": None, "data": None}

        today = datetime.today().date()
        random.seed(today.year * 10000 + today.month * 100 + today.day)

        if recommended._cache["date"] == today and recommended._cache["data"]:
            result = recommended._cache["data"]
            for vband in result:
                vband["liked"] = vband["band_id"] in liked(current_user)
            random.shuffle(result)
            return jsonify(result)

        bands = db.session.query(candidates.band_id).filter(candidates.user_id == current_user.id) \
        .join(band, band.band_id == candidates.band_id).all()

        selected_bands = random.sample(bands, 100)

        result = []
        for vband in selected_bands:
            band_data = get_band_data(vband.band_id)
            if band_data:
                band_data["liked"] = vband.band_id in liked(current_user)
                result.append(band_data)

        recommended._cache["date"] = today
        recommended._cache["data"] = result

        return jsonify(result)
    else:
        return jsonify([])

@main.route('/ajax/remind')
def fetch_remind():
    if current_user.is_authenticated:
        if not hasattr(fetch_remind, "_cache"):
            fetch_remind._cache = {"date": None, "data": None}

        today = datetime.today().date()
        random.seed(today.year * 10000 + today.month * 100 + today.day)

        if fetch_remind._cache["date"] == today and fetch_remind._cache["data"]:
            result = fetch_remind._cache["data"]
            for vband in result:
                vband["liked"] = vband["band_id"] in liked(current_user)
            random.shuffle(result)
            return jsonify(result)

        bands = db.session.query(users.band_id).filter(and_(users.user_id == current_user.id, users.remind_me == True)) \
        .join(band, band.band_id == users.band_id).all()

        selected_bands = random.sample(bands, min(50, len(bands)))

        result = []
        for vband in selected_bands:
            band_data = get_band_data(vband.band_id)
            if band_data:
                band_data["liked"] = vband.band_id in liked(current_user)
                result.append(band_data)

        fetch_remind._cache["date"] = today
        fetch_remind._cache["data"] = result

        return jsonify(result)
    else:
        return jsonify([])
    
@main.route('/ajax/recommended_albums')
async def fetch_albums():
    if current_user.is_authenticated:
        if not hasattr(fetch_albums, "_cache"):
            fetch_albums._cache = {"date": None, "data": None}

        today = datetime.today().date()
        random.seed(today.year * 10000 + today.month * 100 + today.day)

        if fetch_albums._cache["date"] == today and fetch_albums._cache["data"]:
            result = fetch_albums._cache["data"]
            for vband in result:
                vband["liked"] = vband["band_id"] in liked(current_user)
                random.shuffle(result)
            return jsonify(result)

        bands = db.session.query(candidates.band_id).filter(candidates.user_id == current_user.id) \
            .join(band, band.band_id == candidates.band_id).all()

        selected_bands = random.sample(bands, 10)
        selected_band_ids = [vband[0] for vband in selected_bands]

        max_scores_subquery = db.session.query(
            discography.band_id,
            func.max(discography.review_score * discography.review_count).label('max_album_score')
        ) \
            .filter(discography.band_id.in_(selected_band_ids)) \
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
            .all()

        async def fetch_video_for_album(band_id, album_name, album_type, band_name, band_genre, result):
            if album_name:
                video_query = f"{band_name} {album_name} {'Full Album' if album_type == 'Full-length' else album_type}"

                video_response = await asyncio.to_thread(YT.get_video, video_query)
                
                if 'video_url' in video_response.json:
                    result.append({
                        "band_id": band_id,
                        "name": band_name,
                        "album_name": album_name,
                        "album_type": album_type,
                        "genre": band_genre,
                        "liked": band_id in liked(current_user),
                        "video_url": video_response.json['video_url'],
                        "playlist_url": video_response.json['playlist_url'] if video_response.json['playlist_url'] else False
                    })

        async def fetch_top_albums_with_videos(top_albums):
            result = []
            tasks = []

            for band_id, album_name, album_type, band_name, band_genre in top_albums:
                task = fetch_video_for_album(band_id, album_name, album_type, band_name, band_genre, result)
                tasks.append(task)

            await asyncio.gather(*tasks)
            return result

        result = await fetch_top_albums_with_videos(top_albums)

        fetch_albums._cache["date"] = today
        fetch_albums._cache["data"] = result

        return jsonify(result)
    else:
        return jsonify([])

@main.route('/like_band', methods=['POST'])
def like_band():
    if not current_user.is_authenticated:
        return jsonify({'status': 'error', 'message': 'You need to log in to like/dislike bands.'}), 401
    user_id = current_user.id
    data = request.get_json()
    band_id = data.get('band_id')
    action = data.get('action')

    Like_bands(user_id, band_id, action)
    return jsonify({'status': 'success'}), 200

@main.route('/my_bands')
def my_bands():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    user_id = current_user.id

    user_interactions = (
        db.session.query(
            band.band_id,
            band.name,
            users.liked,
            users.liked_date
        )
        .join(users, users.band_id == band.band_id)
        .filter(users.user_id == user_id)
        .all()
    )

    band_data = [
        {'band_id': band_id, 'name': name, 'liked': liked, 'liked_date': liked_date}
        for band_id, name, liked, liked_date in user_interactions
    ]
    
    return render_with_base('my_bands.html', band_data=band_data)

@main.route('/feedback/ajax')
def get_bands():
    user_id = current_user.id
    user_interactions = (
        db.session.query(
            band.band_id,
            band.name,
            users.liked,
            users.liked_date,
            users.remind_me,
            users.remind_me_date
        )
        .join(users, users.band_id == band.band_id)
        .filter(users.user_id == user_id)
        .all()
    )

    band_data = [
        {'band_id': band_id, 'name': name, 'liked': liked, 'liked_date': liked_date, 'remind_me': remind_me, 'remind_me_date': remind_me_date}
        for band_id, name, liked, liked_date, remind_me, remind_me_date in user_interactions
    ]
    return jsonify(band_data)

@main.route('/recommend_bands', methods=['GET'])
@login_required
def recommend_bands():
    return

@main.route('/import')
def imports():
    return render_with_base('import.html')

@main.route('/get_genres', methods=['GET'])
def get_genres():
    genres = db.session.query(genre.name).distinct().all()

    distinct_genres = [genre[0] for genre in genres]
    return jsonify(distinct_genres)

@main.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == 'POST':
        query = request.form.get('q', '').strip()

        # Either a full match or the first word
        matches = (
            db.session.query(band.band_id, band.name)
            .filter(or_(func.unaccent(func.lower(band.name)).ilike(f"{query.lower()} %"), func.unaccent(func.lower(band.name)).ilike(f"{query.lower()}")))
            .all()
        )
    	# Directly redirecting to band page when only one result
        if len(matches) == 1:
            match = matches[0]
            return jsonify({
                'success': True,
                'redirect_url': url_for('main.band_detail', band_id=match.band_id)
            })
        # If more than 1 result, redirect to a more lenient searching system and display results on a page.
        return jsonify({
            'success': True,
            'redirect_url': url_for('main.search', query=query),
        })
    
    query = request.args.get('query', '')
    return render_with_base('search.html', query=query)

@main.route('/search_results')
def query():
    query = request.args.get('query', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    per_page = 100

    exact_matches = (
        db.session.query(band.band_id, band.name, band.genre, band.country)
        .filter(func.unaccent(func.lower(band.name)) == query.lower())
    )

    partial_matches = (
        db.session.query(band.band_id, band.name, band.genre, band.country)
        .filter(or_(band.name.ilike(f'% {query} %'), band.name.ilike(f'{query} %')))
    )

    exact_matches_page = exact_matches.paginate(page=page, per_page=per_page, error_out=False)
    partial_matches_page = partial_matches.paginate(page=page, per_page=per_page, error_out=False)


    matches = exact_matches_page.items + [match for match in partial_matches_page.items if match not in exact_matches_page.items]

    total_matches = exact_matches.count() + partial_matches.count()
    total_pages = ceil(total_matches / per_page)

    return jsonify(
        results=[{
            'name': band.name,
            'band_id': band.band_id,
            'genre': band.genre,
            'country': band.country
        } for band in matches],
        total_pages=total_pages,
        current_page=page
    )

@main.route('/band/<int:band_id>')
def band_detail(band_id):
    vdetail = db.session.get(details, band_id)
    name = db.session.get(band, band_id).name
    feedback = db.session.query(users.liked, users.remind_me).filter(and_(users.user_id == current_user.id, users.band_id == band_id)).first()
    vdiscography = db.session.query(discography).filter_by(band_id=band_id).all()

    types = {album.type for album in vdiscography}

    albums = [
        {
            'album_name': album.name,
            'type': album.type,
            'year': album.year,
            'reviews': album.reviews,
        }
        for album in vdiscography
    ]

    return render_with_base('band_detail.html', band=vdetail, name=name, feedback=feedback, albums=albums, types=types, title=name)

@main.route('/ajax/similar_bands/<int:band_id>', methods=['GET'])
def get_similar_bands(band_id):

    similar_band_ids = db.session.query(
        similar_band.similar_id,
        similar_band.score
    ).filter(similar_band.band_id == band_id) \
     .order_by(similar_band.score.desc()) \
     .limit(20).all()

    similar_bands = []
    liked_set = liked(current_user)
    for similar_band_id, score in similar_band_ids:
        band_data = get_band_data(similar_band_id)

        if band_data:
            band_data['score'] = score
            similar_bands.append(band_data)
            band_data["liked"] = band_data["band_id"] in liked_set

    return jsonify(similar_bands)

async def fetch_head(url):
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as response:
            return response.status, url

@main.route('/ajax/band_logo/<int:band_id>')
async def get_band_logo(band_id):
    band_id_str = str(band_id)
    digits = "/".join(band_id_str[:4])
    file_extensions = ['jpg', 'png', 'gif']
    
    urls = [f"https://www.metal-archives.com/images/{digits}/{band_id_str}_logo.{ext}" for ext in file_extensions]

    responses = await asyncio.gather(*[fetch_head(url) for url in urls])

    for response, ext in zip(responses, file_extensions):
        if response[0] == 200:
            return jsonify(response[1])
    
    return jsonify('')