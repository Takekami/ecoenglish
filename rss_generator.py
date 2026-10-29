# utils/rss_generator.py
import datetime
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

RSS_TEMPLATE = """
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{title}</title>
    <link>{site_url}</link>
    <description>{description}</description>
    <language>en-us</language>
    <itunes:author>{author}</itunes:author>
    <itunes:explicit>no</itunes:explicit>
    <itunes:category text="Education"/>
    {items}
  </channel>
</rss>
"""

ITEM_TEMPLATE = """
<item>
  <title>{title}</title>
  <description>{description}</description>
  <enclosure url={mp3_attr} type="audio/mpeg"/>
  <guid>{mp3_url}</guid>
  <pubDate>{pub_date}</pubDate>
</item>
"""

def format_rfc2822(dt):
    return dt.strftime('%a, %d %b %Y %H:%M:%S +0000')

def generate_rss(feed_title, site_url, author, description, episode_list):
    items_xml = ""
    for ep in episode_list:
        items_xml += ITEM_TEMPLATE.format(
            title=escape(ep["title"]),
            description=escape(ep["description"]),
            mp3_url=escape(ep["mp3_url"]),
            mp3_attr=quoteattr(ep["mp3_url"]),
            pub_date=format_rfc2822(ep["pub_date"])
        )

    return RSS_TEMPLATE.format(
        title=escape(feed_title),
        site_url=escape(site_url),
        description=escape(description),
        author=escape(author),
        items=items_xml
    ).strip()

def save_rss(xml_str, path="rss.xml"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml_str)
