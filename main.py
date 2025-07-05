import datetime, os, random
from pathlib import Path

import feedparser, openai

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

REQ = [OPENAI_API_KEY, S3_BUCKET, WP_URL, WP_USER, WP_APP_PASS,
       PODBEAN_ID, PODBEAN_SECRET]
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
    body = md[start:nxt if nxt > -1 else None].strip()
    return body

# ---------- Lambda ----------

def handler(event=None, context=None):
    # 1) 記事選定 ----------------------------------------------------------
    art = None
    for _ in range(MAX_TRIES):
        candidate = fetch_article(select_feed())
        if not candidate:
            continue
        if not gpt("B1+", candidate.title, candidate.summary, candidate.link).startswith("SKIP"):
            art = candidate
            break

    if not art:
        return {"statusCode": 500, "body": "No suitable article"}

    title, summary, link = art.title, art.summary, art.link
    today = datetime.date.today()

    # 2) GPT 生成 ----------------------------------------------------------
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

    # 3) TTS → S3 → Blog --------------------------------------------------
    mp3_path   = synthesize_speech(script, f"{today}.mp3")
    audio_url  = upload_to_s3(mp3_path, S3_BUCKET)  # for blog use

    html = build_blog_post_html(
        "B1–C1", title, link,
        script, vocab, lq, rq, ans, gp, jp, audio_url
    )
    post_to_wordpress(f"英語ニュース教材：{title}（B1–C1対応）", html)

    # 4) Podbean (直接アップロード) ----------------------------------------
    ep_link = upload_episode_to_podbean(
        f"{title}（B1–C1対応）",
        mp3_path,               # <- ローカル音声ファイル
        summary,
    )

    # 5) RSS 生成 & S3 -----------------------------------------------------
    rss_xml = generate_rss(
        "英語で学ぶ経済ニュース",
        "https://econenglish.jp/",
        "Summary Samurai",
        "最新の経済ニュースを英語で学ぶ。",
        [{
            "title": f"{title}（B1–C1対応）",
            "description": summary,
            "mp3_url": audio_url,
            "pub_date": datetime.datetime.utcnow(),
        }],
    )
    tmp = Path("/tmp/rss.xml")
    save_rss(rss_xml, tmp)
    upload_to_s3(tmp, S3_BUCKET, "rss")

    return {"statusCode": 200, "body": "Done"}
