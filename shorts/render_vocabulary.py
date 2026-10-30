"""One expression -> consistent example -> clearly labeled language extension.

Explicitly opt in to paid Japanese speech. No upload or publishing capability.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import shutil
import sys
import wave

from PIL import Image, ImageDraw

from japanese_voice_samples import generate
from render_previews import (
    W, H, BG, INK, TEAL, MUTED, LINE, WHITE, FFMPEG,
    text_box, speech, read_pcm, run, stamp,
)


def draw_frame(v, kind, step, total, count=None):
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 16), fill=TEAL)
    text_box(d, 'Econenglish', (90, 180, 820, 85), 54, english=True)
    text_box(d, '知っている経済用語を、使える英語に。', (90, 263, 830, 80), 32, MUTED)
    d.line((90, 364, 920, 364), fill=LINE, width=3)
    # Do not reveal the English answer in a topic label before the word reveal.
    text_box(d, '今日の経済英語', (90, 402, 830, 70), 32, TEAL)
    if kind == 'hook':
        text_box(d, f'「{v["japanese_term"]}」', (90, 650, 830, 220), 92)
        text_box(d, '今日は、こんな言い方を。', (90, 930, 830, 220), 57, TEAL)
        text_box(d, '使える表現を、一つずつ。', (90, 1230, 830, 130), 38, MUTED)
    elif kind == 'term':
        text_box(d, v['japanese_term'], (90, 560, 830, 140), 52, MUTED)
        text_box(d, v['english_term'], (90, 790, 830, 350), 96, TEAL, True)
        text_box(d, '言い方の一つです。声に出してみよう。', (90, 1300, 830, 170), 38, MUTED)
    elif kind in ('example_intro', 'example', 'translation', 'replay_intro', 'replay'):
        replay = kind in ('replay_intro', 'replay')
        text_box(d, 'もう一度、聞いてみよう。' if replay else '文の中で聞いてみよう。',
                 (90, 540, 830, 170), 48, TEAL)
        text_box(d, '今日の表現：'+v['english_term'], (90, 720, 830, 95), 36, TEAL)
        text_box(d, v['english_example'], (90, 830, 830, 360), 70, english=True)
        if kind in ('translation', 'replay_intro', 'replay'):
            text_box(d, v['translation'], (90, 1300, 830, 190), 43, MUTED)
    elif kind in ('extension_intro', 'extension'):
        extension = v['extension']
        text_box(d, extension['label'], (90, 540, 830, 170), 48, TEAL)
        text_box(d, '基本の表現：'+v['english_term'], (90, 720, 830, 95), 35, MUTED)
        text_box(d, extension['japanese'], (90, 900, 830, 190), 60)
        if kind == 'extension':
            text_box(d, extension['english'], (90, 1130, 830, 220), 72, TEAL, True)
            text_box(d, extension['note'], (90, 1400, 830, 150), 34, MUTED)
    elif kind == 'end':
        text_box(d, v['english_term'], (90, 590, 830, 280), 85, TEAL, True)
        text_box(d, v['japanese_term'], (90, 920, 830, 150), 55)
        text_box(d, '続きの音声・英文・クイズは教材ページへ', (90, 1220, 830, 140), 36, MUTED)
        text_box(d, 'econenglish.jp', (90, 1380, 830, 130), 60, english=True)
    else:
        raise ValueError(kind)
    text_box(d, v['source_label'], (90, 1590, 830, 65), 28, MUTED)
    disclosure = ('Podcast教材の一文を、そのまま使用'
                  if v.get('example_origin') == 'podcast_script' else 'オリジナルの練習用例文です')
    text_box(d, disclosure, (90, 1660, 830, 65), 27, MUTED)
    text_box(d, '合成音声使用', (90, 1725, 830, 60), 27, MUTED)
    d.rectangle((90, 1810, 920, 1817), fill=LINE)
    d.rectangle((90, 1810, 90+int(830*(step+1)/total), 1817), fill=TEAL)
    return im


def scenes_for(v):
    # Validate before a billed speech request or rendering write.
    if v.get('example_origin') == 'podcast_script':
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from shorts_source import validate_provenance, validate_usage_review
        bundle = v.get('podcast_provenance', {})
        selection = bundle.get('selection', {})
        if (not validate_provenance(selection, bundle.get('script', ''))
                or not validate_usage_review(selection, bundle.get('usage_review'))
                or v['english_example'] != selection.get('sentence')
                or v['english_term'] != selection.get('expression')
                or v['translation'] != selection.get('sentence_ja')
                or v['japanese_term'] != selection.get('meaning_ja')):
            raise ValueError('Shorts text differs from the verified Podcast excerpt')
    pattern = r'(?<!\w)'+re.escape(v['english_term'].casefold())+r'(?!\w)'
    if not re.search(pattern, v['english_example'].casefold()):
        raise ValueError(f'Example must use the introduced expression unchanged: {v["id"]}')
    extension = v.get('extension')
    extra = [
        ('extension_intro', extension['intro'], 'ja', 3, None),
        ('extension', extension['english']+'.', 'en', 3.5, None),
    ] if extension else []
    return [
        ('hook', v['hook_audio'], 'ja', 3, None),
        ('term', v['english_term']+'.', 'en', 2.8, None),
        ('example_intro', 'この表現を、文の中で聞いてみましょう。', 'ja', 2, None),
        ('example', v['english_example'], 'en', 3.5, None),
        ('translation', v['translation_audio'], 'ja', 3, None),
        *extra,
        ('replay_intro', 'では、もう一度聞いてみましょう。', 'ja', 2.5, None),
        ('replay', v['english_example'], 'en', 3.5, None),
        ('end', 'この回の音声と英文は、無料の教材ページで確認できます。', 'ja', 4, None),
    ]


def audio_for(text, lang, voice, cache):
    digest = hashlib.sha256((lang+'|'+voice+'|'+text).encode()).hexdigest()
    path = cache/f'{digest}.wav'
    if lang == 'ja':
        original = cache/f'{digest}-openai.wav'
        generate(text, voice, original)
        run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(original),
             '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le', str(path)])
    elif not path.exists():
        speech(text, 'en', path)
    return path, read_pcm(path)


def render(v, root, cache):
    target = root/v['id']
    target.mkdir(parents=True, exist_ok=True)
    scenes = scenes_for(v)
    pcm, concat, timeline = bytearray(), [], []
    offset = 0
    for i, (kind, text, lang, minimum, count) in enumerate(scenes):
        image = target/f'{i:02}-{kind}.png'
        draw_frame(v, kind, i, len(scenes), count).save(image)
        clip_duration = 0
        if text:
            source, clip = audio_for(text, lang, v['japanese_voice'] if lang == 'ja' else 'Samantha', cache)
            shutil.copyfile(source, target/f'{i:02}-voice.wav')
            clip_duration = len(clip)/96000
        else:
            clip = b''
        duration = math.ceil(max(minimum, clip_duration+.65)*30)/30
        lead = bytes(19200) if clip else b''
        pcm.extend(lead+clip+bytes(round(duration*48000)*2-len(lead)-len(clip)))
        concat.extend([f"file '{image.name}'", f'duration {duration:.9f}'])
        timeline.append({'scene':kind, 'start':round(offset, 3), 'duration':duration,
                         'narration':text, 'language':lang,
                         'voice':(v['japanese_voice'] if lang=='ja' else 'Samantha') if text else None})
        offset += duration
    concat.append(f"file '{image.name}'")
    (target/'frames.txt').write_text('\n'.join(concat)+'\n')
    (target/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2))
    with wave.open(str(target/'narration.wav'),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000); w.writeframes(pcm)
    movie = target/f'{v["id"]}.mp4'
    run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0',
         '-i', str(target/'frames.txt'), '-i', str(target/'narration.wav'), '-vf', 'fps=30',
         '-c:v', 'libx264', '-preset', 'fast', '-crf', '22', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '160k', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
         '-t', str(offset), '-movflags', '+faststart', str(movie)])
    run([FFMPEG,'-v','error','-i',str(movie),'-f','null','-'])
    extension_description = (f'\n\n応用（最初の例文とは別の学習段階）：\n{v["extension"]["japanese"]} → {v["extension"]["english"]}'
                             if v.get('extension') else '')
    example_description = (f'Podcast教材のスクリプトから、英文を変更せずに使用しています。\n教材公開日：{v["podcast_provenance"]["published_at"][:10]}。最新ニュースとしての再配信ではありません。'
                           if v.get('example_origin') == 'podcast_script' else 'オリジナルの練習用例文です。実際の速報ではありません。')
    usage_refs = v.get('podcast_provenance', {}).get('usage_review', {}).get('references', [])
    usage_description = '\n表現の用例確認（ニュースの出典とは別）：\n' + '\n'.join(r['url'] for r in usage_refs) if usage_refs else ''
    (target/'upload-draft.json').write_text(json.dumps({
        'title':v['title'], 'privacyStatus':'private', 'upload_performed':False,
        'description':f'{v["japanese_term"]}の言い方の一つとして、今回はこちらを練習します。\n{v["english_term"]}\n紹介した表現をそのまま使った例文：{v["english_example"]}\n{v["translation"]}{extension_description}\n\n{example_description}\n合成音声使用。\n元の教材・参考：\n{v["source_url"]}\n無料教材：\n{v["lesson_url"]}{usage_description}\n#経済英語 #英語学習 #Shorts',
        'duration_seconds':offset,'format':'japanese_to_english_vocabulary',
        'japanese_voice':v['japanese_voice'],'english_voice':'macOS Samantha',
        'example_origin':v.get('example_origin', 'original_exercise'),
        'podcast_provenance':v.get('podcast_provenance'),
        'sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),
    },ensure_ascii=False,indent=2))
    print(f'{movie}: {offset:.2f}s',flush=True)
    return target


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=Path('output/shorts-vocabulary-v5'))
    p.add_argument('--audio-cache', type=Path)
    p.add_argument('--manifest', type=Path)
    p.add_argument('--allow-original-examples', action='store_true')
    p.add_argument('--allow-paid-speech', action='store_true')
    args = p.parse_args()
    if not args.allow_paid_speech:
        p.error('--allow-paid-speech is required for Japanese voice generation.')
    manifest = args.manifest or Path(__file__).with_name('vocabulary-pilots.json')
    data = json.loads(manifest.read_text())
    if not args.allow_original_examples and any(v.get('example_origin') != 'podcast_script' for v in data['videos']):
        p.error('Use a Podcast-derived --manifest. Archived invented examples require --allow-original-examples.')
    for v in data['videos']:
        scenes_for(v)
    root = args.output.resolve(); root.mkdir(parents=True,exist_ok=True)
    cache = args.audio_cache.resolve() if args.audio_cache else root/'voice-cache'
    cache.mkdir(parents=True,exist_ok=True)
    paths = [render(v,root,cache) for v in data['videos']]
    sheet = Image.new('RGB',(360*len(paths),1920),BG)
    for row, kind in enumerate(('hook','term','translation')):
        for col,path in enumerate(paths):
            with Image.open(next(path.glob(f'*-{kind}.png'))) as im:
                sheet.paste(im.resize((360,640)),(col*360,row*640))
    sheet.save(root/'contact-sheet.jpg',quality=92)
    review=['# 経済用語を英語にする Shorts 台本','経済の仕組みの解説は行わず、用語・用例・英語の使い方に絞る。','']
    for v in data['videos']:
        review.extend(['## '+v['title'],'日本語の声：'+v['japanese_voice'],''])
        review.extend(f'**{kind}**  {text}\n' for kind,text,lang,minimum,count in scenes_for(v) if text)
    (root/'scripts-ja.md').write_text('\n'.join(review))


if __name__=='__main__':
    main()
