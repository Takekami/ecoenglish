import requests
from pathlib import Path
from typing import Optional

# Podbean API endpoints
token_url = "https://api.podbean.com/v1/oauth/token"
media_upload_url = "https://api.podbean.com/v1/media"
episode_publish_url = "https://api.podbean.com/v1/episodes"

# Client credentials (assumed to be set elsewhere securely)
CLIENT_ID = "PODBEAN_CLIENT_ID"
CLIENT_SECRET = "PODBEAN_CLIENT_SECRET"


def _get_token(scope: str) -> str:
    """
    Obtain an OAuth2 access token for the given scope.
    """
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": scope,
    }
    resp = requests.post(token_url, data=data, timeout=15)
    resp.raise_for_status()
    return resp.json()["access_token"]


def upload_media_file(local_path: str) -> str:
    """
    Upload the local audio file to Podbean storage and return media_id.
    """
    token = _get_token(scope="media_upload")
    headers = {"Authorization": f"Bearer {token}"}
    with open(local_path, "rb") as f:
        files = {"media": (Path(local_path).name, f, "audio/mpeg")}
        resp = requests.post(media_upload_url, headers=headers, files=files, timeout=60)
    resp.raise_for_status()
    media_id = resp.json().get("media_id")
    if not media_id:
        raise RuntimeError(f"Podbean media upload failed: {resp.text}")
    return media_id


def upload_episode_to_podbean(
    title: str,
    local_audio_path: str,
    description: str
) -> Optional[str]:
    """
    Uploads audio to Podbean and publishes an episode using the returned media_id.
    Returns the episode link on success, or None on failure.
    """
    # 1) Upload media file
    media_id = upload_media_file(local_audio_path)

    # 2) Publish episode
    token = _get_token(scope="episode_publish")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title": title,
        "media_id": media_id,
        "type": "public",
        "content": description[:10000],  # trim if needed
    }
    resp = requests.post(episode_publish_url, headers=headers, data=payload, timeout=30)
    resp.raise_for_status()

    return resp.json().get("link")
