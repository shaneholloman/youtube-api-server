import json
import os
import asyncio
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import urlopen
from typing import Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Load environment variables from .env file
try:
    from load_env import load_env_file
    load_env_file()
    print(f"[{datetime.now()}] Environment variables loaded from .env file")
except ImportError:
    print(f"[{datetime.now()}] load_env.py not found - using system environment variables only")
except Exception as e:
    print(f"[{datetime.now()}] Error loading .env file: {e}")

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.proxies import GenericProxyConfig
    print(f"[{datetime.now()}] Successfully imported YouTubeTranscriptApi and GenericProxyConfig")
except ImportError:
    print(f"[{datetime.now()}] ERROR: Failed to import youtube_transcript_api")
    raise ImportError(
        "`youtube_transcript_api` not installed. Please install using `pip install youtube_transcript_api`"
    )

# Configure Webshare proxy to avoid IP blocking using environment variables
def get_webshare_config():
    """Get Webshare proxy configuration from environment variables."""
    proxy_url = os.getenv("WEBSHARE_PROXY")

    if not proxy_url:
        print(f"[{datetime.now()}] WARNING: Webshare proxy credentials not found in environment variables")
        print(f"[{datetime.now()}] Set WEBSHARE_PROXY to enable proxy")
        return None

    print(f"[{datetime.now()}] Webshare proxy configuration loaded from environment variables")
    return GenericProxyConfig(
        http_url=proxy_url,
        https_url=proxy_url
    )

WEBSHARE_PROXY_CONFIG = get_webshare_config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"[{datetime.now()}] ========================================")
    print(f"[{datetime.now()}] YouTube API Server Starting Up")
    print(f"[{datetime.now()}] ========================================")
    print(f"[{datetime.now()}] Available endpoints:")
    print(f"[{datetime.now()}]   - GET  /health")
    print(f"[{datetime.now()}]   - POST /video-data")
    print(f"[{datetime.now()}]   - POST /video-captions")
    print(f"[{datetime.now()}]   - POST /video-timestamps")
    print(f"[{datetime.now()}]   - POST /video-transcript-languages")
    proxy_status = "enabled" if WEBSHARE_PROXY_CONFIG else "disabled"
    print(f"[{datetime.now()}] Proxy Status: Webshare proxy {proxy_status}")
    print(f"[{datetime.now()}] Parallel Processing: Enabled with asyncio.to_thread()")
    print(f"[{datetime.now()}] ========================================")

    yield

    # Shutdown
    print(f"[{datetime.now()}] ========================================")
    print(f"[{datetime.now()}] YouTube API Server Shutting Down")
    print(f"[{datetime.now()}] ========================================")

app = FastAPI(title="YouTube Tools API", lifespan=lifespan)
print(f"[{datetime.now()}] FastAPI app initialized")

