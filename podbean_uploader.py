# podbean_uploader.py  ── 置き換え
import os, requests, time
from pathlib import Path
from typing import Optional

CID     = os.getenv("PODBEAN_CLIENT_ID")
CSECRET = os.getenv("PODBEAN_CLIENT_SECRET")

TOKEN_URL       = "https://api.podbean.com/v1/oauth/token"
UPLOADLINK_URL  = "https://api.podbean.com/v1/files/uploadLink"
EPISODE_URL     = "https://api.podbean.com/v1/episodes"

def _token() -> str:
    r = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": CID,
            "client_secret": CSECRET,
            "scope": "episode_publish",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]

def _put_file(presigned_url: str, mp3_path: str) -> None:
    with open(mp3_path, "rb") as f:
        r = requests.put(presigned_url, data=f, headers={"Content-Type": "audio/mpeg"}, timeout=120)
        r.raise_for_status()

def upload_episode_to_podbean(title: str, mp3_path: str, description: str) -> Optional[str]:
    token = _token()

    # 1. presigned URL を取得
    file_size = Path(mp3_path).stat().st_size
    r = requests.post(
        UPLOADLINK_URL,
        headers={"Authorization": f"Bearer {token}"},
        json={"filename": Path(mp3_path).name, "filesize": file_size},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    presigned_url = data["presigned_url"]
    file_key      = data["file_key"]          # episode 登録時に渡す id

    # 2. PUT でアップロード
    _put_file(presigned_url, mp3_path)

    # 3. エピソードとして公開
    payload = {
        "title"      : title,
        "type"       : "public",
        "content"    : (description[:499] + "…") if len(description) > 500 else description,
        "file_key"   : file_key,
        "status"     : "publish",
    }
    r = requests.post(EPISODE_URL, headers={"Authorization": f"Bearer {token}"}, data=payload, timeout=30)
    if r.ok:
        link = r.json().get("link", "")
        print("✅ Podbean OK:", link)
        return link
    else:
        print("Podbean upload failed:", r.text)
        return None
