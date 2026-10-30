"""Fail-closed checks shared by generation and publishing (no external writes)."""
import html
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

import requests
import trafilatura

SECTIONS = (
    "Script", "Vocabulary", "Listening Questions", "Reading Questions", "Answers",
    "Grammar Point", "Grammar Quote", "使用場面", "使用例文", "日本語での経済ニュース解説",
    "Japanese Title", "Meta Description", "Introduction",
)
SOURCE_HOSTS = {"asia.nikkei.com", "www.channelnewsasia.com", "www.cnbc.com"}


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain_text(value):
    parser = PlainText()
    parser.feed(str(value or ""))
    return re.sub(r"\s+", " ", html.unescape(" ".join(parser.parts))).strip()


def enough_source(text):
    # A minimum is a screening heuristic, not evidence of truth/completeness.
    return len(re.findall(r"\b[\w'-]+\b", text)) >= 120


def source_text(url, rss_text, diagnostics=None):
    """Prefer extracted article body. Never bypass paywalls or follow redirects.

    Only the three configured publishers may be requested. Long RSS content can
    be used when extraction is unavailable; headlines/short summaries cannot.
    """
    detail = diagnostics if isinstance(diagnostics, dict) else {}
    detail.update(reason='SOURCE_UNAVAILABLE', article_words=0,
                  rss_words=len(plain_text(rss_text).split()))
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in SOURCE_HOSTS
            or parsed.port not in (None, 443) or parsed.username or parsed.password):
        detail['reason'] = 'SOURCE_URL_NOT_ALLOWED'
        return ""
    try:
        with requests.get(url, timeout=(5, 15), allow_redirects=False, stream=True) as response:
            detail['http_status'] = response.status_code
            detail['reason'] = f'HTTP_{response.status_code}'
            if response.status_code == 200 and "text/html" in response.headers.get("Content-Type", ""):
                chunks, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > 2_000_000:
                        detail['reason'] = 'SOURCE_TOO_LARGE'
                        break
                    chunks.append(chunk)
                else:
                    body = trafilatura.extract(
                        b"".join(chunks), include_comments=False, include_tables=False,
                    ) or ""
                    detail['article_words'] = len(body.split())
                    if enough_source(body):
                        detail['reason'] = 'ARTICLE_EXTRACTED'
                        return body[:24000]
                    detail['reason'] = 'EXTRACTED_TEXT_TOO_SHORT'
    except (requests.RequestException, ValueError) as error:
        detail['reason'] = type(error).__name__
    fallback = plain_text(rss_text)
    if enough_source(fallback):
        detail['reason'] = 'SUBSTANTIVE_RSS_FALLBACK'
        return fallback[:24000]
    return ''


def parse_lesson(md):
    sections = {}
    matches = list(re.finditer(r"^### ([^\n]+)\s*$", md, re.M))
    for index, match in enumerate(matches):
        name = match.group(1).strip()
        if name in sections:
            raise ValueError(f"duplicate section: {name}")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(md)
        sections[name] = md[match.end():end].strip().removesuffix("```").strip()
    return sections


def normalized(text):
    return re.sub(r"\s+", " ", text.translate(str.maketrans({"’": "'", "“": '"', "”": '"'}))).strip()


def validate_lesson(sections):
    errors = [f"missing {name}" for name in SECTIONS if not sections.get(name)]
    if errors:
        return errors
    quote = sections["Grammar Quote"].strip('“”"')
    if normalized(quote) not in normalized(sections["Script"]) or len(quote.split()) < 5:
        errors.append("grammar quote not in script")
    if normalized(quote) not in normalized(sections["Grammar Point"]):
        errors.append("grammar explanation must quote the selected script sentence")
    # Catch a concrete recurring mismatch; semantic review still handles other grammar.
    label = sections['Grammar Point'].split('–')[0].split('—')[0].lower()
    if ('present perfect' in label or '現在完了' in label) and not re.search(
            r"\b(?:have|has)\s+(?!(?:to|a|an|the)\b)\w+", quote, re.I):
        errors.append('present perfect label does not match quoted sentence')
    for name, count in (("Listening Questions", 3), ("Reading Questions", 3), ("Answers", 6)):
        numbers = re.findall(r"^(\d+)\.\s+\S", sections[name], re.M)
        if numbers != [str(i) for i in range(1, count + 1)]:
            errors.append(f"invalid numbered items in {name}")
    listening = sections["Listening Questions"]
    if not re.search(r"^1\.\s+True/False:", listening, re.M):
        errors.append("missing True/False question")
    for item in re.split(r"^\d+\. ", listening, flags=re.M)[2:]:
        if re.findall(r"^\s*([a-d])\)\s+\S", item, re.M) != list("abcd"):
            errors.append("MCQ requires a-d options")
    if len(re.findall(r"^- ", sections["Vocabulary"], re.M)) != 5:
        errors.append("vocabulary requires five entries")
    for name, minimum, maximum in (("Japanese Title", 10, 90), ("Meta Description", 50, 160), ("Introduction", 60, 500)):
        value = sections[name]
        if not minimum <= len(value) <= maximum or not re.search(r"[ぁ-んァ-ヶ一-龠]", value):
            errors.append(f"invalid Japanese metadata: {name}")
        if re.search(r"[<>\n]|https?://|###", value):
            errors.append(f"metadata must be plain text: {name}")
    return errors
