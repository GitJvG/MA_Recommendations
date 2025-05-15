import requests
from bs4 import BeautifulSoup
from MA_Scraper.app import youtube_client, backend, ytm
from flask import jsonify
import re
from typing import Optional, Type, Union

if backend == 'YTDLP' or backend == 'SCRAPE':
    try:
        from yt_dlp import YoutubeDL
    except ImportError as e:
        print(e)

class YTM:
    def get_user_playlists(count):
        records = ytm.get_library_playlists(count)
        return records
    
    def add_to_playlist(playlist_id, video_id):
        ytm.add_playlist_items(playlist_id, video_id)
                                           
class YTAPI:
    def __init__(self):
        self.youtube = youtube_client.get_client()
        
    def get_playlist_videos(self, playlist_url):
        playlist_id = playlist_url.split('list=')[-1]
        video_details = []
        next_page_token = None

        while True:
            playlist_items_request = self.youtube.playlistItems().list(
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
    
    def get_video(self, search_query):
        try:
            search_response = self.youtube.search().list(
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
    GLOBAL_OPTS = {
            'quiet': True,
            'extract_flat': True,
            'no_warnings': True,
            'noprogress': True,
            'extractor_retries': 0, 
            'ignoreerrors': True,
        }
    
    @staticmethod
    def get_playlist_videos(playlist_url):
        YDL_OPTIONS = YTDLP.GLOBAL_OPTS.copy()
        video_details = []

        with YoutubeDL(YDL_OPTIONS) as ydl:
            info_dict = ydl.extract_info(playlist_url, download=False)
            if not info_dict:
                return []
            if 'entries' in info_dict:
                for entry in info_dict['entries']:
                    video_details.append(entry['title'])

        return video_details
    
    @staticmethod
    def get_video(query):
        YDL_OPTIONS = YTDLP.GLOBAL_OPTS.copy()
        YDL_OPTIONS['noplaylist'] = True

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
    def get_playlist_thumbnail(playlist_url):
        YDL_OPTIONS = YTDLP.GLOBAL_OPTS.copy()
        YDL_OPTIONS['writethumbnail'] = False

        with YoutubeDL(YDL_OPTIONS) as ydl:
            result = ydl.extract_info(playlist_url, download=False)
            if not result:
                return
            if 'thumbnails' in result:
                thumbnail_url = result['thumbnails'][0]['url']
                return thumbnail_url
            else:
                print(f"No thumbnail found for the playlist {playlist_url}")
                return
            
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
        javascript = str(soup.find_all('script'))
        javascript = javascript.encode().decode('unicode_escape')
        secondaryContents = None
        if '"secondaryContents"' in javascript:
            secondaryContents = javascript[javascript.find('"secondaryContents"'):]

        regex = r"\"url\":\"(\/watch\?v=[a-zA-Z0-9_-]+(?:&list=(?!RD)[a-zA-Z0-9_-]+|\\u0026list=(?!RD)[a-zA-Z0-9_-]+)?)"
        # Old method without RD filter included unviewable mix playlists
        # regex = r"\"url\":\"(\/watch\?v=[a-zA-Z0-9_-]+(?:&list=[a-zA-Z0-9_-]+|\\u0026list=[a-zA-Z0-9_-]+)?)"
        secondarysource = False
        if secondaryContents:
            secondary = re.search(regex, secondaryContents)
            if secondary:
                url_match = secondary
                secondarysource = True
            else:
                url_match = re.search(regex, javascript)
        else:
            url_match = re.search(regex, javascript)

        if url_match:
            First_result = url_match.group(1)
            video_id = re.search(r"v=([a-zA-Z0-9_-]+)", First_result)
            playlist_id = re.search(r"list=([a-zA-Z0-9_-]+)", First_result)

            if video_id:
                video_id = video_id.group(1)
                thumbnail_url = False
                if playlist_id:
                    playlist_id = playlist_id.group(1)
                    if secondarysource:
                        string_before_video = secondaryContents[:url_match.start()]
                    else:
                        string_before_video = javascript[:url_match.start()]

                    thumbnail_url_pattern = r"\"url\":\"(https?:\/\/[^\"]+)\""
                    thumbnail_url = re.findall(thumbnail_url_pattern, string_before_video)[-1]
                thumbnail_url = thumbnail_url if thumbnail_url else f"https://i.ytimg.com/vi/{video_id}/0.jpg"

                return jsonify({
                    'playlist_url': f'https://www.youtube.com/embed/videoseries?list={playlist_id}' if playlist_id else None,
                    'video_url': f'https://www.youtube.com/embed/{video_id}',
                    'thumbnail_url': thumbnail_url
                })
            
        return jsonify({
                    'playlist_url': None,
                    'video_url': None,
                    'thumbnail_url': None
                })
            
YT: Optional[Type[Union[YTDLP, YTAPI, SCRAPE]]] = globals()[backend]