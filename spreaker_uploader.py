import os
import time
import requests
from pathlib import Path
from requests.exceptions import HTTPError

# ── Configuration ───────────────────────────────────────────────────────────
TOKEN_URL           = "https://api.spreaker.com/oauth2/token"
API_BASE            = "https://api.spreaker.com/v2"
SPREAKER_SHOW_ID    = os.environ["SPREAKER_SHOW_ID"]
CLIENT_ID           = os.environ["SPREAKER_CLIENT_ID"]
CLIENT_SECRET       = os.environ["SPREAKER_CLIENT_SECRET"]
REFRESH_TOKEN       = os.environ["SPREAKER_REFRESH_TOKEN"]

# ── OAuth2 Helper ───────────────────────────────────────────────────────────
def _refresh_access_token() -> str:
    data = {
        "grant_type":    "refresh_token",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
    }
    r = requests.post(TOKEN_URL, data=data, timeout=15)
    r.raise_for_status()
    j = r.json()
    # Overwrite environment variables for next time
    os.environ["SPREAKER_OAUTH_TOKEN"]  = j["access_token"]
    os.environ["SPREAKER_REFRESH_TOKEN"] = j["refresh_token"]
    return j["access_token"]

def _get_auth_header() -> dict:
    """
    Create a valid access token header.
    If the token is not set or expired, automatically refresh it.
    """
    token = os.environ.get("SPREAKER_OAUTH_TOKEN")
    if not token:
        token = _refresh_access_token()
    return {"Authorization": f"Bearer {token}"}

# ── Episode Upload ───────────────────────────────────────────────────────────
def upload_episode_to_spreaker(
    local_audio_path: str,
    title: str,
    description: str,
    scheduled_at: str | None = None
) -> dict:
    """
    Upload local MP3 to Spreaker and publish the episode.
    Return the response from Spreaker API 'response' part as a dict.
    """
    url = f"{API_BASE}/shows/{SPREAKER_SHOW_ID}/episodes"
    files = {
        "media_file": (
            Path(local_audio_path).name,
            open(local_audio_path, "rb"),
            "audio/mpeg"
        )
    }
    data = {
        "title":       title,
        "description": description,
    }
    if scheduled_at:
        data["scheduled_at"] = scheduled_at

    # 1) Try to upload with access_token
    headers = _get_auth_header()
    resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)

    try:
        resp.raise_for_status()
    except HTTPError:
        # If 401 Unauthorized, refresh and try again
        if resp.status_code == 401:
            headers = {"Authorization": f"Bearer {_refresh_access_token()}"}
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)
            resp.raise_for_status()
        else:
            raise

    # Get episode information from the first response
    response = resp.json().get("response", {})
    # If "episode" is nested, expand it
    resp_data = response.get("episode", response)
    # Get episode_id or id
    episode_id = resp_data.get("episode_id") or resp_data.get("id")
    if not episode_id:
        # If failed to get episode_id, raise an error
        raise RuntimeError(f"Failed to get episode_id from Spreaker response: {resp_data!r}")

    # Poll until encoding is complete
    for _ in range(20):  # Wait for up to 20 times (about 100 seconds)
        try:
            info = requests.get(
                f"{API_BASE}/episodes/{episode_id}",
                headers=headers,
                timeout=30
            )
            info.raise_for_status()
        except HTTPError as e:
            # Once log and retry, finally timeout
            print(f"⚠️ Polling episode status failed (attempt {_+1}):", e)
            time.sleep(5)
            continue
        raw = info.json().get("response", {})
        info_data = raw.get("episode", raw)
        status = info_data.get("encoding_status")
        if status == "READY":
             # stream_url and download_url should be ready
             return {
                 "stream_url": info_data.get("stream_url"),
                 "download_url": info_data.get("download_url"),
                 **info_data
             }
        # If still PENDING, wait and retry
        time.sleep(5)

    # If timeout, return the first data
    return resp_data
