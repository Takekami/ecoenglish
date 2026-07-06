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

# ---------- Environment variables ----------
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

# ---------- Constants ----------
BLOG_URL = "https://econenglish.jp/category/english-learning/"
LEVEL_LABEL = "B1–B2"
RSS_FEED_TITLE = "Econenglish — Asia Business English (B1–B2)"
RSS_FEED_DESCRIPTION = (
    "Daily Asia-Pacific business news in English for Japanese intermediate learners. "
    "Full scripts & quizzes at econenglish.jp"
)
RSS_AUTHOR = "Econenglish"
SPREAKER_DESCRIPTION = (
    "Daily Asia-Pacific business news, rewritten for intermediate English learners (B1–B2).\n\n"
    "Full script, vocabulary, grammar notes, quizzes & Japanese commentary:\n"
    f"{BLOG_URL}"
)

RSS_FEEDS = [
    "https://asia.nikkei.com/rss/feed/nar",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
]
MAX_TRIES = 5
LOG_PREFIX = "[ecoenglish]"

# ---------- Helper Functions ----------

def _log(message: str) -> None:
    print(f"{LOG_PREFIX} {message}")

def select_feed() -> str:
    """Rotate feed daily so we don't always hit the same source."""
    return RSS_FEEDS[datetime.date.today().toordinal() % len(RSS_FEEDS)]

def _entry_summary(entry) -> str | None:
    for key in ("summary", "description", "content"):
        val = getattr(entry, key, None)
        if val and str(val).strip():
            return str(val).strip()
    title = getattr(entry, "title", None)
    return title.strip() if title else None

def fetch_article(url: str):
    feed = feedparser.parse(url)
    candidates = [e for e in feed.entries if _entry_summary(e)]
    if not candidates:
        _log(
            f"fetch=empty entries={len(feed.entries)} "
            f"bozo={feed.bozo} feed={url}"
        )
        return None
    entry = random.choice(candidates)
    if not getattr(entry, "summary", None):
        entry.summary = _entry_summary(entry)
    return entry

def is_significant(title: str, summary: str, link: str) -> tuple[bool, str]:
    """Determine if the article is economically or socially significant."""
    prompt = f"""
### ROLE
You are a concise classifier.

### TASK
Read the following headline and summary, then decide if it is economically or socially significant
(Asia-Pacific business, markets, trade, tech, or policy preferred).
Reply with **yes** or **no** only.

Title: {title}
Summary: {summary}
URL: {link}
"""
    r = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    ans = r.choices[0].message.content.strip()
    return ans.lower().startswith("yes"), ans

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

# ---------- Lambda Handler ----------

def handler(event=None, context=None):
    # 1) Article selection ----------------------------------------------------------
    feed_url = select_feed()
    _log(f"START feed={feed_url}")

    art = None
    for attempt in range(1, MAX_TRIES + 1):
        candidate = fetch_article(feed_url)
        if not candidate:
            continue
        accepted, classifier = is_significant(
            candidate.title, candidate.summary, candidate.link
        )
        _log(
            f"try={attempt} gate=1 classifier={classifier!r} "
            f"significant={'yes' if accepted else 'no'} "
            f"title={candidate.title!r} link={candidate.link}"
        )
        if accepted:
            art = candidate
            break

    if not art:
        _log(f"result=NO_ARTICLE tries={MAX_TRIES} feed={feed_url}")
        return {"statusCode": 500, "body": "No suitable article"}

    title, summary, link = art.title, art.summary, art.link
    _log(f"gate=1 passed title={title!r} link={link}")

    # 2) GPT to generate content --------------------------------------------
    md = gpt("B1+", title, summary, link)
    if md.startswith("SKIP"):
        _log(f"result=SKIP gate=2 title={title!r} link={link}")
        return {"statusCode": 204, "body": "Article skipped"}

    _log("gate=2 passed, publishing")

    script = extract(md, "Script")
    vocab  = extract(md, "Vocabulary")
    lq     = extract(md, "Listening Questions")
    rq     = extract(md, "Reading Questions")
    ans    = extract(md, "Answers")
    gp     = extract(md, "Grammar Point")
    jp     = extract(md, "日本語での経済ニュース解説")
    usage  = extract(md, "使用場面")
    example_usage= extract(md, "使用例文")

    # 3) TTS to S3 upload
    mp3_path  = synthesize_speech(script, "news_episode.mp3")
    upload_to_s3(mp3_path, S3_BUCKET, "audio")

    # 4) Spreaker to upload episode and get stream URL
    episode = upload_episode_to_spreaker(
        local_audio_path=mp3_path,
        title=f"{title} | Asia Business English ({LEVEL_LABEL})",
        description=SPREAKER_DESCRIPTION,
        scheduled_at=None,
    )
    # Set stream URL to audio_url
    audio_url = episode.get("stream_url") or episode.get("download_url")
    print("🎧 audio_url:", audio_url)

    # 5) Post to blog and build HTML
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
    wp_link = post_to_wordpress(f"【Asia Business English】{title}（{LEVEL_LABEL}）", html)
    if not wp_link:
        _log(f"result=WP_FAILED title={title!r} link={link}")
    else:
        _log(f"result=SUCCESS title={title!r} link={link} wordpress={wp_link}")

    # 6) RSS to generate and upload to S3 ----------------------------------------
    rss_xml = generate_rss(
        RSS_FEED_TITLE,
        "https://econenglish.jp/",
        RSS_AUTHOR,
        RSS_FEED_DESCRIPTION,
        [{
        "title": f"{title} | Asia Business English ({LEVEL_LABEL})",
        "description": summary,
        "mp3_url": audio_url,
        "pub_date": datetime.datetime.utcnow(),
        }],
    )
    tmp = Path("/tmp/rss.xml")
    save_rss(rss_xml, tmp)
    upload_to_s3(tmp, S3_BUCKET, "rss")

    return {"statusCode": 200, "body": "Done"}
