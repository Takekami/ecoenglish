"""Reviewed MP4 -> private YouTube upload, with a durable duplicate ledger.

No rendering, paid speech, scheduler installation or public upload on import.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shorts_source import validate_provenance, validate_usage_review

CHANNEL = 'UC4UkE1AqN_XWkyW3LqChlyQ'
SCOPES = ['https://www.googleapis.com/auth/youtube.upload',
          'https://www.googleapis.com/auth/youtube.readonly']


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def private_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix(path.suffix + '.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def prepare(movie, draft):
    data = json.loads(Path(draft).read_text())
    if Path(movie).suffix.lower() != '.mp4' or digest(movie) != data['sha256']:
        raise ValueError('Video hash differs from the rendered draft')
    bundle = data.get('podcast_provenance') or {}
    if bundle.get('review_status') not in ('manual_preview_review', 'independent_review_passed'):
        raise ValueError('Editorial review is missing')
    if not validate_provenance(bundle.get('selection', {}), bundle.get('script', '')):
        raise ValueError('Podcast provenance is invalid')
    if not validate_usage_review(bundle['selection'], bundle.get('usage_review')):
        raise ValueError('Dictionary/issuer usage review is missing')
    if data.get('example_origin') != 'podcast_script' or not 0 < data['duration_seconds'] <= 180:
        raise ValueError('Expected a source-backed Short of at most 180 seconds')
    title, description = data['title'], data['description']
    if not title.strip() or len(title) > 100 or len(description.encode('utf-8')) > 5000:
        raise ValueError('Invalid YouTube title/description length')
    if any(c in title + description for c in '<>'):
        raise ValueError('YouTube metadata cannot contain angle brackets')
    body = {'snippet': {'title': title, 'description': description,
                        'categoryId': '27', 'defaultLanguage': 'ja'},
            'status': {'privacyStatus': 'private', 'selfDeclaredMadeForKids': False}}
    return {'channel_id': CHANNEL, 'episode_id': str(bundle['episode_id']),
            'video_sha256': data['sha256'], 'body': body}


def review_hash(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def validate_schedule(value, now=None):
    when = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if when.tzinfo is None or when <= (now or datetime.now(timezone.utc)):
        raise ValueError('Publish time must have a timezone and be in the future')
    return when.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def service(token):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if not creds.valid:
        if not creds.refresh_token:
            raise ValueError('Run auth to obtain an offline refresh token')
        creds.refresh(Request())
        private_write(token, json.loads(creds.to_json()))
    return build('youtube', 'v3', credentials=creds, cache_discovery=False)


def verify_channel(youtube):
    items = youtube.channels().list(part='id', mine=True).execute().get('items', [])
    if [item['id'] for item in items] != [CHANNEL]:
        raise ValueError('OAuth identity is not the expected Econenglish channel')


def upload(youtube, movie, plan, ledger, media_factory):
    verify_channel(youtube)
    ledger = Path(ledger)
    ledger.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with closing(sqlite3.connect(ledger)) as db:
        db.execute('CREATE TABLE IF NOT EXISTS uploads (episode TEXT PRIMARY KEY, hash TEXT UNIQUE, state TEXT, video_id TEXT)')
        try:
            db.execute('INSERT INTO uploads VALUES (?, ?, ?, NULL)',
                       (plan['episode_id'], plan['video_sha256'], 'pending'))
            db.commit()
        except sqlite3.IntegrityError:
            raise ValueError('Already uploaded or uncertain prior attempt; inspect the ledger and YouTube Studio') from None
        # Commit BEFORE insert: ambiguous network failures must never auto-retry insert.
        request = youtube.videos().insert(part='snippet,status', body=plan['body'],
                  notifySubscribers=False,
                  media_body=media_factory(str(movie), mimetype='video/mp4', resumable=True))
        result = None
        while result is None:
            _, result = request.next_chunk(num_retries=0)
        video_id = result['id']
        # Save the remote ID before further verification, even if a later read fails.
        db.execute('UPDATE uploads SET state=?, video_id=? WHERE episode=?',
                   ('uploaded', video_id, plan['episode_id']))
        db.commit()
        if result.get('snippet', {}).get('channelId') != CHANNEL or result.get('status', {}).get('privacyStatus') != 'private':
            raise ValueError('Upload response mismatch; inspect Studio before proceeding')
        return video_id


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--token', type=Path, default=Path('.youtube-secrets/token.json'))
    sub = p.add_subparsers(dest='command', required=True)
    auth = sub.add_parser('auth')
    auth.add_argument('--client', type=Path, required=True)
    for name in ('prepare', 'upload'):
        q = sub.add_parser(name)
        q.add_argument('--video', type=Path, required=True)
        q.add_argument('--draft', type=Path, required=True)
        q.add_argument('--review', type=Path, required=True)
        if name == 'upload':
            q.add_argument('--ledger', type=Path, default=Path('output/youtube/uploads.sqlite3'))
    schedule = sub.add_parser('schedule')
    schedule.add_argument('--video-id', required=True)
    schedule.add_argument('--publish-at', required=True)
    schedule.add_argument('--confirm-public-release', action='store_true')
    args = p.parse_args()
    if args.command == 'auth':
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(str(args.client), SCOPES)
        creds = flow.run_local_server(host='127.0.0.1', port=0, access_type='offline',
                                     prompt='consent', authorization_prompt_message='Complete authorization in your browser.',
                                     success_message='Authorization complete. You may close this tab.')
        private_write(args.token, json.loads(creds.to_json()))
        verify_channel(service(args.token))
        print('Econenglish channel verified; token saved locally (not printed).')
    elif args.command in ('prepare', 'upload'):
        plan = prepare(args.video, args.draft)
        if args.command == 'prepare':
            private_write(args.review, {'plan': plan, 'review_sha256': review_hash(plan),
                          'approved': False, 'audio_and_video_checked': False})
            print(f'Review created: {args.review}. Inspect the MP4 and metadata before approving.')
        else:
            review = json.loads(args.review.read_text())
            if (review.get('approved') is not True or review.get('audio_and_video_checked') is not True
                    or review.get('plan') != plan or review.get('review_sha256') != review_hash(plan)):
                raise ValueError('Review approval is missing or video/metadata changed')
            from googleapiclient.http import MediaFileUpload
            print('Private upload:', upload(service(args.token), args.video, plan, args.ledger, MediaFileUpload))
    else:
        if not args.confirm_public_release:
            raise ValueError('Scheduling makes the video public; pass --confirm-public-release after review')
        when = validate_schedule(args.publish_at)
        youtube = service(args.token)
        verify_channel(youtube)
        items = youtube.videos().list(part='snippet,status,processingDetails', id=args.video_id).execute().get('items', [])
        if len(items) != 1 or items[0]['snippet']['channelId'] != CHANNEL:
            raise ValueError('Video does not belong to Econenglish')
        video = items[0]
        if video['status'].get('privacyStatus') != 'private' or video['status'].get('uploadStatus') != 'processed':
            raise ValueError('Video must be private and successfully processed; inspect Studio')
        status = {k: v for k, v in video['status'].items() if k in
                  ('privacyStatus', 'selfDeclaredMadeForKids', 'embeddable', 'license', 'publicStatsViewable', 'containsSyntheticMedia')}
        status['publishAt'] = when
        result = youtube.videos().update(part='status', body={'id': args.video_id, 'status': status}).execute()
        if result.get('status', {}).get('publishAt') != when:
            # API can normalize timestamps, so compare instants.
            actual = result.get('status', {}).get('publishAt', '')
            if not actual or datetime.fromisoformat(actual.replace('Z', '+00:00')) != datetime.fromisoformat(when.replace('Z', '+00:00')):
                raise ValueError('Schedule was not confirmed; inspect Studio')
        print('Scheduled:', args.video_id, when)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Google HTTP exceptions can contain credential URLs/payloads. Do not print them.
        if isinstance(error, ValueError):
            print(str(error), file=sys.stderr)
        else:
            print(f'{type(error).__name__}: operation stopped; inspect Studio before retrying an upload.', file=sys.stderr)
        sys.exit(1)
