"""Convert a verified script/excerpt bundle into a source-backed video manifest."""
import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit, urlunsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shorts_source import validate_provenance, validate_usage_review


def video_from_bundle(bundle, voice='marin'):
    bundle = dict(bundle)
    if bundle.get('review_status') not in ('independent_review_passed', 'manual_preview_review'):
        raise ValueError('The excerpt and Japanese translations require editorial review')
    item, script = bundle['selection'], bundle['script']
    if not validate_provenance(item, script):
        raise ValueError('Podcast quote, expression or source script was changed')
    if not validate_usage_review(item, bundle.get('usage_review')):
        raise ValueError('Verify dictionary/company usage and reusable contexts before video generation')
    bundle['usage_review_status'] = 'verified'
    episode = bundle['episode_id']
    if not re.fullmatch(r'\d+', episode):
        raise ValueError('A real numeric Podcast episode ID is required')
    date = bundle['published_at'][:10].replace('-', '.')
    url = urlsplit(bundle['lesson_url'])
    expression_url = urlunsplit((url.scheme, url.netloc, url.path, url.query, 'eel-expressions'))
    v = {
        'id': f'podcast-{episode}', 'japanese_voice': voice,
        'title': f'「{item["meaning_ja"]}」を英語で｜Podcastの一文',
        'japanese_term': item['meaning_ja'], 'english_term': item['expression'],
        'hook_audio': f'「{item["meaning_ja"]}」。今日は、こんな英語表現を覚えましょう。',
        'english_example': item['sentence'], 'translation': item['sentence_ja'],
        'translation_audio': f'「{item["sentence_ja"].rstrip("。") }」という意味です。',
        'source_label': f'Podcast教材：{date}公開回',
        'source_url': bundle['lesson_url'], 'lesson_url': expression_url,
        'example_origin': 'podcast_script',
        'podcast_provenance': bundle,
    }
    if item.get('extension'):
        v['extension'] = item['extension']
    return v


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--voice', choices=('marin', 'cedar'), default='marin')
    p.add_argument('--usage-review', type=Path, help='Separately checked dictionary/issuer evidence JSON')
    args = p.parse_args()
    bundle = json.loads(args.bundle.read_text())
    if args.usage_review:
        bundle['usage_review'] = json.loads(args.usage_review.read_text())
    v = video_from_bundle(bundle, args.voice)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        'version':6, 'format':'podcast_script_expression',
        'publication_status':'local_preview_only','videos':[v],
    },ensure_ascii=False,indent=2))
    print(args.output)


if __name__ == '__main__':
    main()
