# utils/wp_poster.py
import os, base64, requests

WP_URL  = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_APP_PASS = os.getenv("WP_APP_PASS")

token = base64.b64encode(f"{WP_USER}:{WP_APP_PASS}".encode()).decode()
HEADERS = {
    "Authorization": f"Basic {token}",
    "Content-Type": "application/json"
}

def post_to_wordpress(title, html, categories=None, tags=None):
    payload = {
        "title": title,
        "content": html,
        "status": "publish"
    }
    if categories:
        payload["categories"] = categories
    if tags:
        payload["tags"] = tags

    r = requests.post(WP_URL, headers=HEADERS, json=payload, timeout=20)

    if r.status_code == 201:
        link = r.json().get("link")
        print("✅ WordPress post OK:", link)
        return link
    else:
        print("❌ WordPress post failed:", r.status_code, r.text[:300])
        return None
