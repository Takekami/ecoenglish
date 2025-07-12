import datetime
import os
import random
from pathlib import Path

import feedparser
import openai

from aws_utils import synthesize_speech, upload_to_s3
from blog_template import build_blog_post_html
from prompt_templates import get_prompt_for_level
from wp_poster import post_to_wordpress
from rss_generator import generate_rss, save_rss
from spreaker_uploader import upload_episode_to_spreaker

# ---------- 環境変数 ----------
OPENAI_API_KEY       = os.getenv("OPENAI_API_KEY")
S3_BUCKET            = os.getenv("S3_BUCKET_NAME")
WP_URL               = os.getenv("WP_URL")
WP_USER              = os.getenv("WP_USER")
WP_APP_PASS          = os.getenv("WP_APP_PASS")
SPREAKER_SHOW_ID     = os.getenv("SPREAKER_SHOW_ID")
SPREAKER_OAUTH_TOKEN = os.getenv("SPREAKER_OAUTH_TOKEN")
SPREAKER_REFRESH_TOKEN = os.getenv("SPREAKER_REFRESH_TOKEN")

REQ = [
    OPENAI_API_KEY, S3_BUCKET,
    WP_URL, WP_USER, WP_APP_PASS,
    SPREAKER_SHOW_ID, SPREAKER_OAUTH_TOKEN, SPREAKER_REFRESH_TOKEN
]
if not all(REQ):
    raise RuntimeError("Missing required env vars")

openai.api_key = OPENAI_API_KEY
client = openai.Client(api_key=OPENAI_API_KEY)

# ---------- 定数 ----------
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://feeds.npr.org/1006/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.abc.net.au/news/feed/51892/rss.xml",
]
MAX_TRIES = 5

# ---------- ヘルパ ----------

def select_feed() -> str:
    """Rotate feed daily so we don't always hit the same source."""
    return RSS_FEEDS[datetime.date.today().toordinal() % len(RSS_FEEDS)]

def fetch_article(url: str):
    feed = feedparser.parse(url)
    entries = [e for e in feed.entries if "summary" in e]
    return random.choice(entries) if entries else None

def is_significant(title: str, summary: str, link: str) -> bool:
    """記事が経済的／社会的に重要か yes/no で判定する"""
    prompt = f"""
### ROLE
You are a concise classifier.

### TASK
Read the following headline and summary, then decide if it is economically or socially significant.
Reply with **yes** or **no** only.

Title: {title}
Summary: {summary}
URL: {link}
"""
    # ここは小モデルにするとコスト削減になるので turbo を推奨
    r = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    ans = r.choices[0].message.content.strip().lower()
    return ans.startswith("yes")

def gpt(level: str, title: str, summary: str, link: str) -> str:
    prompt = get_prompt_for_level(level, title, summary, link)
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return r.choices[0].message.content.strip()

def extract(md: str, header: str) -> str:
    tag = f"### {header}"
    if tag not in md:
        return ""
    start = md.index(tag) + len(tag)
    nxt = md.find("###", start)
    return md[start:nxt if nxt > -1 else None].strip()

# ---------- Lambda ハンドラ ----------

def handler(event=None, context=None):
    # 1) 記事選定 ----------------------------------------------------------
    art = None
    for _ in range(MAX_TRIES):
        candidate = fetch_article(select_feed())
        if not candidate:
            continue
        if is_significant(candidate.title, candidate.summary, candidate.link):
            art = candidate
            break

    if not art:
        return {"statusCode": 500, "body": "No suitable article"}

    title, summary, link = art.title, art.summary, art.link

    # 2) GPT で教材コンテンツ生成 --------------------------------------------
    md = gpt("B1+", title, summary, link)
    if md.startswith("SKIP"):
        return {"statusCode": 204, "body": "Article skipped"}

    script = extract(md, "Script")
    vocab  = extract(md, "Vocabulary")
    lq     = extract(md, "Listening Questions")
    rq     = extract(md, "Reading Questions")
    ans    = extract(md, "Answers")
    gp     = extract(md, "Grammar Point")
    jp     = extract(md, "日本語での経済ニュース解説")
    usage  = extract(md, "使用場面")
    example_usage= extract(md, "使用例文")

    # 3) TTS → S3 アップロード
    mp3_path  = synthesize_speech(script, "news_episode.mp3")
    upload_to_s3(mp3_path, S3_BUCKET, "audio")

    # 4) Spreaker へエピソード登録 → ストリーム URL を取得
    episode = upload_episode_to_spreaker(
        local_audio_path=mp3_path,
        title=f"{title}（Intermediate レベル）",
        description="毎朝更新の英語リスニング教材です。",
        scheduled_at=None
    )
    # 永続的に使えるストリーム URL を audio_url にセット
    audio_url = episode.get("stream_url") or episode.get("download_url")
    print("🎧 audio_url:", audio_url)

    # 5) ブログ投稿（ここで audio_url が Spreaker URL になる）
    html = build_blog_post_html(
        "B1–B2",
        title,
        link,
        script,
        vocab,
        lq,
        rq,
        ans,
        gp,
        usage,
        example_usage,
        jp,
        audio_url,
    )
    post_to_wordpress(f"英語ニュース教材：{title}（Intermediate レベル）", html)

    # 6) RSS 生成 & S3 アップロード ----------------------------------------
    rss_xml = generate_rss(
        "英語で学ぶ経済ニュース",
        "https://econenglish.jp/",
        "Summary Samurai",
        "最新の経済ニュースを英語で学ぶ。",
        [{
        "title": f"{title}（Intermediate レベル）",
        "description": summary,
        "mp3_url": audio_url,
        "pub_date": datetime.datetime.utcnow(),
        }],
    )
    tmp = Path("/tmp/rss.xml")
    save_rss(rss_xml, tmp)
    upload_to_s3(tmp, S3_BUCKET, "rss")

    return {"statusCode": 200, "body": "Done"}
