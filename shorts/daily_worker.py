"""Mac worker: published Podcast bundle -> attestation -> render -> PRIVATE upload."""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
from urllib.parse import unquote, urlsplit, parse_qs, urlunsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from content_quality import plain_text
from shorts_source import validate_provenance
from youtube_upload import CHANNEL, prepare, private_write, service, upload, verify_channel
from usage_check import verify_usage


def emit(stage, **fields):
    print(json.dumps({'system':'econenglish-shorts','time':datetime.now(timezone.utc).isoformat(),
                      'stage':stage,**fields},ensure_ascii=False),flush=True)


def job_id(bundle):
    if not re.fullmatch(r'\d+',str(bundle.get('episode_id',''))):
        raise ValueError('INVALID_EPISODE_ID')
    digest=bundle.get('selection',{}).get('script_sha256','')
    if not isinstance(digest,str) or not re.fullmatch(r'[0-9a-f]{64}',digest):
        raise ValueError('INVALID_SCRIPT_HASH')
    return bundle['episode_id']+'-'+digest[:12]


def verify_lesson(bundle):
    import requests
    if bundle.get('review_status')!='independent_review_passed' or not validate_provenance(bundle['selection'],bundle['script']):
        raise ValueError('UNREVIEWED_OR_CHANGED_SOURCE')
    url=urlsplit(bundle['lesson_url'])
    if url.scheme!='https' or url.hostname!='econenglish.jp' or url.username or url.password or url.port not in (None,443):
        raise ValueError('INVALID_LESSON_URL')
    ids=parse_qs(url.query).get('p',[])
    params={'_fields':'id,status,date_gmt,link,content'}
    endpoint='https://econenglish.jp/wp-json/wp/v2/posts'
    if ids:
        endpoint+='/'+str(int(ids[0]))
    else:
        params.update(slug=unquote(url.path.strip('/')),per_page=1)
    r=requests.get(endpoint,params=params,timeout=(5,20),allow_redirects=False)
    r.raise_for_status();data=r.json()
    post=data[0] if isinstance(data,list) and len(data)==1 else data
    if not isinstance(post,dict) or post.get('status')!='publish':
        raise ValueError('LESSON_NOT_PUBLISHED')
    source_date=datetime.fromisoformat(post['date_gmt']).replace(tzinfo=timezone.utc)
    bundle_date=datetime.fromisoformat(bundle['published_at'])
    if bundle_date.tzinfo is None or abs((bundle_date-source_date).total_seconds())>3600:
        raise ValueError('PUBLICATION_TIME_MISMATCH')
    if not re.fullmatch(r'\d+',bundle['episode_id']):
        raise ValueError('INVALID_EPISODE_ID')
    content=post['content']['rendered']
    headings=list(re.finditer(r'<h2\b[^>]*>(.*?)</h2>',content,re.S|re.I))
    script=None
    for i,h in enumerate(headings):
        if 'Script' in plain_text(h.group(1)):
            script=plain_text(content[h.end():headings[i+1].start() if i+1<len(headings) else len(content)])
            break
    if script!=plain_text(bundle['script']):
        raise ValueError('PUBLISHED_SCRIPT_MISMATCH')
    # Reviewed expression cards are not yet available on every lesson.
    return '#eel-expressions' if 'id="eel-expressions"' in content else '#eel-script'


