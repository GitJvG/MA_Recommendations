from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from MA_Scraper.app.models import Discography, Band, Users
from flask_login import login_required, current_user
from MA_Scraper.app.utils import render_with_base, Like_bands, liked_bands
import re
import unicodedata
from sqlalchemy import and_, func
from MA_Scraper.app.db import Session
from collections import defaultdict
from MA_Scraper.app.YT import YT

extension = Blueprint('extension', __name__)

def normalize_text(text):
    # Replace different types of dashes with a standard hyphen
    text = text.replace('–', '-')  # en dash
    text = text.replace('—', '-')  # em dash
    text = text.replace('−', '-')  # minus sign
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return text.strip()

def extract_keywords(title):
    title = normalize_text(title)
    title = re.sub(r'\([^)]*\)', '', title)
    title = re.sub(r'\([^)]*\)', '', title)
    title = re.sub(r'\[[^]]*\]', '', title)
    title = re.sub(r'\*[^*]*\*', '', title)
    title = re.sub(r'\*\*[^*]*\*\*', '', title)

    parts = re.split(r'[-|]', title)
    keywords = [part.strip() for part in parts if part.strip()]
    keywords = [re.sub(r'\b(full album|hd|stream|vinyl)\b', '', keyword).strip() for keyword in keywords]
    keywords = [keyword for keyword in keywords if keyword]
    keywords = keywords[:2]

    return keywords if len(keywords) > 1 else None

def import_playlist(playlist_url, current_user_id):
    videos = YT.get_playlist_videos(playlist_url)
    cleaned_videos = [(video, extract_keywords(video)) for video in videos]

    band_matches = defaultdict(lambda: {"video_titles": [], "band_name": None})
    no_match_videos = []
    newly_liked_count = 0

    for original_video_title, video_keywords in cleaned_videos:
        if video_keywords is None:
            no_match_videos.append(original_video_title)
        else:
            band_name, *rest = video_keywords
            album_name = rest[0] if rest else None

            result = Session.query(Discography.band_id, Band.name).join(Band, Band.band_id == Discography.band_id).filter(
                and_(
                    func.unaccent(func.lower(Band.name)) == band_name,
                    func.unaccent(func.lower(Discography.name)).ilike(f"%{album_name.lower()}%") if album_name else True
                )
            ).first()

            if result:
                band_id, band_name = result
                band_matches[band_id]["video_titles"].append(original_video_title)
                band_matches[band_id]["band_name"] = band_name
            else:
                band_results = Session.query(Band.band_id, Band.name).filter(
                    func.unaccent(func.lower(Band.name)) == band_name
                ).all()

                if len(band_results) == 1:
                    band_id, band_name = band_results[0]
                    band_matches[band_id]["video_titles"].append(original_video_title)
                    band_matches[band_id]["band_name"] = band_name
                else:
                    no_match_videos.append(original_video_title)

    result_structure = {
        'success_count': len(videos)-len(no_match_videos),
        'failure_count': len(no_match_videos),
        'matches': []
    }
    liked_bands_set = liked_bands(current_user_id)
    for band_id, data in band_matches.items():
        new = band_id not in liked_bands_set
        result_structure['matches'].append({
            'band_id': band_id,
            'band_name': data["band_name"],
            'video_titles': data["video_titles"],
            'new': new
        })
        if new:
            Like_bands(current_user.id, band_id, 'like')
            newly_liked_count += 1

    if no_match_videos:
        result_structure['matches'].append({
            'band_id': None,
            'band_name': None,
            'video_titles': no_match_videos,
            'new': 'N/A'
        })

    result_structure['newly_liked_count'] = newly_liked_count

    return result_structure

@extension.route('/youtube_import', methods=['GET', 'POST'])
def youtube_import():
    if not current_user.is_authenticated:
        return jsonify({'status': 'error', 'message': 'You need to log in to import playlists.'}), 401
    results = None
    if request.method == "POST":
        playlist_url = request.form.get("playlist_url")
        if playlist_url:
            results = import_playlist(playlist_url, current_user.id)

        return jsonify({
            'success': True,
            'results': results,
            'action': "displayResults"
        })

    return render_with_base('import.html')
    
@extension.route('/ajax/youtube_search', methods=['GET'])
async def youtube_search():
    search_query = request.args.get('q')
    response = await YT.get_video(search_query)
    return response
