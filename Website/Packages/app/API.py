from googleapiclient.discovery import build

class YouTubeClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(YouTubeClient, cls).__new__(cls, *args, **kwargs)
            cls._instance.client = None
        return cls._instance

    def init_app(self, api_key):
        if self.client is None:
            self.client = build('youtube', 'v3', developerKey=api_key)

    def get_client(self):
        return self.client
