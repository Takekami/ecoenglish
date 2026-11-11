"""Official text sources and their reviewed reuse notices (2026-11-11)."""
from urllib.parse import urlsplit
from datetime import datetime, timezone, timedelta

STAT_UPDATES = 'https://www.stat.go.jp/english/whatsnew/index.html'
FEEDS = [
    STAT_UPDATES,
    'https://www.mof.go.jp/english/news.rss',
    'https://apps.bea.gov/rss/rss.xml',
    'https://www.federalreserve.gov/feeds/press_monetary.xml',
    'https://www.federalreserve.gov/feeds/speeches.xml',
]
SOURCES = {
    'www.stat.go.jp': ('総務省統計局', 'PDL 1.0', 'https://www.stat.go.jp/info/riyou.html'),
    'www.mof.go.jp': ('財務省', 'PDL 1.0', 'https://www.mof.go.jp/english/about_mof/notice/index.html'),
    'www.bea.gov': ('U.S. Bureau of Economic Analysis', 'Public domain', 'https://www.bea.gov/help/faq/147'),
    'www.federalreserve.gov': ('Federal Reserve Board', 'Public domain', 'https://www.federalreserve.gov/disclaimer.htm'),
}


def source_credit(url):
    return SOURCES.get(urlsplit(url).hostname)


def history_key(url, published_at=None):
    # Statistics Bureau result pages are updated in place for each release.
    if urlsplit(url).hostname == 'www.stat.go.jp' and published_at:
        stamp = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        if stamp.tzinfo is not None:
            stamp = stamp.astimezone(timezone(timedelta(hours=9)))
        return url + '|' + stamp.date().isoformat()
    return url
