from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user  # Import necessary functions
from sqlalchemy import func, desc
from sqlalchemy.orm import aliased
from .models import users, DIM_Band, UserBandPreference, DIM_Discography, Item, UserCandidateRecommendation, DIM_Similar_Band, db  # Import your User model and db instance
from flask import jsonify
from urllib.parse import quote

# Create a blueprint for main routes
main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index():
    return render_template('index.html', recommendations=None)

@main.route('/update_preferences', methods=['POST'])
@login_required  # Ensure the user is logged in
def update_preferences():
    if request.method == 'POST':
        # Get the favorite bands from the form
        favorite_bands = request.form.get('favorite_bands')
        current_user.favorite_bands = favorite_bands  # Update the user's preferences
        db.session.commit()  # Commit the changes to the database
        flash('Preferences updated successfully!', 'success')  # Flash a success message
        return redirect(url_for('main.index'))  # Redirect back to the index
    
@main.route('/popular_bands', methods=['GET'])
def popular_bands():
    # Get the selected genre from the request arguments
    selected_genre = request.args.get('genre')

    if current_user.is_authenticated:
        interacted_band_ids = db.session.query(UserBandPreference.band_id).filter_by(user_id=current_user.id).all()
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

    return render_template('popular_bands.html', bands=bands, genres=genres, selected_genre=selected_genre)

@main.route('/like_band', methods=['POST'])
def like_band():
    if not current_user.is_authenticated:
        flash('You need to log in to like/dislike bands.')
        return redirect(url_for('auth.login'))

    band_id = request.form['band_id']
    action = request.form['action']  # Use 'action' to determine like, dislike, or remind me

    # Check if the user has already interacted with this band
    existing_preference = UserBandPreference.query.filter_by(user_id=current_user.id, band_id=band_id).first()

    if existing_preference:
        # If the user has already interacted, update based on action
        if action == 'like':
            existing_preference.liked = True
            existing_preference.remind_me = False  # Reset remind_me when liked
        elif action == 'dislike':
            existing_preference.liked = False
            existing_preference.remind_me = False  # Reset remind_me when disliked
        elif action == 'remind':
            existing_preference.remind_me = True
    else:
        # If no previous interaction, create a new preference
        if action == 'like':
            new_preference = UserBandPreference(user_id=current_user.id, band_id=band_id, liked=True, remind_me=False)
        elif action == 'dislike':
            new_preference = UserBandPreference(user_id=current_user.id, band_id=band_id, liked=False, remind_me=False)
        elif action == 'remind':
            new_preference = UserBandPreference(user_id=current_user.id, band_id=band_id, liked=None, remind_me=True)

        db.session.add(new_preference)

    db.session.commit()
    return jsonify({'status': 'success'}), 200

@main.route('/my_bands')
def my_bands():
    if not current_user.is_authenticated:
        flash('You need to log in to view your liked/disliked bands.')
        return redirect(url_for('login'))

    # Get the current user's ID
    user_id = current_user.id

    # Query for the bands the user has liked or disliked
    user_interactions = (
        db.session.query(
            DIM_Band,
            UserBandPreference.liked
        )
        .join(UserBandPreference, UserBandPreference.band_id == DIM_Band.Band_ID)
        .filter(UserBandPreference.user_id == user_id)
        .all()
    )

    # Render the template with the list of user interactions
    return render_template('my_bands.html', user_interactions=user_interactions)

@main.route('/recommend_bands', methods=['GET'])
@login_required
def recommend_bands():
    # Get the current user's ID
    return

# Import your auth blueprint
from .auth import auth as auth_blueprint

# Register the auth blueprint
main.register_blueprint(auth_blueprint)

@main.route('/get_genres', methods=['GET'])
def get_genres():
    genres = db.session.query(Item.genre1).distinct().all()
    distinct_genres = [genre[0] for genre in genres]
    return jsonify(distinct_genres)

import requests
from flask import render_template
from urllib.parse import quote

from flask import render_template
import requests
from urllib.parse import quote

@main.route('/band/<int:band_id>')
def band_detail(band_id):
    band = DIM_Band.query.get(band_id)
    discography = DIM_Discography.query.filter_by(Band_ID=band_id).all()
    types = {album.Type for album in discography}

    # Return albums without Invidious links for now
    albums_without_links = [
        {
            'album_name': album.Album_Name,
            'type': album.Type,
            'year': album.Year,
            'reviews': album.Reviews,
        }
        for album in discography
    ]

    return render_template('band_detail.html', band=band, albums=albums_without_links, types=types)

@main.route('/discovery')
@login_required
def discovery():
    # Get the user's ID
    user_id = current_user.id

    # Step 1: Subquery to get the band IDs the user has interacted with
    interacted_band_ids = (
        db.session.query(UserBandPreference.band_id)
        .filter(UserBandPreference.user_id == user_id)
        .filter(UserBandPreference.liked == True)
        .order_by(func.random())  # Randomly order the bands
        .limit(10)  # Limit to 10 random bands
        .subquery()
    )

    all_interacted_band_ids = (
        db.session.query(UserBandPreference.band_id)
        .filter(UserBandPreference.user_id == user_id)
        .subquery()
    )

    # Create aliases for the Item table
    liked_band_alias = aliased(Item)
    similar_band_alias = aliased(Item)

    # Step 2: Query for similar bands along with the actual liked band name
    similar_bands_query = (
        db.session.query(
            DIM_Similar_Band.Band_ID.label('liked_band_id'),
            liked_band_alias.band_name.label('liked_band_name'),  # Get the name of the liked band
            DIM_Similar_Band.Similar_Artist_ID.label('similar_band_id'),
            similar_band_alias.band_name.label('similar_band_name'),  # Get the name of the similar band
            DIM_Similar_Band.Score
        )
        .filter(DIM_Similar_Band.Similar_Artist_ID.notin_(all_interacted_band_ids))
        .join(liked_band_alias, DIM_Similar_Band.Band_ID == liked_band_alias.item)  # Join to get the liked band's name
        .join(similar_band_alias, DIM_Similar_Band.Similar_Artist_ID == similar_band_alias.item)  # Join to get similar band's name
        .filter(DIM_Similar_Band.Band_ID.in_(interacted_band_ids))  # Include only those similar to interacted bands
        .order_by(desc(DIM_Similar_Band.Score))
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
    return render_template('discovery.html', similar_bands=result)

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
