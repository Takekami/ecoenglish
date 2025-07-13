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
    scheduled_at: str | None = None
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

    # 最初のレスポンスから episode 情報を取り出し
    response = resp.json().get("response", {})
    # "episode" ネストがあれば展開
    resp_data = response.get("episode", response)
    # episode_id または id を取得
    episode_id = resp_data.get("episode_id") or resp_data.get("id")
    if not episode_id:
        # 取得失敗なら明示的にエラーにして続きを止める
        raise RuntimeError(f"Failed to get episode_id from Spreaker response: {resp_data!r}")

    # エンコード完了までポーリング
    for _ in range(20):  # 最大20回（約100秒）待つ
        try:
            info = requests.get(
                f"{API_BASE}/episodes/{episode_id}",
                headers=headers,
                timeout=30
            )
            info.raise_for_status()
        except HTTPError as e:
            # 一度だけログを出してからリトライ、最終的にタイムアウト判定に移行
            print(f"⚠️ Polling episode status failed (attempt {_+1}):", e)
            time.sleep(5)
            continue
        raw = info.json().get("response", {})
        info_data = raw.get("episode", raw)
        status = info_data.get("encoding_status")
        if status == "READY":
             # stream_url や download_url が揃っているはず
             return {
                 "stream_url": info_data.get("stream_url"),
                 "download_url": info_data.get("download_url"),
                 **info_data
             }
        # まだ PENDING なら少し待って再試行
        time.sleep(5)

    # タイムアウトしたら、とりあえず最初のデータを返す
    return resp_data
