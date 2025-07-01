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
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
S3_BUCKET        = os.getenv("S3_BUCKET_NAME")
WP_URL           = os.getenv("WP_URL")
WP_USER          = os.getenv("WP_USER")
WP_PASSWORD      = os.getenv("WP_PASSWORD")
PODBEAN_ID       = os.getenv("PODBEAN_CLIENT_ID")
PODBEAN_SECRET   = os.getenv("PODBEAN_CLIENT_SECRET")

# 必須変数が欠けていれば Lambda を起動しない
REQUIRED_VARS = [OPENAI_API_KEY, S3_BUCKET, WP_URL, WP_USER, WP_PASSWORD, PODBEAN_ID, PODBEAN_SECRET]
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
LEVELS = ["B1+", "B2"]


# ---------- ヘルパ ----------
def select_feed():
    return RSS_FEEDS[datetime.date.today().toordinal() % len(RSS_FEEDS)]


def fetch_article(feed_url):
    feed = feedparser.parse(feed_url)
    with_summary = [e for e in feed.entries if "summary" in e]
    return random.choice(with_summary) if with_summary else None


def generate_content(level, title, summary, url):
    prompt = get_prompt_for_level(level, title, summary, url)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a skilled English learning content creator."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content


# ---------- Lambda ハンドラ ----------
def handler(event=None, context=None):
    try:
        feed_url = select_feed()
        entry = fetch_article(feed_url)
        if not entry:
            raise RuntimeError("No article found in RSS")

        title, summary, url = entry.title, entry.summary, entry.link
        today = datetime.date.today()
        episode_list = []

        for level in LEVELS:
            # --- AI 生成 ---
            content = generate_content(level, title, summary, url)

            # --- スクリプト抽出 ---
            script_start = content.find("### Script\n")
            script_end = content.find("### Listening Questions")
            script = content[script_start + 11 : script_end].strip()

            # --- 音声合成 & S3 アップロード ---
            local_mp3 = synthesize_speech(script, f"{level}_{today}.mp3")
            audio_url = upload_to_s3(local_mp3, S3_BUCKET)

            # --- WordPress 投稿 ---
            blog_html = build_blog_post_html(content, audio_url, level)
            post_title = f"{level} 英語ニュース教材：{title}"
            wp_link = post_to_wordpress(post_title, blog_html)
            if not wp_link:
                raise RuntimeError("WordPress post failed")

            # --- Podbean アップロード ---
            episode_link = upload_episode_to_podbean(
                title=post_title,
                mp3_url=audio_url,
                description=f"今日のニュース：{title}",
                client_id=PODBEAN_ID,
                client_secret=PODBEAN_SECRET,
            )
            if not episode_link:
                raise RuntimeError("Podbean upload failed")

            episode_list.append(
                {
                    "title": post_title,
                    "description": f"今日のニュース：{title}",
                    "mp3_url": audio_url,
                    "pub_date": datetime.datetime.utcnow(),
                }
            )

        # --- RSS フィード生成 & S3 へ ---
        rss_xml = generate_rss(
            feed_title="英語で学ぶ経済ニュース",
            site_url="https://yourdomain.com",
            author="Takeyuki Murakami",
            description="毎朝届く、英語で学ぶ最新の経済ニュース。CEFR B1+ / B2対応。",
            episode_list=episode_list,
        )
        save_path = "/tmp/rss.xml"
        save_rss(rss_xml, path=save_path)
        upload_to_s3(save_path, S3_BUCKET, folder="rss")

        return {"statusCode": 200, "body": "Podcast & blog posted successfully."}

    except Exception as e:
        # CloudWatch に詳細を出しておく
        print("Error occurred:", e)
        return {"statusCode": 500, "body": f"Error: {e}"}
