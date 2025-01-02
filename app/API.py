from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

class YouTubeClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(YouTubeClient, cls).__new__(cls, *args, **kwargs)
            cls._instance.api_key_client = None
            cls._instance.oauth_client = None
            cls._instance.credentials = None
        return cls._instance

    def init_app(self, api_key, oauth_credentials_file=None):
        """Initialize with an API key. Optionally, provide an OAuth credentials file for on-demand authentication."""
        self.api_key_client = build('youtube', 'v3', developerKey=api_key)
        self.oauth_credentials_file = oauth_credentials_file

    def _authenticate_with_oauth(self):
        """Perform OAuth 2.0 authentication flow and return authenticated client."""
        if not self.oauth_credentials_file:
            raise ValueError("OAuth credentials file not provided for authenticated requests.")

        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        credentials = None
        token_file = 'token.pickle'

        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                credentials = pickle.load(token)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.oauth_credentials_file, scopes)
                credentials = flow.run_local_server(port=0)

            with open(token_file, 'wb') as token:
                pickle.dump(credentials, token)

        self.credentials = credentials
        self.oauth_client = build('youtube', 'v3', credentials=credentials)

    def get_client(self, authenticated=False):
        """
        Get the appropriate YouTube client.
        - Default: API key-based client.
        - Authenticated: OAuth-based client, initialized on demand.
        """
        if authenticated:
            if not self.oauth_client:
                self._authenticate_with_oauth()
            return self.oauth_client
        return self.api_key_client