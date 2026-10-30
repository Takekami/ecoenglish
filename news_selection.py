"""Bounded, multi-publisher selection. No AI calls or publishing side effects."""
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
import re
from urllib.parse import urlsplit, urlunsplit

import feedparser
import requests

from content_quality import SOURCE_HOSTS, plain_text

MAX_PER_FEED = 6
MAX_AGE_DAYS = 7


def canonical_url(url):
    try:
        p = urlsplit(url)
        if p.scheme != 'https' or p.hostname not in SOURCE_HOSTS or p.username or p.password or p.port not in (None, 443):
            return None
        return urlunsplit((p.scheme, p.netloc.lower(), p.path.rstrip('/'), p.query, ''))
    except (TypeError, ValueError):
        return None


def candidate_id(url):
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def entry_time(entry):
    for key in ('published', 'updated'):
        value = entry.get(key)
        if not value:
            continue
        try:
            stamp = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            try:
                stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (TypeError, ValueError):
                continue
        if stamp.tzinfo is not None:
            return stamp.astimezone(timezone.utc)
    return None


def collect_candidates(feeds, emit, recent_urls=(), now=None):
    now = now or datetime.now(timezone.utc)
    seen = set(recent_urls)
    candidates = []
    for feed in feeds:
        try:
            response = requests.get(feed, timeout=(4, 10), allow_redirects=False)
            response.raise_for_status()
            if len(response.content) > 2_000_000:
                emit('feed_rejected', feed=feed, reason='FEED_TOO_LARGE')
                continue
            entries = feedparser.parse(response.content).entries
        except requests.RequestException as error:
            emit('feed_failed', feed=feed, reason=type(error).__name__)
            continue
        eligible = []
        for entry in entries:
            url = canonical_url(entry.get('link'))
            title = plain_text(entry.get('title', ''))[:350]
            if not url or not title:
                continue
            cid = candidate_id(url)
            if url in seen:
                emit('candidate_rejected', candidate_id=cid, url=url, reason='DUPLICATE_OR_ALREADY_PUBLISHED')
                continue
            seen.add(url)
            stamp = entry_time(entry)
            if stamp and (stamp < now - timedelta(days=MAX_AGE_DAYS) or stamp > now + timedelta(hours=6)):
                emit('candidate_rejected', candidate_id=cid, url=url, reason='SOURCE_DATE_OUT_OF_RANGE', source_date=stamp.isoformat())
                continue
            snippets = [entry.get('summary', ''), entry.get('description', '')]
            snippets.extend(c.get('value', '') for c in entry.get('content', []) if isinstance(c, dict))
            summary = max((plain_text(s) for s in snippets), key=len, default='')[:4000]
            eligible.append({'id':cid, 'title':title, 'url':url, 'summary':summary,
                             'feed':feed, 'published_at':stamp.isoformat() if stamp else None})
        eligible.sort(key=lambda c: c['published_at'] or '', reverse=True)
        for c in eligible[:MAX_PER_FEED]:
            emit('candidate_collected', candidate_id=c['id'], title=c['title'], url=c['url'],
                 feed=feed, source_date=c['published_at'], reason='DATE_UNKNOWN' if not c['published_at'] else 'ELIGIBLE')
        candidates.extend(eligible[:MAX_PER_FEED])
        emit('feed_scanned', feed=feed, entries=len(entries), shortlisted=min(len(eligible), MAX_PER_FEED))
    return candidates


def recent_lessons(emit):
    """Read public lesson provenance; failure must be visible, not a false empty history."""
    try:
        r = requests.get('https://econenglish.jp/wp-json/wp/v2/posts', params={
            'per_page':30, '_fields':'id,title,content'}, timeout=(4, 10), allow_redirects=False)
        r.raise_for_status()
        posts = r.json()
        if not isinstance(posts, list):
            raise ValueError('invalid history response')
        urls, titles = set(), []
        for post in posts:
            titles.append(plain_text(post.get('title', {}).get('rendered', ''))[:250])
            for href in re.findall(r'href=[\"\']([^\"\']+)', post.get('content', {}).get('rendered', '')):
                url = canonical_url(href)
                if url:
                    urls.add(url)
        emit('history_loaded', lessons=len(posts), source_urls=len(urls))
        return urls, titles
    except (requests.RequestException, ValueError, TypeError, KeyError) as error:
        emit('history_failed', reason=type(error).__name__)
        return None, None


def parse_ranking(raw, candidates, emit):
    """Require one well-typed verdict per submitted candidate; fail closed."""
    import json
    rows = json.loads(raw)['candidates']
    if not isinstance(rows, list) or len(rows) != len(candidates):
        raise ValueError('ranking coverage mismatch')
    by_id = {c['id']:c for c in candidates}
    seen, accepted = set(), []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str):
            raise ValueError('invalid ranking row')
        cid = row.get('id')
        if cid not in by_id or cid in seen:
            raise ValueError('invalid/duplicate ranking ID')
        seen.add(cid)
        dimensions = ('economic_relevance', 'learning_value', 'comprehensibility', 'novelty')
        if any(type(row.get(k)) is not int or not 0 <= row[k] <= 3 for k in dimensions):
            raise ValueError('invalid ranking score')
        if type(row.get('eligible')) is not bool or not isinstance(row.get('reason'), str) or not row['reason'].strip():
            raise ValueError('invalid ranking explanation')
        fit = row['eligible'] and all(row[k] >= 2 for k in dimensions[:3])
        score = 3*row['economic_relevance'] + 3*row['learning_value'] + 2*row['comprehensibility'] + row['novelty']
        emit('candidate_ranked', candidate_id=cid, url=by_id[cid]['url'], accepted=fit,
             reason=row['reason'][:500], scores={k:row[k] for k in dimensions}, score=score)
        if fit:
            accepted.append(dict(by_id[cid], score=score, selection_reason=row['reason'][:500]))
    return sorted(accepted, key=lambda c:(c['score'], c['published_at'] or ''), reverse=True)
