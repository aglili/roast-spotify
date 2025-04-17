from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
from fastapi import Request
from spotipy import  Spotify
from logger import  get_logger

load_dotenv()


LOG = get_logger()

SPOTIPY_CLIENT_ID : str = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET: str = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")


SCOPES = "user-top-read playlist-read-private user-library-read"

def get_spotify_oauth() -> SpotifyOAuth:
    return SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPES,
        cache_path=None,
        show_dialog=True
    )


async def get_spotify_client(request: Request) -> Spotify | None:
    sp_oauth = get_spotify_oauth()
    token_info = request.session.get("token_info")

    if not token_info:
        LOG.error("No token info found in session.")
        return None

    if sp_oauth.is_token_expired(token_info):
        LOG.info("Token expired, attempting refresh.")
        try:
            new_token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            if new_token_info:
                request.session["token_info"] = new_token_info
                token_info = new_token_info
                LOG.info("Token refreshed successfully.")
            else:
                LOG.error("Failed to refresh token, clearing session.")
                request.session.pop("token_info", None)
                return None
        except Exception as e:
            LOG.error(f"Error refreshing token: {e}. Clearing session.")
            request.session.pop("token_info", None)
            return None

    try:
        return Spotify(auth=token_info['access_token'])
    except Exception as e:
        LOG.error(f"Error creating Spotify client with token: {e}")
        return None