def process_bundle(bundle, config, root, *, lesson_check=verify_lesson, usage_check=verify_usage,
                   renderer=None, client=None, youtube=None, media_factory=None):
    job=job_id(bundle)
    episode=bundle['episode_id']
    work=root/job;work.mkdir(parents=True,exist_ok=True)
    state_path=work/'state.json'
    if state_path.exists():
        state=json.loads(state_path.read_text())
        emit('job_already_handled',job=job,state=state['state'])
        return state
    state={'job':job,'state':'started','episode_id':episode}
    private_write(state_path,state)  # fail closed on interruption, not silent rerun
    try:
        fragment=lesson_check(bundle)
        emit('lesson_verified',job=job)
        ledger=Path(config['upload_ledger'])
        if ledger.exists():
            with sqlite3.connect(ledger) as db:
                row=db.execute('SELECT state,video_id FROM uploads WHERE episode=?',(episode,)).fetchone()
            if row:
                state.update(state='already_uploaded' if row[0]=='uploaded' else 'upload_uncertain',video_id=row[1])
                private_write(state_path,state);return state
        if client is None:
            from openai import OpenAI
            from japanese_voice_samples import key_from_environment
            client=OpenAI(api_key=key_from_environment(),max_retries=0,timeout=90)
        bundle=dict(bundle)
        bundle['usage_review']=usage_check(bundle,client,work)
        emit('usage_verified',job=job)
        from from_podcast import video_from_bundle
        date=datetime.fromisoformat(bundle['published_at'])
        voice='marin' if date.date().toordinal()%2==0 else 'cedar'
        video=video_from_bundle(bundle,voice)
        if len(video['title'])>100:raise ValueError('TITLE_TOO_LONG')
        url=urlsplit(video['lesson_url'])
        video['lesson_url']=urlunsplit((url.scheme,url.netloc,url.path,url.query,fragment[1:]))
        private_write(work/'manifest.json',{'videos':[video]})
        if renderer is None:
            from render_vocabulary import render
            renderer=render
        cache=root/'voice-cache';cache.mkdir(exist_ok=True)
        target=renderer(video,work,cache)
        movie=target/(video['id']+'.mp4')
        plan=prepare(movie,target/'upload-draft.json')
        private_write(work/'automated-checks.json',{'plan':plan,'check_type':'automated_private_preview',
                      'source_and_usage_verified':True,'renderer_decode_and_signal_checks_passed':True,
                      'human_audio_video_reviewed':False})
        emit('render_verified',job=job,voice=voice)
        if youtube is None:youtube=service(Path(config['token']))
        if media_factory is None:
            from googleapiclient.http import MediaFileUpload
            media_factory=MediaFileUpload
        video_id=upload(youtube,movie,plan,ledger,media_factory)
        state.update(state='uploaded_private',video_id=video_id)
        emit('uploaded_private',job=job,video_id=video_id)
    except ValueError as error:
        state.update(state='held',reason=str(error)[:250])
        emit('job_held',job=job,reason=state['reason'])
    except Exception as error:
        state.update(state='failed',reason=type(error).__name__)
        emit('job_failed',job=job,reason=type(error).__name__)
    private_write(state_path,state)
    return state


def poll(config, root):
    import boto3
    from botocore.config import Config
    s3=boto3.client('s3',region_name=config['region'],config=Config(
        connect_timeout=5,read_timeout=30,retries={'total_max_attempts':2}))
    activation=datetime.fromisoformat(config['activated_at'])
    objects=[]
    for page in s3.get_paginator('list_objects_v2').paginate(Bucket=config['bucket'],Prefix='shorts/drafts/'):
        objects.extend(o for o in page.get('Contents',[]) if o['LastModified']>=activation and o['Key'].endswith('.json'))
    for obj in sorted(objects,key=lambda x:x['LastModified']):
        if obj['Size']>200_000:
            emit('object_rejected',reason='BUNDLE_TOO_LARGE');continue
        with s3.get_object(Bucket=config['bucket'],Key=obj['Key'])['Body'] as body:
            bundle=json.loads(body.read(200001))
        job=job_id(bundle)
        if (root/job/'state.json').exists():continue
        if datetime.now(timezone.utc)-obj['LastModified']>timedelta(days=3):
            work=root/job;work.mkdir(parents=True,exist_ok=True)
            private_write(work/'state.json',{'state':'expired','reason':'MORE_THAN_3_DAYS_OLD'})
            continue
        return process_bundle(bundle,config,root)
    emit('queue_empty',objects=len(objects))
    return None


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,default=ROOT/'.youtube-secrets/worker.json')
    p.add_argument('--check',action='store_true',help='Check credentials and configuration, no search/render/upload')
    p.add_argument('--status',action='store_true',help='Read local job states only')
    args=p.parse_args();config=json.loads(args.config.read_text())
    root=Path(config['output']);root.mkdir(parents=True,exist_ok=True)
    if args.status:
        for path in sorted(root.glob('*/state.json')):
            print(path.read_text())
        return
    with (root/'worker.lock').open('w') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:emit('worker_busy');return
        if args.check:
            import boto3
            boto3.client('s3',region_name=config['region']).list_objects_v2(Bucket=config['bucket'],Prefix='shorts/drafts/',MaxKeys=1)
            verify_channel(service(Path(config['token'])))
            emit('preflight_ok',channel=CHANNEL)
        else:poll(config,root)


if __name__=='__main__':
    try:main()
    except Exception as error:
        emit('worker_failed',reason=type(error).__name__);sys.exit(1)
