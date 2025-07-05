# podbean_uploader.py
import os, requests, tempfile, boto3
from pathlib import Path
from urllib.parse import urlparse

ID     = os.getenv("PODBEAN_CLIENT_ID")
SECRET = os.getenv("PODBEAN_CLIENT_SECRET")
TOKEN_ENDPOINT   = "https://api.podbean.com/v1/oauth/token"
UPLOAD_ENDPOINT  = "https://api.podbean.com/v1/episodes/upload"
EPISODE_ENDPOINT = "https://api.podbean.com/v1/episodes"

def _get_access_token():
    url = "https://api.podbean.com/v1/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id":     os.getenv("PODBEAN_CLIENT_ID"),
        "client_secret": os.getenv("PODBEAN_CLIENT_SECRET"),
        "scope": "episode_publish"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(url, data=payload, headers=headers, timeout=10)
    r.raise_for_status()           # ここで 400 が出る場合は上の5項目を再点検
    return r.json()["access_token"]

def _download(url: str) -> str:
    """署名付き S3 URL → /tmp/xxxx.mp3 に保存してローカルパスを返す"""
    fn = Path(urlparse(url).path).name
    tmp = Path(tempfile.gettempdir()) / fn
    with requests.get(url, stream=True) as res:
        res.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in res.iter_content(1024 * 1024):
                f.write(chunk)
    return str(tmp)

def upload_episode_to_podbean(title: str, s3_signed_url: str, description: str) -> str | None:
    token = _get_access_token()

    # --- ① S3 から一時ダウンロード（Podbean API は外部 URL 受付不可） ---
    local_mp3 = _download(s3_signed_url)

    # --- ② /episodes/upload ---
    with open(local_mp3, "rb") as f:
        up = requests.post(
            UPLOAD_ENDPOINT,
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (Path(local_mp3).name, f, "audio/mpeg")}
        )
    if up.status_code != 200:
        print("Podbean upload failed:", up.text);  return None

    upload_key = up.json()["upload_key"]

    # --- ③ /episodes  ---
    ep = requests.post(
        EPISODE_ENDPOINT,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json"},
        json={
            "title":       title,
            "upload_key":  upload_key,
            "status":      "published",
            "description": description
        })
    if ep.status_code != 200:
        print("Episode create failed:", ep.text);  return None

    link = ep.json().get("link")
    print("✅ Podbean OK:", link)
    return link
