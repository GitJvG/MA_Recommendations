from flask import Blueprint, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user  # Import necessary functions
from sqlalchemy import func, desc, and_
from sqlalchemy.orm import aliased
from .models import user, band, users, discography, similar_band, details, genre, genres, member, prefix, candidates, db  # Import your User model and db instance
from urllib.parse import quote
import requests
from app.utils import render_with_base
import random
from datetime import datetime
from urllib.parse import quote

main = Blueprint('main', __name__)

from .auth import auth as auth_blueprint
main.register_blueprint(auth_blueprint)

@main.route('/', methods=['GET'])
def index():
    return render_with_base('index.html')

@main.route('/ajax/featured')
def featured():
    # Simulated in-route cache
    if not hasattr(featured, "_cache"):
        featured._cache = {"date": None, "data": None}

    today = datetime.today()
    random.seed(today.year * 10000 + today.month * 100 + today.day)

    if featured._cache["date"] == today and featured._cache["data"]:
        return jsonify(featured._cache["data"])

    # Run the logic if the cache is outdated
    bands_2024 = db.session.query(band.band_id, band.name).join(discography).filter(discography.year == 2024).all()
    band_ids_2024 = [band[0] for band in bands_2024]

    bands_with_scores = db.session.query(
        band.band_id,
        band.name,
        func.sum(similar_band.score).label('total_score')
    ).join(similar_band, band.band_id == similar_band.band_id).filter(band.band_id.in_(band_ids_2024)) \
        .group_by(band.band_id).order_by(func.sum(similar_band.score).desc()).all()
    
    top_bands = bands_with_scores[:min(len(bands_with_scores), 200)]

    selected_bands = random.sample(top_bands, min(5, len(top_bands)))

    result = [
        {"band_id": band.band_id, "name": band.name} for band in selected_bands
    ]

    featured._cache["date"] = today
    featured._cache["data"] = result

    return jsonify(result)

@main.route('/ajax/recommended')
def recommended():
    if not hasattr(recommended, "_cache"):
        recommended._cache = {"date": None, "data": None}

    today = datetime.today()
    random.seed(today.year * 10000 + today.month * 100 + today.day)

    if featured._cache["date"] == today and recommended._cache["data"]:
        return jsonify(recommended._cache["data"])

    bands = db.session.query(candidates.band_id, band.name).filter(candidates.user_id == current_user.id) \
    .join(band, band.band_id == candidates.band_id).all()

    selected_bands = random.sample(bands, 50)

    result = [
        {"band_id": band.band_id, "name": band.name} for band in selected_bands
    ]

    recommended._cache["date"] = today
    recommended._cache["data"] = result

    return jsonify(result)
    
"""@main.route('/popular_bands', methods=['GET'])
def popular_bands():
    # Get the selected genre from the request arguments
    selected_genre = request.args.get('genre')

    if current_user.is_authenticated:
        interacted_band_ids = db.session.query(users.band_id).filter_by(user_id=current_user.id).all()
        # Convert list of tuples into a flat list
        interacted_band_ids = [band_id for (band_id,) in interacted_band_ids]
    else:
        interacted_band_ids = []

    # Query to fetch popular bands from the Item model, with an optional genre filter
    query = db.session.query(Item).filter(~Item.item.in_(interacted_band_ids))

    if selected_genre:
        query = query.filter(
            (Item.genre1 == selected_genre) | 
            (Item.genre2 == selected_genre) | 
            (Item.genre3 == selected_genre) | 
            (Item.genre4 == selected_genre)
        )

    # Order by the score (or any other popularity metric)
    bands = query.order_by(Item.score.desc()).limit(30).all()

    # Fetch distinct genres to populate the dropdown
    genres = db.session.query(Item.genre1).distinct().all()

    return render_template('popular_bands.html', bands=bands, genres=genres, selected_genre=selected_genre)"""

@main.route('/like_band', methods=['POST'])
def like_band():
    if not current_user.is_authenticated:
        return jsonify({'status': 'error', 'message': 'You need to log in to like/dislike bands.'}), 401

    data = request.get_json()
    band_id = data.get('band_id')
    action = data.get('action')

    now = datetime.now().replace(microsecond=0)
    existing_preference = users.query.filter_by(user_id=current_user.id, band_id=band_id).first()

    if existing_preference:
        if action == 'like':
            existing_preference.liked = True
            existing_preference.liked_date = now
        elif action == 'dislike':
            existing_preference.liked = False
            existing_preference.liked_date = now
        elif action == 'remind':
            existing_preference.remind_me = True
            existing_preference.remind_me_date = now
    else:
        if action == 'like':
            new_preference = users(user_id=current_user.id, band_id=band_id, liked=True, remind_me=False, liked_date=now)
        elif action == 'dislike':
            new_preference = users(user_id=current_user.id, band_id=band_id, liked=False, remind_me=False, liked_date=now)
        elif action == 'remind':
            new_preference = users(user_id=current_user.id, band_id=band_id, liked=False, remind_me=True, remind_me_date=now)
        db.session.add(new_preference)

    db.session.commit()
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
        exact_matches = (
            db.session.query(band.band_id, band.name)
            .filter(db.func.lower(band.name) == query).all()
            )
        print(len(exact_matches))
        if len(exact_matches) == 1:
            match = exact_matches[0]
            return jsonify({
                'success': True,
                'redirect_url': url_for('main.band_detail', band_id=match.band_id)
            })

        return jsonify({
                'success': True,
                'redirect_url': url_for('main.search', query=query),
            })
    query = request.args.get('query', '').strip().lower()
    return render_with_base('search.html', query=query)

