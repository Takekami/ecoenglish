"""Verbatim Podcast-script excerpts for Shorts. No network or publishing writes."""
import hashlib
import json
import re
from datetime import date
from urllib.parse import urlsplit


def script_digest(script):
    return hashlib.sha256(script.encode('utf-8')).hexdigest()


def candidate_from_sections(sections):
    """Optional generated selection; a missing or invalid selection is skipped.

    Never use Vocabulary example sentences: they may be invented practice text.
    Offsets refer to the exact Script used by the Podcast TTS, without rewriting.
    Japanese translations still require independent semantic review.
    """
    raw = sections.get('Shorts Candidate', '')
    if not raw or raw.strip() == 'null':
        return None
    try:
        item = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(item, dict):
        return None
    fields = ('expression', 'meaning_ja', 'sentence', 'sentence_ja')
    if any(not isinstance(item.get(k), str) or not item[k].strip() for k in fields):
        return None
    expression, quote = item['expression'], item['sentence']
    script = sections.get('Script', '')
    if (not isinstance(script, str) or expression != expression.strip()
            or quote != quote.strip() or not 2 <= len(expression.split()) <= 6
            or not 5 <= len(quote.split()) <= 35 or len(quote) > 350
            or quote[-1] not in '.!?' or '\n' in quote
            or any(len(item[k]) > 250 for k in ('meaning_ja', 'sentence_ja'))
            or any(not re.search(r'[ぁ-んァ-ヶ一-龠]', item[k])
                   for k in ('meaning_ja', 'sentence_ja'))):
        return None
    start = script.find(quote)
    if start < 0:
        return None
    # Require a complete source sentence, rather than silently dropping a modal,
    # negation, attribution or a leading clause from the original.
    before = script[:start].rstrip()
    if before and before[-1] not in '.!?':
        return None
    end = start + len(quote)
    if end < len(script) and not script[end].isspace():
        return None
    term = re.search(r'(?<!\w)'+re.escape(expression)+r'(?!\w)', quote, re.I)
    if not term:
        return None
    # Preserve the surface form actually heard, including articles/plurals.
    result = {key: item[key] for key in fields}
    result.update(expression=term.group(), script_sha256=script_digest(script),
                  sentence_start=start, sentence_end=end,
                  expression_start=start+term.start(), expression_end=start+term.end())
    extension = item.get('extension')
    if extension is not None:
        keys = ('label', 'japanese', 'english', 'intro', 'note')
        if (not isinstance(extension, dict)
                or any(not isinstance(extension.get(k), str) or not extension[k].strip()
                       or len(extension[k]) > 250 for k in keys)):
            return None
        result['extension'] = {k: extension[k] for k in keys}
    return result


def validate_provenance(item, script):
    try:
        start, end = item['sentence_start'], item['sentence_end']
        term_start, term_end = item['expression_start'], item['expression_end']
        return (all(type(n) is int for n in (start, end, term_start, term_end))
                and 0 <= start <= term_start < term_end <= end <= len(script)
                and item['script_sha256'] == script_digest(script)
                and script[start:end] == item['sentence']
                and script[term_start:term_end] == item['expression'])
    except (KeyError, TypeError):
        return False


def validate_usage_review(selection, review):
    """Validate a separately recorded primary-source editorial check.

    This does not fetch a page or establish frequency. The editor must actually
    read the reference; generation output is never accepted as its own review.
    """
    if not isinstance(review, dict) or review.get('status') != 'verified':
        return False
    if (review.get('expression') != selection.get('expression')
            or review.get('script_sha256') != selection.get('script_sha256')
            or review.get('method') != 'primary_source_editorial_check'):
        return False
    note = review.get('transfer_note_ja', '')
    contexts = review.get('reuse_contexts_ja', [])
    if (not isinstance(note, str) or not re.search(r'[ぁ-んァ-ヶ一-龠]', note)
            or not isinstance(contexts, list) or len(set(map(str, contexts))) < 2
            or any(not isinstance(x, str) or not x.strip() for x in contexts)):
        return False
    references = review.get('references')
    if not isinstance(references, list) or not references:
        return False
    for ref in references:
        if not isinstance(ref, dict) or ref.get('kind') not in ('dictionary', 'company_announcement'):
            return False
        if any(not isinstance(ref.get(k), str) or not ref[k].strip()
               for k in ('url', 'publisher', 'title', 'excerpt', 'checked_on')):
            return False
        try:
            url = urlsplit(ref['url'])
            if url.scheme != 'https' or not url.hostname or url.username or url.password:
                return False
            date.fromisoformat(ref['checked_on'])
        except ValueError:
            return False
        if not re.search(r'(?<!\w)'+re.escape(selection['expression'])+r'(?!\w)',ref['excerpt'],re.I):
            return False
    return True


def draft_bundle(candidate, script, *, episode_id, lesson_url, source_url,
                 title, published_at, review_status):
    if not validate_provenance(candidate, script):
        raise ValueError('Shorts example no longer matches its Podcast script')
    return {
        'schema_version': 1, 'status': 'editorial_draft',
        'review_status': review_status, 'published_at': published_at,
        'usage_review_status': 'pending_primary_source_check',
        'episode_id': str(episode_id), 'lesson_url': lesson_url,
        'source_url': source_url, 'episode_title': title,
        'script': script, 'selection': candidate,
        'youtube_upload_performed': False,
    }
