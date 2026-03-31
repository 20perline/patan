# patan

**patan** - A lightweight Python library for interacting with Chinese social media platforms.

## Features

- 🚀 **Async HTTP Client**: Built on `httpx` with automatic retries and error handling
- 🔐 **Signature Algorithms**: Built-in A-Bogus and X-Bogus signature generation for Douyin
- 🎯 **Type-Safe**: Full type annotations with Pydantic models
- ⚙️ **Simple Configuration**: Environment variables and `.env` file support
- 🛡️ **Exception Hierarchy**: Comprehensive error types for different failure scenarios
- 💻 **CLI Tool**: Built-in command-line interface for quick testing

## Installation

```bash
# Using uv (recommended)
uv add patan

# Using pip
pip install patan

# With browser cookie support
uv add patan[browser]
pip install patan[browser]
```

## Quick Start

### Method 1: Command-Line Interface (Recommended for Testing)

```bash
# Check configuration
python -m patan config

# Test your setup
python -m patan test

# Fetch user profile
python -m patan user https://www.douyin.com/user/MS4wLjABAAAA...

# Fetch video details
python -m patan video https://www.douyin.com/video/7300000000000000000

# Fetch user posts
python -m patan posts https://www.douyin.com/user/MS4wLjABAAAA... --count 10

# Fetch video comments
python -m patan comments https://www.douyin.com/video/7300000000000000000
```

### Method 2: Python API

```python
import asyncio
from patan import DouyinClient

async def main():
    # Initialize client (reads from .env file)
    client = DouyinClient()

    # Fetch user profile
    user_profile = await client.fetch_user_profile(sec_user_id="MS4wLjABAAAA...")

    # Fetch video details
    video_detail = await client.fetch_video_detail(aweme_id="7300000000000000000")

    # Fetch user posts
    user_posts = await client.fetch_user_post_videos(
        sec_user_id="MS4wLjABAAAA...",
        max_cursor=0,
        count=20
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### URL ID Extraction

```python
async def extract_ids():
    client = DouyinClient()

    # Extract user ID from profile URL
    sec_user_id = await client.get_sec_user_id("https://www.douyin.com/user/MS4wLjABAAAA...")

    # Extract video ID from video URL
    aweme_id = await client.get_aweme_id("https://www.douyin.com/video/7300000000000000000")

    # Extract live stream ID
    webcast_id = await client.get_webcast_id("https://live.douyin.com/123456789")
```

## Configuration

patan uses environment variables and `.env` files for configuration.

### Method 1: .env File (Recommended)

Create a `.env` file in your project root:

```bash
# .env file
COOKIE="your_cookie_here"

# Optional: Proxy settings
# HTTP_PROXY="http://127.0.0.1:7890"
# HTTPS_PROXY="http://127.0.0.1:7890"

# Optional: Custom User-Agent
# USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

### Method 2: Environment Variables

```bash
export COOKIE="your_cookie_here"
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"

python your_script.py
```

### Method 3: Runtime Cookie Update

```python
client = DouyinClient()

# Update cookie at runtime
await client.update_cookie("new_cookie_value")

# Or create config with new cookie
new_config = client.config.with_cookie("new_cookie_value")
client.config = new_config
```

### Configuration Priority

1. Environment variables (highest)
2. `.env` file
3. Default values (lowest)

## CLI Tool Reference

The built-in CLI tool provides quick access to common operations:

### Commands

```bash
# Show configuration status
python -m patan config

# Test API connection
python -m patan test

# Fetch user profile
python -m patan user <douyin_user_url>

# Fetch video details
python -m patan video <douyin_video_url>

# Fetch user posts
python -m patan posts <douyin_user_url> --count 20

# Fetch video comments
python -m patan comments <douyin_video_url>
```

### Examples

```bash
# Check your current configuration
python -m patan config

# Test if everything works
python -m patan test

# Get user information
python -m patan user https://www.douyin.com/user/MS4wLjABAAAA...

# Get video details
python -m patan video https://www.douyin.com/video/7300000000000000000

# Get user's recent posts
python -m patan posts https://www.douyin.com/user/MS4wLjABAAAA... --count 10

# Get comments from a video
python -m patan comments https://www.douyin.com/video/7300000000000000000
```

## Cookie Acquisition

1. **Manual**: Open browser DevTools (F12) → Network → Copy `Cookie` header
2. **Browser Extension**: Use "EditThisCookie" or "Cookie-Editor"
3. **Programmatic**: Use `browser_cookie3` (optional dependency)

```bash
# Install browser cookie support
pip install patan[browser]
```

## Advanced Usage

### Error Handling

```python
from patan.utils.exceptions import (
    APIConnectionError,
    APINotFoundError,
    APIResponseError,
    APIUnauthorizedError,
    APITimeoutError,
)

try:
    user_profile = await client.fetch_user_profile(sec_user_id="...")
except APIUnauthorizedError:
    print("Authentication failed - check your cookie")
except APINotFoundError:
    print("User not found")
except APITimeoutError:
    print("Request timeout - try again")
except APIResponseError as e:
    print(f"API error: {e}")
```

### Custom Configuration

```python
from patan.douyin import DouyinClient, DouyinConfig

# Load config
config = DouyinConfig.load()
client = DouyinClient(config=config)
```

### Token Generation

```python
# Generate various tokens and IDs
tokens = await client.generate_ms_token()
verify_fp = await client.generate_verify_fp()
web_id = await client.generate_web_id()
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/patan.git
cd patan

# Install dependencies
uv sync --system

# Run tests
uv run pytest tests/

# Check type hints
uv run pyright patan/
```

### Project Structure

```
patan/
├── core/          # Core functionality (HTTP, logging, config)
├── douyin/        # Douyin API client
├── utils/         # Utility functions
└── __init__.py    # Package initialization
```

## Dependencies

| Dependency | Version | Purpose | Required |
|------------|---------|---------|----------|
| httpx | ≥0.27.0 | Async HTTP client | ✅ |
| pydantic | ≥2.0.0 | Data validation | ✅ |
| python-dotenv | ≥1.0.0 | Environment variables | ✅ |
| gmssl | ≥3.2.2 | SM3 signature algorithm | ✅ |
| browser-cookie3 | ≥0.19 | Browser cookies | ❌ |

## Troubleshooting

### Common Issues

1. **Cookie Expired**: Douyin cookies expire frequently. Update your `.env` file
2. **Rate Limiting**: Use appropriate delays between requests
3. **Signature Failures**: Ensure User-Agent matches your browser
4. **Network Issues**: Configure proxy if accessing from outside China

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This library is for educational purposes only. Please respect the terms of service of the platforms you interact with.
