from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import discography, band, users
from flask_login import login_required, current_user
from app.utils import render_with_base, Like_bands, liked_bands
import re
import unicodedata
from sqlalchemy import and_, func
from app import db, youtube_client
from collections import defaultdict
import requests
from yt_dlp import YoutubeDL
from bs4 import BeautifulSoup


extension = Blueprint('extension', __name__)

youtube = youtube_client.get_client()
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

def get_playlist_videos(playlist_url):
    playlist_id = playlist_url.split('list=')[-1]
    video_details = []
    next_page_token = None

    while True:
        playlist_items_request = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=200,
            pageToken=next_page_token
        )
        playlist_items_response = playlist_items_request.execute()

        for item in playlist_items_response['items']:
            video_title = item['snippet']['title']

            video_details.append(video_title)

        next_page_token = playlist_items_response.get('nextPageToken')
        if not next_page_token:
            break

    return video_details

def main(playlist_url, current_user_id):
    videos = get_playlist_videos(playlist_url)
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

            result = db.session.query(discography.band_id, band.name).join(band, band.band_id == discography.band_id).filter(
                and_(
                    func.unaccent(func.lower(band.name)) == band_name,
                    func.unaccent(func.lower(discography.name)).ilike(f"%{album_name.lower()}%") if album_name else True
                )
            ).first()

            if result:
                band_id, band_name = result
                band_matches[band_id]["video_titles"].append(original_video_title)
                band_matches[band_id]["band_name"] = band_name
            else:
                band_results = db.session.query(band.band_id, band.name).filter(
                    func.unaccent(func.lower(band.name)) == band_name
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
            results = main(playlist_url, current_user.id)

        return jsonify({
            'success': True,
            'results': results,
            'action': "displayResults"
        })

    return render_with_base('import.html')

def get_video_id_without_api(search_query):
    """Manually scraped results seem better than those through api, even after tweaking parameters, it has similar performance."""
    query = '+'.join(search_query.split())
    print(query)
    url = f'https://www.youtube.com/results?search_query={query}'
    response = requests.get(url)
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, 'html.parser')

    video_id_match = re.search(r"\"videoId\":\"([^\"]+)\"", str(soup))

    if video_id_match:
        video_id = video_id_match.group(1)
        return jsonify({
            'video_url': f'https://www.youtube.com/embed/{video_id}'
        })
    else:
        return jsonify({'error': 'No video found'}), 404

def get_video_id_with_api(search_query):
    try:
        search_response = youtube.search().list(
            part="snippet",
            q=search_query,
            type="video",
            order="relevance",
        ).execute()

        if 'items' in search_response and len(search_response['items']) > 0:
            video_id = search_response['items'][0]['id']['videoId']
            return jsonify({
                'video_url': f'https://www.youtube.com/embed/{video_id}'
            })
        else:
            return jsonify({'error': 'No video found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

def get_video_with_ytdlp(query):
    YDL_OPTIONS = {
        'noplaylist': True,
        'quiet': True,
        'extract_flat': True
    }

    with YoutubeDL(YDL_OPTIONS) as ydl:
        search_result = ydl.extract_info(f"ytsearch:{query}", download=False)

        # Extract the first result's URL
        if 'entries' in search_result and search_result['entries']:
            video = search_result['entries'][0]
            return jsonify({
                'video_url': f'https://www.youtube.com/embed/{video['id']}'
            }) 
        else:
            return jsonify({'error': 'No video found'}), 404
    
@extension.route('/ajax/youtube_search', methods=['GET'])
def youtube_search():
    search_query = request.args.get('q')
    return get_video_with_ytdlp(search_query)