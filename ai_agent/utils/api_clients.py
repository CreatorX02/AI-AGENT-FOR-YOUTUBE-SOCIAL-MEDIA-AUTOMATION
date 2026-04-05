"""API client helpers for YouTube, TikTok, Instagram, Facebook, and Twitter."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ai_agent.config import Config

logger = logging.getLogger(__name__)


class YouTubeClient:
    """Wrapper around the YouTube Data API v3."""

    def __init__(self, config: Optional[Config] = None) -> None:
        self._config = config or Config()
        self._service: Any = None

    def _get_service(self) -> Any:
        if self._service is None:
            try:
                from googleapiclient.discovery import build  # type: ignore

                self._service = build(
                    "youtube", "v3", developerKey=self._config.YOUTUBE_API_KEY
                )
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError(
                    "google-api-python-client is required."
                ) from exc
        return self._service

    def search_trending(
        self, query: str, max_results: int = 10, region_code: str = "US"
    ) -> List[Dict[str, Any]]:
        """Search YouTube for trending videos matching *query*."""
        service = self._get_service()
        response = (
            service.search()
            .list(
                part="snippet",
                q=query,
                type="video",
                order="viewCount",
                regionCode=region_code,
                maxResults=max_results,
            )
            .execute()
        )
        return response.get("items", [])

    def get_video_stats(self, video_id: str) -> Dict[str, Any]:
        """Fetch statistics for a single video."""
        service = self._get_service()
        response = (
            service.videos()
            .list(part="snippet,statistics,contentDetails", id=video_id)
            .execute()
        )
        items = response.get("items", [])
        return items[0] if items else {}

    def upload_video(
        self,
        file_path: str,
        title: str,
        description: str,
        tags: List[str],
        category_id: str = "22",
        privacy_status: str = "public",
    ) -> str:
        """Upload a video file and return the new video ID."""
        try:
            from googleapiclient.http import MediaFileUpload  # type: ignore
            from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
            from googleapiclient.discovery import build  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "google-api-python-client and google-auth-oauthlib are required."
            ) from exc

        scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": self._config.YOUTUBE_CLIENT_ID,
                    "client_secret": self._config.YOUTUBE_CLIENT_SECRET,
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes,
        )
        credentials = flow.run_local_server(port=0)
        service = build("youtube", "v3", credentials=credentials)

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id,
            },
            "status": {"privacyStatus": privacy_status},
        }
        media = MediaFileUpload(file_path, resumable=True)
        request = service.videos().insert(
            part="snippet,status", body=body, media_body=media
        )
        response = request.execute()
        video_id: str = response.get("id", "")
        logger.info("Uploaded YouTube video: %s", video_id)
        return video_id

    def get_channel_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Return basic channel statistics (requires an authenticated service)."""
        service = self._get_service()
        response = (
            service.channels()
            .list(
                part="statistics",
                id=self._config.YOUTUBE_CHANNEL_ID,
            )
            .execute()
        )
        items = response.get("items", [])
        return items[0].get("statistics", {}) if items else {}


class TikTokClient:
    """Minimal TikTok API client (Content Posting API)."""

    _BASE_URL = "https://open.tiktokapis.com/v2"

    def __init__(self, config: Optional[Config] = None) -> None:
        self._config = config or Config()

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._config.TIKTOK_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

    def upload_video(
        self, video_url: str, caption: str, hashtags: List[str]
    ) -> Dict[str, Any]:
        """Initiate a TikTok video upload and return the API response."""
        import requests  # type: ignore

        full_caption = caption + " " + " ".join(f"#{t}" for t in hashtags)
        payload = {
            "post_info": {
                "title": full_caption[:150],
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "video_url": video_url,
            },
        }
        response = requests.post(
            f"{self._BASE_URL}/post/publish/video/init/",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        data: Dict[str, Any] = response.json()
        logger.info("TikTok upload initiated: %s", data)
        return data


class InstagramClient:
    """Meta Graph API client for Instagram Reels publishing."""

    _BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, config: Optional[Config] = None) -> None:
        self._config = config or Config()

    def upload_reel(
        self, video_url: str, caption: str
    ) -> Dict[str, Any]:
        """Create a Reels container and publish it; return the media ID."""
        import requests  # type: ignore

        # Step 1: Create container
        container_response = requests.post(
            f"{self._BASE_URL}/{self._config.INSTAGRAM_ACCOUNT_ID}/media",
            params={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "access_token": self._config.INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=30,
        )
        container_response.raise_for_status()
        container_id: str = container_response.json().get("id", "")

        # Step 2: Publish
        publish_response = requests.post(
            f"{self._BASE_URL}/{self._config.INSTAGRAM_ACCOUNT_ID}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": self._config.INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=30,
        )
        publish_response.raise_for_status()
        data: Dict[str, Any] = publish_response.json()
        logger.info("Instagram Reel published: %s", data)
        return data


class FacebookClient:
    """Meta Graph API client for Facebook video publishing."""

    _BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, config: Optional[Config] = None) -> None:
        self._config = config or Config()

    def upload_video(
        self, video_url: str, description: str, title: str
    ) -> Dict[str, Any]:
        """Upload a video to a Facebook Page and return the API response."""
        import requests  # type: ignore

        response = requests.post(
            f"{self._BASE_URL}/{self._config.FACEBOOK_PAGE_ID}/videos",
            params={
                "file_url": video_url,
                "description": description,
                "title": title,
                "access_token": self._config.FACEBOOK_ACCESS_TOKEN,
            },
            timeout=30,
        )
        response.raise_for_status()
        data: Dict[str, Any] = response.json()
        logger.info("Facebook video uploaded: %s", data)
        return data


class TwitterClient:
    """Twitter v2 API client for posting video tweets."""

    _BASE_URL = "https://api.twitter.com/2"

    def __init__(self, config: Optional[Config] = None) -> None:
        self._config = config or Config()

    def _auth(self) -> Any:
        try:
            from requests_oauthlib import OAuth1  # type: ignore

            return OAuth1(
                self._config.TWITTER_API_KEY,
                self._config.TWITTER_API_SECRET,
                self._config.TWITTER_ACCESS_TOKEN,
                self._config.TWITTER_ACCESS_SECRET,
            )
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("requests-oauthlib is required for Twitter.") from exc

    def post_tweet(self, text: str) -> Dict[str, Any]:
        """Post a text tweet and return the API response."""
        import requests  # type: ignore

        response = requests.post(
            f"{self._BASE_URL}/tweets",
            json={"text": text[:280]},
            auth=self._auth(),
            timeout=15,
        )
        response.raise_for_status()
        data: Dict[str, Any] = response.json()
        logger.info("Tweet posted: %s", data)
        return data
