from fastapi import  APIRouter,Request,Depends
from dependencies import get_spotify_oauth,get_spotify_client
from fastapi.responses import RedirectResponse,JSONResponse
from groq import Groq
from spotipy import  Spotify
import os
from dotenv import  load_dotenv
from logger import get_logger

router = APIRouter(
    tags=["Routes"]
)

LOG = get_logger()

# Initialize Groq Client
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
try:
    groq_client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    LOG.error(f"Error initializing Groq client: {e}")
    groq_client = None


@router.get("/")
async def read_root():
    """Basic endpoint to check if the API is running."""
    return {"message": "Go to /login to authenticate."}



@router.get("/login")
async def login(request: Request):
    """Redirects user to Spotify for authentication."""
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(auth_url)

@router.get("/logout")
async def logout(request: Request):
    """Clears the session to log the user out."""
    request.session.pop("token_info", None)
    LOG.info("User session cleared (logged out).")
    return RedirectResponse("/api/v1/login")


@router.get("/callback")
async def callback(request: Request, code: str | None = None, error: str | None = None):
    """
    Handles the redirect back from Spotify after user authentication.
    Exchanges the code for tokens and stores them in the session.
    """
    session = request.session
    sp_oauth = get_spotify_oauth()

    if error:
        LOG.error(f"Spotify OAuth Error: {error}")
        return JSONResponse(
            status_code=400,
            content={"message": f"Authentication Failed: {error}"}
        )

    if not code:
        LOG.error("No authorization code received from Spotify.")
        return JSONResponse(
            status_code=400,
            content={"message": "Authentication Failed: No code provided."}
        )

    try:
        token_info = sp_oauth.get_access_token(code, check_cache=False)
        session["token_info"] = token_info
        LOG.info("Successfully obtained tokens and stored in session.")
        return RedirectResponse("/api/v1/roastme")
    except Exception as e:
        LOG.error(f"Error getting access token: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Could not get access token: {e}"}
        )

@router.get("/roastme")
async def get_roast_page(request: Request):
    """Simple page confirming login and providing the roast button/link."""
    if not request.session.get("token_info"):
        return RedirectResponse("/api/v1/login")
    return {"message": "You are logged in! Make a GET request to /roast to get your music taste roasted."}


@router.get("/roast")
async def generate_roast(sp: Spotify | None = Depends(get_spotify_client)):
    """
    Fetches user's music data from Spotify and uses Groq to generate a roast.
    Requires authentication (uses the get_spotify_client dependency).
    """
    if not groq_client:
         return JSONResponse(status_code=503, content={"message": "Groq client not initialized"})

    if not sp:
        LOG.error("Roast endpoint called without valid authentication.")
        return RedirectResponse("/api/v1/login")

    try:

        top_tracks = sp.current_user_top_tracks(limit=20, time_range='short_term')
        track_names = [track['name'] for track in top_tracks['items']] if top_tracks else []

        # Get top artists (medium term, limit 20)
        top_artists = sp.current_user_top_artists(limit=20, time_range='medium_term')
        artist_names = [artist['name'] for artist in top_artists['items']] if top_artists else []
        genres = list(set(genre for artist in top_artists['items'] for genre in artist.get('genres', []))) if top_artists else []



        if not track_names and not artist_names:
            return JSONResponse(status_code=404, content={"message": "Could not find enough music data on Spotify to generate a roast."})

        prompt_data = f"My top artists recently are: {', '.join(artist_names[:10])}.\n"
        prompt_data += f"My top tracks recently are: {', '.join(track_names[:10])}.\n"
        if genres:
            prompt_data += f"Some genres I listen to include: {', '.join(genres[:10])}.\n"

        system_prompt = "You are a witty and sarcastic AI assistant specialized in roasting people based on their music taste. Be funny, slightly mean, but keep it lighthearted. Do not refuse to roast. Respond only with the roast itself, no preamble."
        user_prompt = f"Roast my music taste based on this information:\n{prompt_data}"

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=200,
        )

        roast_content = chat_completion.choices[0].message.content

        return {"roast": roast_content.strip()}

    except Exception as e:
        LOG.error(f"An error occurred during roast generation: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Failed to generate roast: {e}"}
        )