@main.route('/search_results')
def query():
    query = request.args.get('query', '').strip().lower()
    print(query)
    partial_matches = db.session.query(band.band_id, band.name).filter(band.name.ilike(f'%{query}%')).all()
    print(partial_matches)
    return jsonify(results = [{'name': band.name, 'band_id': band.band_id} for band in partial_matches])


@main.route('/band/<int:band_id>')
def band_detail(band_id):
    vdetail = db.session.get(details, band_id)
    name = db.session.get(band, band_id).name
    feedback = db.session.query(users.liked, users.remind_me).filter(and_(users.user_id == current_user.id, users.band_id == band_id)).first()
    vdiscography = discography.query.filter_by(band_id=band_id).all()
    vdiscography.reverse()
    types = {album.type for album in vdiscography}

    # Return albums without Invidious links for now
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
    for similar_band_id, score in similar_band_ids:
        band_data = db.session.query(
            band.band_id,
            band.name.label('band_name'),
            genre.name.label('genre_name')
        ) \
        .join(genres, genres.band_id == band.band_id) \
        .filter(genres.type == 'genre') \
        .join(genre, genres.item_id == genre.genre_id) \
        .filter(band.band_id == similar_band_id) \
        .all()

        if band_data:
            vgenres = [data.genre_name.title() for data in band_data]
            vgenres_string = ', '.join(vgenres)

            similar_bands.append({
                "band_id": band_data[0].band_id,
                "name": band_data[0].band_name,
                "score": score,
                "genre": vgenres_string
            })

    return jsonify(similar_bands)

"""@main.route('/discovery')
@login_required
def discovery():
    # Get the user's ID
    user_id = current_user.id

    # Step 1: Subquery to get the band IDs the user has interacted with
    interacted_band_ids = (
        db.session.query(users.band_id)
        .filter(users.user_id == user_id)
        .filter(users.liked == True)
        .order_by(func.random())  # Randomly order the bands
        .limit(10)  # Limit to 10 random bands
        .subquery()
    )

    all_interacted_band_ids = (
        db.session.query(users.band_id)
        .filter(users.user_id == user_id)
        .subquery()
    )

    # Create aliases for the Item table
    liked_band_alias = aliased(Item)
    similar_band_alias = aliased(Item)

    # Step 2: Query for similar bands along with the actual liked band name
    similar_bands_query = (
        db.session.query(
            similar_band.band_id.label('liked_band_id'),
            liked_band_alias.band_name.label('liked_band_name'),  # Get the name of the liked band
            similar_band.similar_id.label('similar_band_id'),
            similar_band_alias.band_name.label('similar_band_name'),  # Get the name of the similar band
            similar_band.Score
        )
        .filter(similar_band.similar_id.notin_(all_interacted_band_ids))
        .join(liked_band_alias, similar_band.band_id == liked_band_alias.item)  # Join to get the liked band's name
        .join(similar_band_alias, similar_band.similar_id == similar_band_alias.item)  # Join to get similar band's name
        .filter(similar_band.band_id.in_(interacted_band_ids))  # Include only those similar to interacted bands
        .order_by(desc(similar_band.Score))
    )

    # Step 3: Create a subquery from similar_bands_query
    similar_bands_subquery = similar_bands_query.subquery()

    # Final selection to limit to 2 similar bands per liked band
    ranked_similar_bands = (
        db.session.query(
            similar_bands_subquery.c.liked_band_id,
            similar_bands_subquery.c.liked_band_name,  # Use the actual liked band name here
            similar_bands_subquery.c.similar_band_id,
            similar_bands_subquery.c.similar_band_name,
            similar_bands_subquery.c.Score,
            func.row_number().over(partition_by=similar_bands_subquery.c.liked_band_id, order_by=desc(similar_bands_subquery.c.Score)).label('rank')
        )
    )

    # Create the subquery from ranked_similar_bands to filter
    ranked_similar_bands_subquery = ranked_similar_bands.subquery()

    # Filter to keep only the top 2 similar bands per liked band
    top_similar_bands = (
        db.session.query(ranked_similar_bands_subquery)
        .filter(ranked_similar_bands_subquery.c.rank <= 2)
        .all()
    )

    # Step 4: Prepare the final result structure
    result = {}
    for row in top_similar_bands:
        liked_band_id = row.liked_band_id
        if liked_band_id not in result:
            result[liked_band_id] = {
                'liked_band_name': row.liked_band_name,  # Use the liked band's name
                'similar_bands': []
            }
        result[liked_band_id]['similar_bands'].append({
            'similar_band_id': row.similar_band_id,
            'similar_band_name': row.similar_band_name,
            'score': row.Score
        })

    # Step 5: Pass similar bands to the template
    return render_template('discovery.html', similar_bands=result)"""

@main.route('/fetch_video/<album_id>', methods=['GET'])
def fetch_video():
    album_name = request.args.get('album_name')
    band = request.args.get('Band_Name')
    
    invidious_base_url = "https://inv.nadeko.net/api/v1/search"
    search_query = f"{quote(band)} {quote(album_name)}"
    
    try:
        response = requests.get(f"{invidious_base_url}?q={search_query}")
        response.raise_for_status()
        video_data = response.json()

        if video_data and len(video_data) > 0:  # Check if there's at least one result
            video_id = video_data[0]['videoId']  # Get the first video ID
            video_url = f"https://inv.nadeko.net/embed/{video_id}"  # Embed URL
            return jsonify({'video_url': video_url})
        else:
            return jsonify({'error': 'No video found'}), 404

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500