class YouTubeTools:
    @staticmethod
    def get_youtube_video_id(url: str) -> Optional[str]:
        """Function to get the video ID from a YouTube URL."""
        print(f"[{datetime.now()}] get_youtube_video_id called with URL: {url}")

        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        print(f"[{datetime.now()}] Parsed hostname: {hostname}")

        if hostname == "youtu.be":
            video_id = parsed_url.path[1:]
            print(f"[{datetime.now()}] Extracted video ID from youtu.be: {video_id}")
            return video_id
        if hostname in ("www.youtube.com", "youtube.com"):
            if parsed_url.path == "/watch":
                query_params = parse_qs(parsed_url.query)
                video_id = query_params.get("v", [None])[0]
                print(f"[{datetime.now()}] Extracted video ID from watch URL: {video_id}")
                return video_id
            if parsed_url.path.startswith("/embed/"):
                video_id = parsed_url.path.split("/")[2]
                print(f"[{datetime.now()}] Extracted video ID from embed URL: {video_id}")
                return video_id
            if parsed_url.path.startswith("/v/"):
                video_id = parsed_url.path.split("/")[2]
                print(f"[{datetime.now()}] Extracted video ID from /v/ URL: {video_id}")
                return video_id

        print(f"[{datetime.now()}] ERROR: Could not extract video ID from URL: {url}")
        return None

    @staticmethod
    def get_video_data(url: str) -> dict:
        """Function to get video data from a YouTube URL."""
        print(f"[{datetime.now()}] get_video_data called with URL: {url}")

        if not url:
            print(f"[{datetime.now()}] ERROR: No URL provided to get_video_data")
            raise HTTPException(status_code=400, detail="No URL provided")

        try:
            video_id = YouTubeTools.get_youtube_video_id(url)
            if not video_id:
                print(f"[{datetime.now()}] ERROR: Invalid YouTube URL: {url}")
                raise HTTPException(status_code=400, detail="Invalid YouTube URL")
            print(f"[{datetime.now()}] Video ID extracted: {video_id}")
        except Exception as e:
            print(f"[{datetime.now()}] ERROR: Exception while getting video ID: {str(e)}")
            raise HTTPException(status_code=400, detail="Error getting video ID from URL")

        try:
            params = {"format": "json", "url": f"https://www.youtube.com/watch?v={video_id}"}
            oembed_url = "https://www.youtube.com/oembed"
            query_string = urlencode(params)
            full_url = oembed_url + "?" + query_string
            print(f"[{datetime.now()}] Making request to oEmbed API: {full_url}")

            with urlopen(full_url) as response:
                response_text = response.read()
                print(f"[{datetime.now()}] Received response from oEmbed API")
                video_data = json.loads(response_text.decode())
                print(f"[{datetime.now()}] Successfully parsed video data JSON")

                clean_data = {
                    "title": video_data.get("title"),
                    "author_name": video_data.get("author_name"),
                    "author_url": video_data.get("author_url"),
                    "type": video_data.get("type"),
                    "height": video_data.get("height"),
                    "width": video_data.get("width"),
                    "version": video_data.get("version"),
                    "provider_name": video_data.get("provider_name"),
                    "provider_url": video_data.get("provider_url"),
                    "thumbnail_url": video_data.get("thumbnail_url"),
                }
                print(f"[{datetime.now()}] Video data retrieved: Title='{clean_data.get('title')}', Author='{clean_data.get('author_name')}'")
                return clean_data
        except Exception as e:
            print(f"[{datetime.now()}] ERROR: Exception while getting video data: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting video data: {str(e)}")

    @staticmethod
    def _create_youtube_api():
        """Create a YouTubeTranscriptApi instance with proxy config."""
        if WEBSHARE_PROXY_CONFIG:
            return YouTubeTranscriptApi(proxy_config=WEBSHARE_PROXY_CONFIG)
        else:
            print(f"[{datetime.now()}] WARNING: Creating YouTubeTranscriptApi without proxy - may be subject to IP blocking")
            return YouTubeTranscriptApi()

    @staticmethod
    def _get_transcript_with_fallback(video_id: str, languages: Optional[List[str]] = None):
        """Get transcript with language fallback logic."""
        ytt_api = YouTubeTools._create_youtube_api()

        # First, list available transcripts
        transcript_list = ytt_api.list(video_id)
        available_languages = [t.language_code for t in transcript_list]

        # Determine which language to use
        if languages:
            # Try requested languages first
            for lang in languages:
                if lang in available_languages:
                    return ytt_api.fetch(video_id, languages=[lang]), available_languages
            # If none found, use first available
            return ytt_api.fetch(video_id, languages=[available_languages[0]]), available_languages
        else:
            # No languages specified, prefer English
            if 'en' in available_languages:
                return ytt_api.fetch(video_id, languages=['en']), available_languages
            else:
                return ytt_api.fetch(video_id, languages=[available_languages[0]]), available_languages

    @staticmethod
    async def get_video_captions(url: str, languages: Optional[List[str]] = None) -> str:
        """Get captions from a YouTube video using the new API."""
        print(f"[{datetime.now()}] get_video_captions called with URL: {url}, languages: {languages}")

        if not url:
            print(f"[{datetime.now()}] ERROR: No URL provided to get_video_captions")
            raise HTTPException(status_code=400, detail="No URL provided")

        try:
            video_id = YouTubeTools.get_youtube_video_id(url)
            if not video_id:
                print(f"[{datetime.now()}] ERROR: Invalid YouTube URL: {url}")
                raise HTTPException(status_code=400, detail="Invalid YouTube URL")
            print(f"[{datetime.now()}] Video ID extracted: {video_id}")
        except Exception as e:
            print(f"[{datetime.now()}] ERROR: Exception while getting video ID: {str(e)}")
            raise HTTPException(status_code=400, detail="Error getting video ID from URL")

        try:
            print(f"[{datetime.now()}] Fetching transcript in background thread...")

            # Run the blocking operation in a background thread
            fetched_transcript, available_languages = await asyncio.to_thread(
                YouTubeTools._get_transcript_with_fallback, video_id, languages
            )

            print(f"[{datetime.now()}] Available transcript languages: {available_languages}")

            if fetched_transcript:
                print(f"[{datetime.now()}] Transcript fetched successfully")
                print(f"[{datetime.now()}] Transcript info - Language: {fetched_transcript.language}, Code: {fetched_transcript.language_code}, Generated: {fetched_transcript.is_generated}")
                print(f"[{datetime.now()}] Number of snippets: {len(fetched_transcript)}")

                # Extract text from the fetched transcript object
                caption_text = " ".join(snippet.text for snippet in fetched_transcript)
                print(f"[{datetime.now()}] Combined caption text length: {len(caption_text)} characters")
                return caption_text

            print(f"[{datetime.now()}] WARNING: No captions found for video")
            return "No captions found for video"
        except Exception as e:
            print(f"[{datetime.now()}] ERROR: Exception while getting captions: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting captions for video: {str(e)}")

    @staticmethod
    async def get_video_timestamps(url: str, languages: Optional[List[str]] = None) -> List[str]:
        """Generate timestamps for a YouTube video based on captions using the new API."""
        print(f"[{datetime.now()}] get_video_timestamps called with URL: {url}, languages: {languages}")

        if not url:
            print(f"[{datetime.now()}] ERROR: No URL provided to get_video_timestamps")
            raise HTTPException(status_code=400, detail="No URL provided")

        try:
            video_id = YouTubeTools.get_youtube_video_id(url)
            if not video_id:
                print(f"[{datetime.now()}] ERROR: Invalid YouTube URL: {url}")
                raise HTTPException(status_code=400, detail="Invalid YouTube URL")
            print(f"[{datetime.now()}] Video ID extracted: {video_id}")
        except Exception as e:
            print(f"[{datetime.now()}] ERROR: Exception while getting video ID: {str(e)}")
            raise HTTPException(status_code=400, detail="Error getting video ID from URL")

        try:
            print(f"[{datetime.now()}] Fetching transcript in background thread...")

            # Run the blocking operation in a background thread
            fetched_transcript, available_languages = await asyncio.to_thread(
                YouTubeTools._get_transcript_with_fallback, video_id, languages
            )

            print(f"[{datetime.now()}] Available transcript languages: {available_languages}")
            print(f"[{datetime.now()}] Transcript fetched successfully")
            print(f"[{datetime.now()}] Processing {len(fetched_transcript)} snippets into timestamps")

            timestamps = []
            for i, snippet in enumerate(fetched_transcript):
                start = int(snippet.start)
                minutes, seconds = divmod(start, 60)
                timestamp = f"{minutes}:{seconds:02d} - {snippet.text}"
                timestamps.append(timestamp)

                if i < 5:  # Log first 5 timestamps as sample
                    print(f"[{datetime.now()}] Sample timestamp [{i}]: {timestamp}")

            print(f"[{datetime.now()}] Generated {len(timestamps)} timestamps")
            return timestamps
        except Exception as e:
            print(f"[{datetime.now()}] ERROR: Exception while generating timestamps: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating timestamps: {str(e)}")

    @staticmethod
    async def get_video_transcript_languages(url: str) -> List[dict]:
        """List available transcript languages for a video."""
        print(f"[{datetime.now()}] get_video_transcript_languages called with URL: {url}")

        if not url:
            print(f"[{datetime.now()}] ERROR: No URL provided")
            raise HTTPException(status_code=400, detail="No URL provided")

        try:
            video_id = YouTubeTools.get_youtube_video_id(url)
            if not video_id:
                print(f"[{datetime.now()}] ERROR: Invalid YouTube URL: {url}")
                raise HTTPException(status_code=400, detail="Invalid YouTube URL")
            print(f"[{datetime.now()}] Video ID extracted: {video_id}")
        except Exception as e:
            print(f"[{datetime.now()}] ERROR: Exception while getting video ID: {str(e)}")
            raise HTTPException(status_code=400, detail="Error getting video ID from URL")

        try:
            print(f"[{datetime.now()}] Listing available transcripts in background thread...")

            def list_transcripts(video_id):
                ytt_api = YouTubeTools._create_youtube_api()
                return ytt_api.list(video_id)

            # Run the blocking operation in a background thread
            transcript_list = await asyncio.to_thread(list_transcripts, video_id)

            languages_info = []
            for transcript in transcript_list:
                lang_info = {
                    "language": transcript.language,
                    "language_code": transcript.language_code,
                    "is_generated": transcript.is_generated,
                    "is_translatable": transcript.is_translatable
                }
                languages_info.append(lang_info)
                print(f"[{datetime.now()}] Found transcript: {transcript.language} ({transcript.language_code}) - Generated: {transcript.is_generated}")

            print(f"[{datetime.now()}] Found {len(languages_info)} available transcript languages")
            return languages_info

        except Exception as e:
            print(f"[{datetime.now()}] ERROR: Exception while listing transcript languages: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error listing transcript languages: {str(e)}")

