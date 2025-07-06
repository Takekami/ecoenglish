import os
import requests
from pathlib import Path
from requests.exceptions import HTTPError

# ── Configuration ───────────────────────────────────────────────────────────
TOKEN_URL           = "https://api.spreaker.com/oauth2/token"
API_BASE            = "https://api.spreaker.com/v2"
SPREAKER_SHOW_ID    = os.environ["SPREAKER_SHOW_ID"]
CLIENT_ID           = os.environ["SPREAKER_CLIENT_ID"]
CLIENT_SECRET       = os.environ["SPREAKER_CLIENT_SECRET"]
REFRESH_TOKEN       = os.environ["SPREAKER_REFRESH_TOKEN"]  # 初回取得のリフレッシュトークン

# ── OAuth2 Helper ───────────────────────────────────────────────────────────
def _refresh_access_token() -> str:
    """
    リフレッシュトークンを使って新しい access_token を取得し、
    環境変数も更新して返します。
    """
    data = {
        "grant_type":    "refresh_token",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
    }
    r = requests.post(TOKEN_URL, data=data, timeout=15)
    r.raise_for_status()
    j = r.json()
    # 環境変数を上書きして次回以降も使えるように
    os.environ["SPREAKER_OAUTH_TOKEN"]  = j["access_token"]
    os.environ["SPREAKER_REFRESH_TOKEN"] = j["refresh_token"]
    return j["access_token"]

def _get_auth_header() -> dict:
    """
    有効な access_token を返すヘッダーを作成。
    トークンが未設定 or 期限切れのときは自動でリフレッシュを試みます。
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
    scheduled_at: str | None = None  # "2025-07-07T08:00:00+09:00" のような ISO8601
) -> dict:
    """
    ローカル MP3 を Spreaker にアップロードし、エピソードを公開します。
    成功時は Spreaker API のレスポンス 'response' 部分を dict で返します。
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

    # 1) access_token で試しにアップロード
    headers = _get_auth_header()
    resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)

    try:
        resp.raise_for_status()
    except HTTPError:
        # 401 Unauthorized の場合はリフレッシュ→再試行
        if resp.status_code == 401:
            headers = {"Authorization": f"Bearer {_refresh_access_token()}"}
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)
            resp.raise_for_status()
        else:
            raise

    return resp.json()["response"]
