import requests
from yt_dlp import YoutubeDL
from bs4 import BeautifulSoup
from app import youtube_client, backend
from flask import jsonify
import re
from typing import Optional, Type, Union

class YTAPI:
    youtube = youtube_client.get_client()

    def get_user_playlists():
        youtube = youtube_client.get_client(authenticated=True)
        try:
            response = youtube.playlists().list(
                part="snippet",
                mine=True,
                maxResults=50
            ).execute()

            playlists = []
            for item in response.get('items', []):
                playlists.append({
                    'id': item['id'],
                    'title': item['snippet']['title']
                })

            return {'success': True, 'playlists': playlists}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @classmethod
    def add_video_to_playlist(cls, playlist_id, video_id):
        try:
            request_body = {
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }

            response = cls.youtube.playlistItems().insert(
                part="snippet",
                body=request_body
            ).execute()

            return {
                'success': True,
                'message': 'Video added successfully!',
                'response': response
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
        
    @classmethod
    def get_playlist_videos(cls, playlist_url):
        playlist_id = playlist_url.split('list=')[-1]
        video_details = []
        next_page_token = None

        while True:
            playlist_items_request = cls.youtube.playlistItems().list(
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
    
    @classmethod
    def get_video(cls, search_query):
        try:
            search_response = cls.youtube.search().list(
                part="snippet",
                q=search_query,
                type="video",
                order="relevance",
            ).execute()

            if 'items' in search_response and len(search_response['items']) > 0:
                video_id = search_response['items'][0]['id']['videoId']
                return jsonify({
                    'playlist_url': None,
                    'video_url': f'https://www.youtube.com/embed/{video_id}'
                })
            else:
                return jsonify({'error': 'No video found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
class YTDLP:
    @staticmethod
    def get_playlist_videos(playlist_url):
        YDL_OPTIONS = {
            'quiet': True,  # Suppress output for cleaner results
            'extract_flat': True,  # Extract metadata
        }

        video_details = []

        with YoutubeDL(YDL_OPTIONS) as ydl:
            info_dict = ydl.extract_info(playlist_url, download=False)
            if 'entries' in info_dict:
                for entry in info_dict['entries']:
                    video_details.append(entry['title'])

        return video_details
    
    @staticmethod
    def get_video(query):
        YDL_OPTIONS = {
            'noplaylist': True,
            'quiet': True,
            'extract_flat': True
        }

        with YoutubeDL(YDL_OPTIONS) as ydl:
            search_result = ydl.extract_info(f"ytsearch:{query}", download=False)

            if 'entries' in search_result and search_result['entries']:
                video = search_result['entries'][0]
                return jsonify({
                    'playlist_url': None,
                    'video_url': f'https://www.youtube.com/embed/{video['id']}'
                }) 
            else:
                return jsonify({'error': 'No video found'}), 404
            
    @staticmethod
    def add_video_to_playlist(playlist_url):
        return YTAPI.add_video_to_playlist(playlist_url)
    
    @staticmethod
    def get_user_playlists():
        return YTAPI.get_user_playlists()
            
class SCRAPE:
    @staticmethod
    def get_playlist_videos(playlist_url):
        return YTDLP.get_playlist_videos(playlist_url)

    @staticmethod
    def get_video(search_query):
        """Scrape YouTube search results to extract video and playlist info."""
        query = '+'.join(search_query.split())
        
        url = f'https://www.youtube.com/results?search_query={query}'

        response = requests.get(url)
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to retrieve content'}), 404
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for the first "url":"/watch?" occurrence (can be video or playlist)
        url_match = re.search(r"\"url\":\"(/watch\?v=[a-zA-Z0-9_-]+(?:&list=[a-zA-Z0-9_-]+|\\u0026list=[a-zA-Z0-9_-]+)?)\"", str(soup))

        if url_match:
            # Extract the first result (for playlists it's /watch?v=FirstVideoID\u0026list=PlaylistID)
            First_result = url_match.group(1)

            video_id = re.search(r"v=([a-zA-Z0-9_-]+)", First_result)
            playlist_id = re.search(r"list=([a-zA-Z0-9_-]+)", First_result)

            if video_id:
                video_id = video_id.group(1)
                playlist_id = playlist_id.group(1) if playlist_id else None
                return jsonify({
                    'playlist_url': f'https://www.youtube.com/embed/videoseries?list={playlist_id}' if playlist_id else None,
                    'video_url': f'https://www.youtube.com/embed/{video_id}'
                })
            
        return jsonify({
                    'playlist_url': None,
                    'video_url': None
                })
    
    @staticmethod
    def add_video_to_playlist(playlist_url):
        return YTAPI.add_video_to_playlist(playlist_url)
    
    @staticmethod
    def get_user_playlists():
        return YTAPI.get_user_playlists()
            
YT: Optional[Type[Union[YTDLP, YTAPI, SCRAPE]]] = globals()[backend]