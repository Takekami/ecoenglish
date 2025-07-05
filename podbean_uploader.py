import os, requests

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

def upload_episode_to_podbean(title: str, media_url: str, description: str) -> str | None:
    token = _get_access_token()

    payload = {
        "title": title,
        "status": "publish",
        "type": "public",
        "format": "mp3",
        "source_url": media_url,
        "content": description,
    }
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.post(EPISODE_URL, data=payload, headers=headers, timeout=30)
    if r.ok:
        episode_link = r.json().get("link")
        print("✅ Podbean episode OK:", episode_link)
        return episode_link
    else:
        print("Podbean upload failed:", r.text)
        return None