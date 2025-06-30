# main.py
import feedparser
import random
import datetime
import os
import openai
from aws_utils import synthesize_speech, upload_to_s3
from blog_template import build_blog_post_html
from prompt_templates import get_prompt_for_level
from wp_poster import post_to_wordpress
from rss_generator import generate_rss, save_rss

client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
openai.api_key = os.getenv("OPENAI_API_KEY")

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://feeds.npr.org/1006/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.abc.net.au/news/feed/51892/rss.xml",
]

LEVELS = ["B1+", "B2"]
S3_BUCKET = os.getenv("S3_BUCKET_NAME")


def select_feed():
    today_index = datetime.date.today().toordinal() % len(RSS_FEEDS)
    return RSS_FEEDS[today_index]

def fetch_article(feed_url):
    feed = feedparser.parse(feed_url)
    entries = [e for e in feed.entries if 'summary' in e]
    return random.choice(entries) if entries else None

def generate_content(level, title, summary, url):
    prompt = get_prompt_for_level(level, title, summary, url)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a skilled English learning content creator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

def handler(event=None, context=None):
    feed_url = select_feed()
    entry = fetch_article(feed_url)
    if not entry:
        print("No article found.")
        return {"statusCode": 500, "body": "No article found"}

    title, summary, url = entry.title, entry.summary, entry.link
    today = datetime.date.today()
    episode_list = []

    for level in LEVELS:
        content = generate_content(level, title, summary, url)

        script_start = content.find("### Script\n")
        script_end = content.find("### Listening Questions")
        script = content[script_start + 11:script_end].strip()

        audio_file = synthesize_speech(script, f"{level}_{today}.mp3")
        audio_url = upload_to_s3(audio_file, S3_BUCKET)

        blog_html = build_blog_post_html(content, audio_url, level)
        post_title = f"{level} 英語ニュース教材：{title}"
        post_to_wordpress(post_title, blog_html)

        episode_list.append({
            "title": post_title,
            "description": f"今日のニュース：{title}",
            "mp3_url": audio_url,
            "pub_date": datetime.datetime.utcnow()
        })

    # RSSフィード生成（Podbean用）
    rss_xml = generate_rss(
        feed_title="英語で学ぶ経済ニュース",
        site_url="https://yourdomain.com",
        author="Takeyuki Murakami",
        description="毎朝届く、英語で学ぶ最新の経済ニュース。CEFR B1+ / B2対応。",
        episode_list=episode_list
    )
    save_rss(rss_xml, path="/tmp/rss.xml")
    upload_to_s3("/tmp/rss.xml", S3_BUCKET, folder="rss")

    return {"statusCode": 200, "body": "Podcast and blog posted successfully."}