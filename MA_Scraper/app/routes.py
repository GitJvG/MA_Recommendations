from flask import Blueprint, request, url_for, jsonify, g, Response
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_
from MA_Scraper.app.models import user, band, users, discography, similar_band, details, genre, genres, member, prefix, candidates, band_logo, db
from MA_Scraper.app import cache_manager
from MA_Scraper.app.utils import render_with_base, Like_bands
from MA_Scraper.app.queries import Above_avg_albums, Max_albums, New_albums
import random
import asyncio
import aiohttp
from datetime import datetime
from MA_Scraper.app.YT import YT
from math import ceil
from functools import wraps
import requests

main = Blueprint('main', __name__)

from MA_Scraper.app.auth import auth as auth_blueprint
from MA_Scraper.app.extension import extension as extension_blueprint
main.register_blueprint(auth_blueprint)
main.register_blueprint(extension_blueprint)

today = datetime.today().date()
random.seed(today.year * 100 + today.month * 10 + today.day)

ROWS = {
    ('/ajax/remind'): 1,
    ('/ajax/featured'): 1,
    ('/ajax/recommended_albums'): 3,
    ('/ajax/known_albums'): 3,
    ('/band/<int:band_id>'): 1,
}

def apply_query_limit(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        endpoint = request.path
        count = min(int(request.args.get('count', 1)), 8)
        items = g.items if endpoint == 'main.index' else g.items
        limit = ROWS.get((endpoint), 1) * count
        kwargs['query_limit'] = limit

        return await func(*args, **kwargs)
    return wrapper

def jsonify_with_row(data):
    endpoint = request.path
    rows = ROWS.get((endpoint), 1)
    return jsonify({
        'data': data,
        'rowsCount': rows,
    })

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

async def fetch_video_for_album(band_id, album_name, album_type, band_name, band_genre, result):
    if album_name:
        video_query = f"{band_name} {album_name} {'Full Album' if album_type == 'Full-length' else album_type}"

        video_response = await YT.get_video(video_query)
        
        if 'video_url' in video_response.json:
            result.append({
                "band_id": band_id,
                "name": band_name,
                "album_name": album_name,
                "album_type": album_type,
                "genre": band_genre,
                "video_url": video_response.json['video_url'],
                "playlist_url": video_response.json['playlist_url'] if video_response.json['playlist_url'] else False,
                "thumbnail_url": video_response.json['thumbnail_url'] if video_response.json['thumbnail_url'] else None
            })

async def fetch_top_albums_with_videos(albums):
    result = []
    tasks = []

    for band_id, album_name, album_type, band_name, band_genre in albums:
        task = fetch_video_for_album(band_id, album_name, album_type, band_name, band_genre, result)
        tasks.append(task)

    await asyncio.gather(*tasks)
    return result

@main.route('/', methods=['GET'])
def index():
    return render_with_base('index.html', main_content_class="index")

@main.route('/ajax/featured')
@apply_query_limit
async def featured(query_limit):
    cache = cache_manager.get_cache()
    if cache:
        return jsonify_with_row(cache)

    alb = New_albums(query_limit)
    result = await fetch_top_albums_with_videos(alb)
    cache_manager.set_cache(result)

    return jsonify_with_row(result)

@main.route('/ajax/remind')
@login_required
@apply_query_limit
async def fetch_remind(query_limit):
    cache = cache_manager.get_cache()
    if cache:
        return jsonify_with_row(cache)
    
    bands = db.session.query(users.band_id).filter(and_(users.user_id == current_user.id, users.remind_me == True)) \
    .join(band, band.band_id == users.band_id).order_by(func.random()).limit(query_limit).all()

    selected_band_ids = [vband[0] for vband in bands]
    Albums = Max_albums(selected_band_ids, True)

    result = await fetch_top_albums_with_videos(Albums)
    cache_manager.set_cache(result)

    return jsonify_with_row(result)
    
@main.route('/ajax/recommended_albums')
@login_required
@apply_query_limit
async def fetch_albums(query_limit):
    cache = cache_manager.get_cache()
    if cache:
        return jsonify_with_row(cache)

    bands = db.session.query(candidates.band_id).filter(candidates.user_id == current_user.id) \
        .outerjoin(users, and_(users.band_id == candidates.band_id, users.user_id == candidates.user_id)) \
        .filter((users.liked == True) | (users.liked == None)) \
        .join(discography, discography.band_id == candidates.band_id) \
        .filter(discography.type.in_(["Full-length", "Split", "EP"])) \
        .group_by(candidates.band_id) \
        .having(func.sum(discography.review_score) > 0) \
        .order_by(func.random()).limit(query_limit).all()

    selected_band_ids = [vband[0] for vband in bands]
    Albums = Max_albums(selected_band_ids)
    
    result = await fetch_top_albums_with_videos(Albums)
    cache_manager.set_cache(result)
    return jsonify_with_row(result)

@main.route('/ajax/above_avg_albums')
@login_required
async def fetch_above_avg_albums():
    bands = request.args.getlist('bands')
    ppb = min(int(request.args.get('count', 1)), 8)

    Albums = Above_avg_albums(bands, ppb)
    result = await fetch_top_albums_with_videos(Albums)
    return jsonify_with_row(result)
    
@main.route('/ajax/known_albums')
@login_required
@apply_query_limit
async def fetch_known_albums(query_limit):
    cache = cache_manager.get_cache()
    if cache:
        return jsonify_with_row(cache)

    bands = db.session.query(users.band_id).filter(users.user_id == current_user.id) \
        .filter(users.liked == True) \
        .join(band, band.band_id == users.band_id) \
        .join(discography, discography.band_id == band.band_id) \
        .filter(discography.type.in_(["Full-length", "Split", "EP"])).distinct(band.band_id).subquery()
    
    bands = db.session.query(bands).order_by(func.random()).limit(query_limit).all()

    selected_band_ids = [vband[0] for vband in bands]
    Albums = Above_avg_albums(selected_band_ids)

    result = await fetch_top_albums_with_videos(Albums)
    cache_manager.set_cache(result)

    return jsonify_with_row(result)
    
@main.route('/like_band', methods=['POST'])
@login_required
def like_band():
    user_id = current_user.id
    data = request.get_json()
    band_id = data.get('band_id')
    action = data.get('action')

    Like_bands(user_id, band_id, action)
    return jsonify({'status': 'success'}), 200

@main.route('/my_bands')
@login_required
def my_bands():
    user_id = current_user.id

    user_interactions = (
        db.session.query(
            band.band_id,
            band.name,
            users.liked,
            users.liked_date
        )
        .join(users, users.band_id == band.band_id)
        .filter(users.user_id == user_id).order_by(users.liked_date.desc()).limit(50)
        .all()
    )

    band_data = [
        {'band_id': band_id, 'name': name, 'liked': liked, 'liked_date': liked_date}
        for band_id, name, liked, liked_date in user_interactions
    ]
    
    return render_with_base('my_bands.html', band_data=band_data)

@main.route('/feedback/ajax')
@login_required
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

@main.route('/import')
@login_required
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

        matches = (
            db.session.query(band.band_id, band.name)
            .filter(or_(func.unaccent(func.lower(band.name)).ilike(f"{query.lower()} %"), func.unaccent(func.lower(band.name)).ilike(f"{query.lower()}")))
            .all()
        )
        if len(matches) == 1:
            match = matches[0]
            return jsonify({
                'success': True,
                'redirect_url': url_for('main.band_detail', band_id=match.band_id)
            })
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
@login_required
def band_detail(band_id):
    vdetail = db.session.get(details, band_id)
    name = db.session.get(band, band_id).name
    feedback = db.session.query(users.liked, users.remind_me).filter(and_(users.user_id == current_user.id, users.band_id == band_id)).first()
    vdiscography = db.session.query(discography).filter_by(band_id=band_id).order_by(discography.year.asc(), discography.album_id.asc()).all()
    vsimilar = db.session.query(similar_band.similar_id, band.name, band.country, band.genre, details.status, details.label).join(band, band.band_id == similar_band.similar_id) \
        .join(details, details.band_id == similar_band.similar_id).filter(similar_band.band_id==band_id).order_by(similar_band.score.desc()).all()
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

    similar = [
        {
            'id': sim.similar_id,
            'name': sim.name,
            'country': sim.country,
            'genre': sim.genre,
            'label': sim.label,
            'status': sim.status
        }
        for sim in vsimilar
    ]

    return render_with_base('band_detail.html', band=vdetail, name=name, feedback=feedback, albums=albums, types=types, similar=similar, title=name)

async def fetch_head(session: aiohttp.ClientSession, url: str):
    async with session.head(url, allow_redirects=True) as response:
        return response.status, url

async def fetch_image(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as response:
        if response.status == 200:
            return await response.read(), response.content_type
        return None, None

@main.route('/ajax/band_logo/<int:band_id>')
async def get_band_logo(band_id):
    import time
    start = time.monotonic()
    stored_logo = db.session.get(band_logo, band_id)
    if stored_logo and stored_logo.data and stored_logo.content_type:
        return Response(stored_logo.data, mimetype=stored_logo.content_type)
    
    async with aiohttp.ClientSession() as http_session:
        band_id_str = str(band_id)
        digits = "/".join(band_id_str[:4])
        file_extensions = ['jpg', 'png', 'gif', 'jpeg']
        urls = [f"https://www.metal-archives.com/images/{digits}/{band_id_str}_logo.{ext}" for ext in file_extensions]

        responses = await asyncio.gather(*[fetch_head(http_session, url) for url in urls])

        for attempt in range(2):
            for (status, resolved_url), ext in zip(responses, file_extensions):
                if status == 200 and resolved_url:
                    image_data, content_type = await fetch_image(http_session, resolved_url)
                    if image_data and content_type:
                        new_logo = band_logo(band_id=band_id, data=image_data, content_type=content_type)
                        db.session.add(new_logo)
                        db.session.commit()
                        end = time.monotonic()
                        print(f"took about {end-start} from metal-arch")
                        return Response(image_data, mimetype=content_type)
        return jsonify('')