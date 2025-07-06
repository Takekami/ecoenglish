import os
import requests
from pathlib import Path

# Configuration via environment variables
# Obtain an OAuth2 token for your Spreaker account via the Developer Dashboard (Authentication guide)
SPREAKER_SHOW_ID = os.environ["SPEAKER_CLIENT_ID"]
SPREAKER_OAUTH_TOKEN = os.environ["SPEAKER_CLIENT_SECRET"]

API_BASE = "https://api.spreaker.com/v2"


def upload_episode_to_spreaker(
    local_audio_path: str,
    title: str,
    description: str,
    scheduled_at: str | None = None  # ISO8601 datetime if you want to schedule
) -> dict:
    """
    Uploads a local MP3 to Spreaker and publishes it as a new episode.
    Returns the JSON response with episode metadata.

    - local_audio_path: Path to your generated .mp3
    - title: Episode title
    - description: Episode description
    - scheduled_at: Optional ISO8601 string to schedule publication
    """
    url = f"{API_BASE}/shows/{SPREAKER_SHOW_ID}/episodes"
    headers = {"Authorization": f"Bearer {SPREAKER_OAUTH_TOKEN}"}

    # Prepare multipart form-data
    files = {
        "media_file": (
            Path(local_audio_path).name,
            open(local_audio_path, "rb"),
            "audio/mpeg"
        )
    }
    data = {
        "title": title,
        "description": description,
    }
    if scheduled_at:
        data["scheduled_at"] = scheduled_at

    resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["response"]