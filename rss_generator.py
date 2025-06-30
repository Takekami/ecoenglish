# utils/rss_generator.py
import datetime
import xml.etree.ElementTree as ET

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
  <enclosure url="{mp3_url}" type="audio/mpeg"/>
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
            title=ep["title"],
            description=ep["description"],
            mp3_url=ep["mp3_url"],
            pub_date=format_rfc2822(ep["pub_date"])
        )

    return RSS_TEMPLATE.format(
        title=feed_title,
        site_url=site_url,
        description=description,
        author=author,
        items=items_xml
    )

def save_rss(xml_str, path="rss.xml"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml_str)
