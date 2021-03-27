
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from bes import REPO_ROOT


YOUTUBE_API = None
SPOTIFY_API = None


###############################################################################
################################ YouTube ######################################
###############################################################################
# Disable OAuthlib's HTTPS verification when running locally.
# *DO NOT* leave this option enabled in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
YOUTUBE_CLIENT_SECRETS_FILE = REPO_ROOT / f'{os.getenv("YOUTUBE_CLIENT_SECRETS_FILE")}'

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly",
          "https://www.googleapis.com/auth/youtube"]


def create_youtube_api(readonly=True):
    # Get credentials and create an API client
    scopes = SCOPES[:1] if readonly else SCOPES[1:]
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        str(YOUTUBE_CLIENT_SECRETS_FILE), scopes)
    credentials = flow.run_console()
    youtube_api = googleapiclient.discovery.build(
        YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
    return youtube_api


def get_or_create_youtube_api(readonly=True):
    global YOUTUBE_API
    if YOUTUBE_API is None:
        YOUTUBE_API = create_youtube_api(readonly)
    return YOUTUBE_API


###############################################################################
################################ Spotify ######################################
###############################################################################
# important links for documentation
# https://developer.spotify.com/documentation/general/guides/scopes/#playlist-modify-public
# https://spotipy.readthedocs.io/en/2.17.1/#module-spotipy.client

SPOTIFY_USER_ID = os.getenv('SPOTIFY_USER_ID')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

def get_or_create_spotify_api():
    global SPOTIFY_API
    if SPOTIFY_API is None:
        SPOTIFY_API = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri="http://localhost:8000",
                scope="playlist-modify-public",
            )
        )
    return SPOTIFY_API