class YouTubeRequest(BaseModel):
    url: str
    languages: Optional[List[str]] = None

@app.post("/video-data")
async def get_video_data(request: YouTubeRequest):
    """Endpoint to get video metadata"""
    print(f"[{datetime.now()}] POST /video-data endpoint called")
    print(f"[{datetime.now()}] Request data: url={request.url}, languages={request.languages}")

    result = YouTubeTools.get_video_data(request.url)
    print(f"[{datetime.now()}] Returning video data response")
    return result

@app.post("/video-captions")
async def get_video_captions(request: YouTubeRequest):
    """Endpoint to get video captions"""
    print(f"[{datetime.now()}] POST /video-captions endpoint called")
    print(f"[{datetime.now()}] Request data: url={request.url}, languages={request.languages}")

    captions = await YouTubeTools.get_video_captions(request.url, request.languages)
    print(f"[{datetime.now()}] Returning captions response")
    return {"captions": captions}

@app.post("/video-timestamps")
async def get_video_timestamps(request: YouTubeRequest):
    """Endpoint to get video timestamps"""
    print(f"[{datetime.now()}] POST /video-timestamps endpoint called")
    print(f"[{datetime.now()}] Request data: url={request.url}, languages={request.languages}")

    timestamps = await YouTubeTools.get_video_timestamps(request.url, request.languages)
    print(f"[{datetime.now()}] Returning timestamps response")
    return {"timestamps": timestamps}

