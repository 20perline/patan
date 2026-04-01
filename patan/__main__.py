"""patan CLI - Interactive command-line interface."""

import asyncio
from pathlib import Path
from typing import Any

import typer
from patan.channels.douyin import DouyinClient, DouyinConfig
from patan.core import logger
from patan.core.downloader import VideoDownloader

app = typer.Typer(help="patan - Chinese social media API client library")


@app.command()
def config() -> None:
    """Show current configuration status."""
    typer.echo("🔧 patan Configuration")
    typer.echo("=" * 50)

    try:
        cfg = DouyinConfig.load()

        # Check cookie
        cookie = cfg.headers.get("Cookie", "")
        if cookie:
            typer.echo(f"✅ Cookie: {len(cookie)} characters")
        else:
            typer.echo("❌ Cookie: Not configured")

        # Check proxies
        proxies = cfg.proxies
        if any(proxies.values()):
            typer.echo(f"✅ Proxies: {proxies}")
        else:
            typer.echo("ℹ️  Proxies: Not configured")

        # Show headers
        typer.echo("\n📋 Headers:")
        typer.echo(f"   User-Agent: {cfg.headers.get('User-Agent', 'N/A')[:60]}...")
        typer.echo(f"   Referer: {cfg.headers.get('Referer', 'N/A')}")

        # Show token config
        typer.echo("\n🔑 Token Configuration:")
        typer.echo(f"   MS Token URL: {cfg.ms_token_conf.get('url', 'N/A')}")
        typer.echo(f"   TTWID URL: {cfg.ttwid_conf.get('url', 'N/A')}")

    except Exception as exc:
        typer.echo(f"❌ Error loading configuration: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def test() -> None:
    """Test API connection and configuration."""
    typer.echo("🧪 Testing patan configuration...")
    typer.echo("=" * 50)

    async def run_test() -> None:
        try:
            client = DouyinClient()
            cfg = client.config

            # Test 1: Check configuration
            typer.echo("\n1️⃣  Configuration Check:")
            if cfg.headers.get("Cookie"):
                typer.echo("   ✅ Cookie configured")
            else:
                typer.echo("   ⚠️  Cookie not configured - add COOKIE to .env file")

            # Test 2: Generate tokens
            typer.echo("\n2️⃣  Token Generation:")
            try:
                verify_fp = await client.generate_verify_fp()
                typer.echo(f"   ✅ verify_fp: {verify_fp['verify_fp'][:20]}...")

                web_id = await client.generate_web_id()
                typer.echo(f"   ✅ web_id: {web_id['web_id'][:20]}...")
            except Exception as exc:
                typer.echo(f"   ❌ Token generation failed: {exc}")

            # Test 3: Test URL extraction
            typer.echo("\n3️⃣  URL Extraction:")
            test_url = "https://www.douyin.com/video/7300000000000000000"
            typer.echo(f"   Testing: {test_url}")
            try:
                # This will fail if the URL is invalid, but that's expected
                aweme_id = await client.get_aweme_id(test_url)
                typer.echo(f"   ✅ Extracted aweme_id: {aweme_id}")
            except Exception as exc:
                typer.echo(f"   ℹ️  Expected error (invalid URL): {str(exc)[:50]}...")

            typer.echo("\n✅ Configuration test completed!")
            typer.echo("\n💡 Next steps:")
            typer.echo("   1. Add your COOKIE to .env file")
            typer.echo("   2. Run: python -m patan user <profile_url>")
            typer.echo("   3. Run: python -m patan video <video_url>")

        except Exception as exc:
            typer.echo(f"❌ Test failed: {exc}", err=True)
            logger.exception("Test failed")
            raise typer.Exit(code=1)

    asyncio.run(run_test())


@app.command()
def user(url: str) -> None:
    """Fetch user profile from Douyin URL.

    Args:
        url: Douyin user profile URL

    Example:
        python -m patan user https://www.douyin.com/user/MS4wLjABAAAA...
    """
    typer.echo("👤 Fetching user profile...")
    typer.echo(f"URL: {url}")
    typer.echo("=" * 50)

    async def fetch_user() -> None:
        try:
            client = DouyinClient()

            # Extract sec_user_id from URL
            typer.echo("\n1️⃣  Extracting user ID...")
            sec_user_id = await client.get_sec_user_id(url)
            typer.echo(f"   ✅ sec_user_id: {sec_user_id}")

            # Fetch user profile
            typer.echo("\n2️⃣  Fetching user profile...")
            profile: dict[str, Any] = await client.fetch_user_profile(sec_user_id)

            # Display results
            typer.echo("\n📊 User Profile:")
            if "aweme_info" in profile:
                user_data = profile.get("aweme_info", {}).get("user", {})
                typer.echo(f"   Nickname: {user_data.get('nickname', 'N/A')}")
                typer.echo(f"   Signature: {user_data.get('signature', 'N/A')}")
                typer.echo(f"   Following: {user_data.get('follow_info', {}).get('following_count', 'N/A')}")
                typer.echo(f"   Followers: {user_data.get('follow_info', {}).get('follower_count', 'N/A')}")
                typer.echo(f"   Likes: {user_data.get('user_stats', {}).get('total_favorited', 'N/A')}")
            else:
                typer.echo(f"   Raw data: {profile}")

        except Exception as exc:
            typer.echo(f"❌ Error: {exc}", err=True)
            logger.exception("User fetch failed")
            raise typer.Exit(code=1)

    asyncio.run(fetch_user())


@app.command()
def posts(url: str, count: int = 10) -> None:
    """Fetch user posts from Douyin URL.

    Args:
        url: Douyin user profile URL
        count: Number of posts to fetch

    Example:
        python -m patan posts https://www.douyin.com/user/MS4wLjABAAAA... --count 10
    """
    typer.echo("📝 Fetching user posts...")
    typer.echo(f"URL: {url}")
    typer.echo(f"Count: {count}")
    typer.echo("=" * 50)

    async def fetch_posts() -> None:
        try:
            client = DouyinClient()

            # Extract sec_user_id from URL
            typer.echo("\n1️⃣  Extracting user ID...")
            sec_user_id = await client.get_sec_user_id(url)
            typer.echo(f"   ✅ sec_user_id: {sec_user_id}")

            # Fetch user posts
            typer.echo("\n2️⃣  Fetching posts...")
            posts: dict[str, Any] = await client.fetch_user_post_videos(
                sec_user_id=sec_user_id,
                max_cursor=0,
                count=count
            )

            # Display results
            typer.echo("\n📊 Posts (max_cursor=0):")
            if "aweme_list" in posts:
                aweme_list = posts.get("aweme_list", [])
                typer.echo(f"   Total posts: {len(aweme_list)}")

                for idx, aweme in enumerate(aweme_list, 1):
                    desc = aweme.get("desc", "No description")
                    stats = aweme.get("statistics", {})
                    likes = stats.get("digg_count", 0)
                    typer.echo(f"   {idx}. {desc[:50]}... (❤️ {likes})")
            else:
                typer.echo(f"   Raw data: {posts}")

        except Exception as exc:
            typer.echo(f"❌ Error: {exc}", err=True)
            logger.exception("Posts fetch failed")
            raise typer.Exit(code=1)

    asyncio.run(fetch_posts())


@app.command()
def video(url: str, save_dir: Path = Path(".")) -> None:
    """Download video from Douyin URL.

    Args:
        url: Douyin video URL
        save_dir: Directory to save the video file

    Example:
        python -m patan video https://www.douyin.com/video/7300000000000000000
        python -m patan video https://www.douyin.com/video/7300000000000000000 --save-dir ./downloads
    """
    typer.echo("🎬 Fetching video details...")
    typer.echo(f"URL: {url}")
    typer.echo("=" * 50)

    async def fetch_video() -> None:
        try:
            client = DouyinClient()

            # Extract aweme_id from URL
            typer.echo("\n1️⃣  Extracting video ID...")
            aweme_id = await client.get_aweme_id(url)
            typer.echo(f"   ✅ aweme_id: {aweme_id}")

            # Fetch video details
            typer.echo("\n2️⃣  Fetching video details...")
            details: dict[str, Any] = await client.fetch_video_detail(aweme_id)

            # Display results
            typer.echo("\n📊 Video Details:")
            if "aweme_detail" not in details:
                typer.echo(f"   Raw data: {details}")
                return

            video_data = details.get("aweme_detail", {})
            desc = video_data.get("desc", "No description")
            stats = video_data.get("statistics", {})
            typer.echo(f"   Description: {desc}")
            typer.echo(f"   Likes: {stats.get('digg_count', 0)}")
            typer.echo(f"   Comments: {stats.get('comment_count', 0)}")
            typer.echo(f"   Shares: {stats.get('share_count', 0)}")
            typer.echo(f"   Plays: {stats.get('play_count', 0)}")

            # Download video
            video_url_list = video_data.get("video", {}).get("play_addr", {}).get("url_list", [])
            if not video_url_list:
                typer.echo("\n⚠️  No downloadable video URL found")
                return

            typer.echo("\n3️⃣  Downloading video...")
            cfg = DouyinConfig.load()
            async with VideoDownloader(proxy=cfg.proxies.get("https")) as downloader:
                filename = f"{aweme_id}.mp4"
                save_path = await downloader.download(video_url_list[0], save_dir, filename=filename)
                typer.echo(f"\n✅ Saved to: {save_path}")

        except Exception as exc:
            typer.echo(f"❌ Error: {exc}", err=True)
            logger.exception("Video download failed")
            raise typer.Exit(code=1)

    asyncio.run(fetch_video())


@app.command()
def comments(url: str) -> None:
    """Fetch comments from Douyin video URL.

    Args:
        url: Douyin video URL

    Example:
        python -m patan comments https://www.douyin.com/video/7300000000000000000
    """
    typer.echo("💬 Fetching video comments...")
    typer.echo(f"URL: {url}")
    typer.echo("=" * 50)

    async def fetch_comments() -> None:
        try:
            client = DouyinClient()

            # Extract aweme_id from URL
            typer.echo("\n1️⃣  Extracting video ID...")
            aweme_id = await client.get_aweme_id(url)
            typer.echo(f"   ✅ aweme_id: {aweme_id}")

            # Fetch comments
            typer.echo("\n2️⃣  Fetching comments...")
            comments_data: dict[str, Any] = await client.fetch_video_comments(aweme_id)

            # Display results
            typer.echo("\n📊 Comments:")
            if "comments" in comments_data:
                comments = comments_data.get("comments", [])
                typer.echo(f"   Total comments: {len(comments)}")

                for idx, comment in enumerate(comments[:10], 1):  # Show first 10
                    text = comment.get("text", "No text")
                    likes = comment.get("digg_count", 0)
                    reply_count = comment.get("reply_comment_total", 0)
                    typer.echo(f"   {idx}. {text[:60]}... (❤️ {likes}, 💬 {reply_count})")

                if len(comments) > 10:
                    typer.echo(f"   ... and {len(comments) - 10} more comments")
            else:
                typer.echo(f"   Raw data: {comments_data}")

        except Exception as exc:
            typer.echo(f"❌ Error: {exc}", err=True)
            logger.exception("Comments fetch failed")
            raise typer.Exit(code=1)

    asyncio.run(fetch_comments())


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
