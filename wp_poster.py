# utils/wp_poster.py
import requests
import os
import base64

def post_to_wordpress(title, content_html, categories=None, tags=None):
    WP_URL = os.getenv("WP_URL")
    WP_USER = os.getenv("WP_USER")
    WP_APP_PASS = os.getenv("WP_APP_PASS")

    auth_str = f"{WP_USER}:{WP_APP_PASS}"
    auth_header = base64.b64encode(auth_str.encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json"
    }

    payload = {
        "title": title,
        "content": content_html,
        "status": "publish"
    }
    if categories:
        payload["categories"] = categories  # ID list
    if tags:
        payload["tags"] = tags  # ID list

    response = requests.post(WP_URL, headers=headers, json=payload)

    if response.status_code == 201:
        print("✅ WordPress post successful:", response.json().get("link"))
        return response.json().get("link")
    else:
        print("❌ WordPress post failed:", response.status_code, response.text)
        return None
