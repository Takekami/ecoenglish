import os, requests
from typing import Optional

CLIENT_ID     = os.getenv("PODBEAN_CLIENT_ID")
CLIENT_SECRET = os.getenv("PODBEAN_CLIENT_SECRET")

TOKEN_URL   = "https://api.podbean.com/v1/oauth/token"
EPISODE_URL = "https://api.podbean.com/v1/episodes"
MAX_DESC    = 500      # free plan 上限

def _get_token() -> str:
    r = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": "episode_publish",
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["access_token"]

def _trim(txt: str, limit: int = MAX_DESC) -> str:
    flat = " ".join(txt.split())
    return (flat[: limit - 1] + "…") if len(flat) >= limit else flat

def upload_episode_to_podbean(title: str, media_url: str, description: str) -> Optional[str]:
    token = _get_token()
    payload = {
        "title": title,
        "media_url": media_url,   # presigned S3 URL
        "type": "public",
        "content": _trim(description),
    }
    r = requests.post(EPISODE_URL, headers={"Authorization": f"Bearer {token}"}, data=payload, timeout=30)
    if r.ok:
        link = r.json().get("link")
        print("✅ Podbean episode OK:", link)
        return link
    print("Podbean upload failed:", r.text)
    return None