@app.post("/video-transcript-languages")
async def get_video_transcript_languages(request: YouTubeRequest):
    """Endpoint to list available transcript languages for a video"""
    print(f"[{datetime.now()}] POST /video-transcript-languages endpoint called")
    print(f"[{datetime.now()}] Request data: url={request.url}")

    languages_info = await YouTubeTools.get_video_transcript_languages(request.url)
    print(f"[{datetime.now()}] Returning transcript languages response")
    return {"available_languages": languages_info}

@app.get("/health")
async def health_check():
    """Health check endpoint to verify server and proxy status"""
    print(f"[{datetime.now()}] GET /health endpoint called")

    proxy_status = "enabled" if WEBSHARE_PROXY_CONFIG else "disabled"
    proxy_username = os.getenv("WEBSHARE_PROXY_USERNAME", "not_set")

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "proxy_status": f"webshare_{proxy_status}",
        "proxy_username": proxy_username if WEBSHARE_PROXY_CONFIG else None,
        "parallel_processing": "enabled"
    }

if __name__ == "__main__":
    # Use environment variable for port, default to 8000 if not set
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"[{datetime.now()}] ========================================")
    print(f"[{datetime.now()}] Starting YouTube API Server")
    print(f"[{datetime.now()}] Host: {host}")
    print(f"[{datetime.now()}] Port: {port}")

    if WEBSHARE_PROXY_CONFIG:
        username = os.getenv("WEBSHARE_PROXY_USERNAME", "unknown")
        print(f"[{datetime.now()}] Proxy: Webshare enabled (username: {username})")
    else:
        print(f"[{datetime.now()}] Proxy: Disabled - set WEBSHARE_PROXY_USERNAME and WEBSHARE_PROXY_PASSWORD to enable")

    print(f"[{datetime.now()}] Environment Variables:")
    print(f"[{datetime.now()}]   - WEBSHARE_PROXY_USERNAME: {'Set' if os.getenv('WEBSHARE_PROXY_USERNAME') else 'Not Set'}")
    print(f"[{datetime.now()}]   - WEBSHARE_PROXY_PASSWORD: {'Set' if os.getenv('WEBSHARE_PROXY_PASSWORD') else 'Not Set'}")
    print(f"[{datetime.now()}] ========================================")

    uvicorn.run(app, host=host, port=port)
