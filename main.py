# main.py
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
from podbean_uploader import upload_episode_to_podbean

# ---------- 環境変数 ----------
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")
S3_BUCKET       = os.getenv("S3_BUCKET_NAME")
WP_URL          = os.getenv("WP_URL")
WP_USER         = os.getenv("WP_USER")
WP_APP_PASS     = os.getenv("WP_APP_PASS")
PODBEAN_ID      = os.getenv("PODBEAN_CLIENT_ID")
PODBEAN_SECRET  = os.getenv("PODBEAN_CLIENT_SECRET")

REQUIRED_VARS = [
    OPENAI_API_KEY, S3_BUCKET,
    WP_URL, WP_USER, WP_APP_PASS,
    PODBEAN_ID, PODBEAN_SECRET
]
if not all(REQUIRED_VARS):
    raise RuntimeError("One or more required environment variables are missing")

# ---------- OpenAI ----------
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
LEVELS = ["B1+", "B2"]

# ---------- ヘルパ ----------
def select_feed():
    return RSS_FEEDS[datetime.date.today().toordinal() % len(RSS_FEEDS)]

def fetch_article(feed_url):
    feed = feedparser.parse(feed_url)
    entries = [e for e in feed.entries if "summary" in e]
    return random.choice(entries) if entries else None

def generate_content(level, title, summary, url):
    prompt = get_prompt_for_level(level, title, summary, url)
    res = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a skilled English learning content creator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    return res.choices[0].message.content

def get_candidate_entry():
    """重要度 yes の記事が出るまで最大 MAX_TRIES 試行"""
    for _ in range(MAX_TRIES):
        entry = fetch_article(select_feed())
        if not entry:
            continue
        judge = generate_content("B1+", entry.title, entry.summary, entry.link)
        if not judge.startswith("SKIP"):
            return entry
    return None

def _extract_section(md: str, header: str) -> str:
    try:
        start = md.index(f"### {header}") + len(f"### {header}")
        end = md.index("###", start)
    except ValueError:
        end = len(md)
    return md[start:].strip() if start < end else md[start:end].strip()

# ---------- Lambda ハンドラ ----------
def handler(event=None, context=None):
    try:
        entry = get_candidate_entry()
        if not entry:
            return {"statusCode": 500, "body": "No suitable article found"}

        title, summary, url = entry.title, entry.summary, entry.link
        today = datetime.date.today()
        episode_list = []

        # ---- B1+ / B2 を両方処理 ----
        for level in LEVELS:
            gpt_md = generate_content(level, title, summary, url)

            script = _extract_section(gpt_md, "Script")
            lq     = _extract_section(gpt_md, "Listening Questions")
            rq     = _extract_section(gpt_md, "Reading Questions")
            gp     = _extract_section(gpt_md, "Grammar Point")

            mp3_path  = synthesize_speech(script, f"{level}_{today}.mp3")
            audio_url = upload_to_s3(mp3_path, S3_BUCKET)

            html = build_blog_post_html(level, title, url, script, lq, rq, gp, audio_url)
            if not post_to_wordpress(f"{level} 英語ニュース教材：{title}", html):
                raise RuntimeError("WordPress post failed")

            if not upload_episode_to_podbean(f"{level}: {title}", audio_url, summary):
                raise RuntimeError("Podbean upload failed")

            episode_list.append({
                "title": f"{level}: {title}",
                "description": summary,
                "mp3_url": audio_url,
                "pub_date": datetime.datetime.utcnow(),
            })

        # ---- RSS を 1 度だけ生成して S3 へ ----
        rss_xml = generate_rss(
            feed_title   = "英語で学ぶ経済ニュース",
            site_url     = "https://yourdomain.com",
            author       = "Takeyuki Murakami",
            description  = "毎朝届く、英語で学ぶ最新の経済ニュース。CEFR B1+ / B2対応。",
            episode_list = episode_list,
        )
        tmp = Path("/tmp/rss.xml")
        save_rss(rss_xml, path=tmp)
        upload_to_s3(tmp, S3_BUCKET, folder="rss")

        return {"statusCode": 200, "body": "Podcast & blog posted successfully."}

    except Exception as e:
        print("Error occurred:", e)
        return {"statusCode": 500, "body": f"Error: {e}"}
