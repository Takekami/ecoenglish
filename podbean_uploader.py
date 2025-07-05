import os
import requests
from pathlib import Path
from typing import Optional

"""podbean_uploader.py – *direct upload* version
------------------------------------------------
1. 取得した MP3 ファイルを Podbean の一時ストレージに **multipart/form‑data** でアップロード
2. 戻り値 `location` を `media_key` として `POST /v1/episodes`

Free プランでも利用可 / ファイルサイズ上限 100 MB。
"""

CLIENT_ID: str  = os.getenv("PODBEAN_CLIENT_ID", "")
CLIENT_SECRET: str = os.getenv("PODBEAN_CLIENT_SECRET", "")

TOKEN_URL   = "https://api.podbean.com/v1/oauth/token"
UPLOAD_URL  = "https://api.podbean.com/v1/files/upload"
EPISODE_URL = "https://api.podbean.com/v1/episodes"

TIMEOUT = 60  # seconds
MAX_DESC = 500  # free plan description limit

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _truncate(txt: str, limit: int = MAX_DESC) -> str:
    """Trim description to Podbean free‑plan limit (500 chars)."""
    txt = (txt or "").replace("\n", " ").strip()
    return txt[: limit - 1] + "…" if len(txt) >= limit else txt


def _get_access_token() -> str:
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "episode_publish",  # ← ファイルアップロード + 公開
    }
    r = requests.post(TOKEN_URL, data=data, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["access_token"]


def _upload_media(token: str, mp3_path: str) -> str:
    """Upload the local mp3 to Podbean and return the media *location* string."""
    headers = {"Authorization": f"Bearer {token}"}
    with open(mp3_path, "rb") as f:
        files = {"file": (Path(mp3_path).name, f, "audio/mpeg")}
        r = requests.post(UPLOAD_URL, headers=headers, files=files, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["location"]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def upload_episode_to_podbean(title: str, mp3_path: str, description: str) -> Optional[str]:
    """Upload *mp3_path* as a public episode and return the episode link (or None)."""
    try:
        token = _get_access_token()
        media_key = _upload_media(token, mp3_path)

        payload = {
            "title": title,
            "type": "public",
            "media_key": media_key,
            "content": _truncate(description),
        }
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.post(EPISODE_URL, data=payload, headers=headers, timeout=TIMEOUT)
        if r.ok:
            link = r.json().get("link")
            print("✅ Podbean episode OK:", link)
            return link
        else:
            print("Podbean upload failed:", r.text)
            return None

    except Exception as e:
        print("Podbean upload failed:", e)
        return None
