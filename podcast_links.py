"""Deterministic Japanese show notes; no extra model call."""
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


def tracked_lesson_url(url: str, episode_id, source: str = "spreaker") -> str:
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError("Lesson link must be a public HTTPS URL")
    query = [(key, value) for key, value in parse_qsl(parts.query) if not key.startswith("utm_")]
    query += [("utm_source", source), ("utm_medium", "podcast"),
              ("utm_campaign", "news_lessons"), ("utm_content", str(episode_id))]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), "eel-start"))


def episode_description(title: str, lesson_url: str, episode_id, source="spreaker") -> str:
    return (
        f"{title}\n\nこの回の英文・単語・理解度クイズはこちら：\n"
        f"{tracked_lesson_url(lesson_url, episode_id, source)}\n\n"
        "まず音声を聞き、クイズに答えてから英文を確認してみましょう。\n"
        "中級者向け（B1〜B2目安）。ニュースは教材公開時点の内容です。\n\n"
        "初めての方へ：\nhttps://econenglish.jp/howtousethisblogandpodcast/"
    )
