# podbean_uploader.py
import os, requests
from typing import Optional

CLIENT_ID     = os.getenv("PODBEAN_CLIENT_ID")
CLIENT_SECRET = os.getenv("PODBEAN_CLIENT_SECRET")

TOKEN_URL   = "https://api.podbean.com/v1/oauth/token"
EPISODE_URL = "https://api.podbean.com/v1/episodes"

def _get_access_token() -> str:
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "episode_publish",
    }
    r = requests.post(TOKEN_URL, data=data, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

MAX_LEN = 500  # Podbean free-plan limit (characters)

def _truncate(text: str, limit: int = MAX_LEN) -> str:
    txt = text.strip().replace("\n", " ")
    return txt[: limit - 1] + "…" if len(txt) >= limit else txt

def upload_episode_to_podbean(title: str,
                              media_url: str,
                              description: str) -> Optional[str]:

    token = _get_access_token()      # ← ここを追加

    payload = {
        "title": title,
        "media_url": media_url,
        "type": "public",
        "content": _truncate(description),
    }
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.post(EPISODE_URL, data=payload, headers=headers, timeout=30)
    if r.ok:
        link = r.json().get("link")
        print("✅ Podbean episode OK:", link)
        return link
    else:
        print("Podbean upload failed:", r.text)
        return None