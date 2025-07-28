# YouTube Tools API Server

A FastAPI-based server that provides convenient endpoints for extracting information from YouTube videos, including video metadata, captions, timestamped transcripts, and available transcript languages.

## Features

- Get video metadata (title, author, thumbnails, etc.)
- Extract video captions/transcripts with language fallback
- Generate timestamped transcripts
- List available transcript languages for videos
- Support for multiple languages in captions
- Webshare proxy integration to avoid IP blocking
- Async processing with parallel execution
- Clean and RESTful API design
- Comprehensive error handling

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

1. Clone the repository:
```bash
git clone https://github.com/zaidmukaddam/youtube-api-server.git
cd youtube-api-server
```

2. Install dependencies using uv (recommended):
```bash
uv sync
```

## Configuration

### Environment Variables

The server supports optional proxy configuration to avoid YouTube's IP blocking:

- `WEBSHARE_PROXY_USERNAME` - Your Webshare proxy username (optional)
- `WEBSHARE_PROXY_PASSWORD` - Your Webshare proxy password (optional)
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)

You can set these in your environment or create a `.env` file in the project root.

### Check Environment Setup

Use the included environment checker:
```bash
python load_env.py
```

This will verify your environment configuration and show which variables are set.

## Running the Server

Start the server using:

```bash
uv run main.py
```

By default, the server runs on:
- Host: 0.0.0.0
- Port: 8000

You can customize these using environment variables:
```bash
export PORT=8080
export HOST=127.0.0.1
uv run main.py
```

## API Endpoints

### 1. Health Check
```http
GET /health
```

**Response:** Server status, proxy configuration, and system information.

### 2. Get Video Metadata
```http
POST /video-data
```

**Request Body:**
```json
{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Response:** Video metadata including title, author, thumbnails, duration, etc.

### 3. List Available Transcript Languages
```http
POST /video-transcript-languages
```

**Request Body:**
```json
{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Response:** List of available transcript languages with details about generated vs manual transcripts.

### 4. Get Video Captions
```http
POST /video-captions
```

**Request Body:**
```json
{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "languages": ["en", "es"]  // Optional, supports fallback
}
```

**Response:** Complete transcript text of the video with automatic language fallback.

### 5. Get Video Timestamps
```http
POST /video-timestamps
```

**Request Body:**
```json
{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "languages": ["en"]  // Optional, supports fallback
}
```

**Response:** List of timestamps with corresponding caption text and timing information.

## Example Usage

### Using curl

```bash
# Health check
curl -X GET "http://localhost:8000/health"

# Get video metadata
curl -X POST "http://localhost:8000/video-data" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# List available languages
curl -X POST "http://localhost:8000/video-transcript-languages" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Get video captions with language fallback
curl -X POST "http://localhost:8000/video-captions" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "languages": ["en", "es"]}'

# Get timestamped transcript
curl -X POST "http://localhost:8000/video-timestamps" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "languages": ["en"]}'
```

### Using Python

```python
import requests

base_url = "http://localhost:8000"
video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Get video metadata
response = requests.post(f"{base_url}/video-data",
                        json={"url": video_url})
metadata = response.json()

# Get captions
response = requests.post(f"{base_url}/video-captions",
                        json={"url": video_url, "languages": ["en"]})
captions = response.json()["captions"]
```

## Testing

The project includes a comprehensive testing script that tests all endpoints with various scenarios:

```bash
chmod +x test_endpoints.sh
./test_endpoints.sh
```

Or test against a custom server:
```bash
./test_endpoints.sh http://your-server:8000
```

The test script covers:
- All API endpoints
- Multiple video types (English, Hindi, etc.)
- Language fallback scenarios
- Error handling
- Edge cases and invalid inputs

## Error Handling

The API includes comprehensive error handling for:
- Invalid YouTube URLs (400 Bad Request)
- Missing or unavailable captions (500 Internal Server Error)
- Network errors and proxy issues
- Invalid language codes
- Malformed requests (422 Unprocessable Entity)
- Server connectivity issues

## Proxy Support

The server supports Webshare proxy integration to avoid YouTube's IP blocking:

1. Sign up for a [Webshare](https://www.webshare.io/) account
2. Set your credentials as environment variables:
   ```bash
   export WEBSHARE_PROXY_USERNAME="your_username"
   export WEBSHARE_PROXY_PASSWORD="your_password"
   ```
3. Restart the server - proxy will be automatically enabled

## Performance Features

- **Async Processing**: All transcript operations run asynchronously
- **Parallel Execution**: Blocking operations are executed in background threads
- **Language Fallback**: Automatic fallback to available languages
- **Proxy Rotation**: Webshare proxy integration for reliable access

## Dependencies

The project uses these main dependencies:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `youtube-transcript-api` - YouTube transcript extraction
- `pydantic` - Data validation
- `gunicorn` - Production WSGI server

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run the tests (`./test_endpoints.sh`)
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Clone and install dependencies:
```bash
git clone https://github.com/zaidmukaddam/youtube-api-server.git
cd youtube-api-server
uv sync
```

2. Check environment setup:
```bash
python load_env.py
```

3. Run the server:
```bash
python main.py
```

4. Run tests:
```bash
./test_endpoints.sh
```

Please make sure to test your changes with the provided test script before submitting.
