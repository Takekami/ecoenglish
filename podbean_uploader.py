# utils/podbean_uploader.py
import os
import requests

def get_podbean_access_token():
    client_id = os.getenv("PODBEAN_CLIENT_ID")
    client_secret = os.getenv("PODBEAN_CLIENT_SECRET")

    response = requests.post(
        "https://api.podbean.com/v1/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print("❌ Failed to get access token:", response.status_code, response.text)
        return None

def upload_episode_to_podbean(title, mp3_url, description):
    access_token = get_podbean_access_token()
    if not access_token:
        return None

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
        "title": title,
        "media_url": mp3_url,
        "type": "public",
        "content": description
    }

    response = requests.post(
        "https://api.podbean.com/v1/episodes",
        headers=headers,
        data=payload
    )

    if response.status_code == 200:
        print("✅ Podbean episode uploaded successfully:", response.json().get("link"))
        return response.json().get("link")
    else:
        print("❌ Podbean upload failed:", response.status_code, response.text)
        return None