"""Offline macOS preview renderer. Does not authenticate, upload or publish."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import wave

from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

W, H = 1080, 1920
BG, INK, TEAL = '#F5F3EC', '#142D39', '#14786D'
MUTED, LINE, WHITE = '#536771', '#D9E0D9', '#FFFFFF'
JP = '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc'
EN = '/System/Library/Fonts/Avenir Next.ttc'
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def font(size, english=False):
    return ImageFont.truetype(EN if english else JP, size)


def lines_for(draw, text, f, width):
    lines = []
    for para in text.split('\n'):
        words = para.split(' ') if re.fullmatch(r'[\x20-\x7e]+', para) else list(para)
        sep = ' ' if re.fullmatch(r'[\x20-\x7e]+', para) else ''
        line = ''
        for word in words:
            trial = line + (sep if line else '') + word
            if draw.textlength(trial, font=f) > width and line:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
    return lines


def text_box(draw, text, box, size, color=INK, english=False, minimum=26):
    x, y, width, height = box
    for actual in range(size, minimum - 1, -1):
        f = font(actual, english)
        lines = lines_for(draw, text, f, width)
        step = math.ceil(actual * 1.55)
        if len(lines) * step <= height and all(draw.textlength(s, font=f) <= width for s in lines):
            for i, line in enumerate(lines):
                draw.text((x, y + i * step), line, font=f, fill=color)
            return
    raise ValueError(f'Text cannot fit safe area: {text}')


def card(draw, text, y, label=None, selected=False):
    draw.rounded_rectangle((90, y, 920, y + 160), radius=24,
                           fill='#E1EDE6' if selected else WHITE,
                           outline=TEAL if selected else LINE, width=3)
    text_box(draw, label or '', (119, y + 42, 70, 85), 44, TEAL, True)
    text_box(draw, text, (210, y + 44, 675, 92), 44)


def frame(video, kind, index, total, countdown=None):
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 16), fill=TEAL)
    text_box(d, 'Econenglish', (90, 180, 820, 85), 54, english=True)
    text_box(d, '経済英語を、一問ずつ。', (90, 263, 830, 75), 32, MUTED)
    d.line((90, 364, 920, 364), fill=LINE, width=3)
    text_box(d, video['topic'], (90, 402, 830, 70), 32, TEAL, True)
    if kind == 'hook':
        text_box(d, video['hook'], (90, 570, 830, 470), 80)
        text_box(d, 'まずは英語を聞いてみよう。', (90, 1180, 830, 180), 42, MUTED)
    elif kind == 'listen':
        text_box(d, 'LISTEN', (90, 570, 830, 120), 76, TEAL, True)
        text_box(d, '音声を聞いてください', (90, 730, 830, 160), 56)
        for i in range(17):
            h = [48, 92, 140, 76, 180, 112, 60][i % 7]
            x = 110 + i * 46
            d.rounded_rectangle((x, 1080-h//2, x+16, 1080+h//2), radius=8, fill=TEAL)
        text_box(d, '英文は正解と一緒に表示します。', (90, 1320, 830, 120), 35, MUTED)
    elif kind in ('question', 'countdown'):
        text_box(d, video['question'], (90, 540, 830, 190), 58)
        for i, option in enumerate(video['options']):
            card(d, option, 850+i*200, chr(65+i))
        if countdown is not None:
            text_box(d, f'{countdown}', (90, 1320, 220, 150), 88, TEAL, True)
            text_box(d, '考える時間', (300, 1360, 600, 90), 36, MUTED)
    elif kind == 'answer':
        text_box(d, f'正解  {video["answer"]}', (90, 530, 830, 140), 70, TEAL)
        card(d, video['options'][ord(video['answer'])-65], 750, video['answer'], True)
        text_box(d, video['english'], (90, 1020, 830, 250), 57, english=True)
        text_box(d, video['translation'], (90, 1330, 830, 170), 39, MUTED)
    elif kind == 'explanation':
        text_box(d, 'ここがポイント', (90, 540, 830, 130), 57, TEAL)
        text_box(d, video['explanation'], (90, 780, 830, 550), 52)
        d.line((90, 1370, 920, 1370), fill=LINE, width=3)
        text_box(d, video['takeaway'], (90, 1420, 830, 110), 40)
    elif kind == 'repeat':
        text_box(d, 'もう一度、聞いてみよう。', (90, 540, 830, 160), 50, TEAL)
        text_box(d, video['english'], (90, 830, 830, 370), 64, english=True)
        text_box(d, video['translation'], (90, 1320, 830, 190), 42, MUTED)
    elif kind == 'end':
        text_box(d, '今日の一問、完了。', (90, 560, 830, 200), 65)
        text_box(d, '音声・クイズ付き無料教材', (90, 970, 830, 170), 46, TEAL)
        text_box(d, 'econenglish.jp', (90, 1160, 830, 150), 63, english=True)
        text_box(d, '出典の詳細は概要欄へ', (90, 1410, 830, 90), 34, MUTED)
    else:
        raise ValueError(kind)
    # Right-side controls and the bottom overlay stay outside this safe area.
    text_box(d, video['source_label'], (90, 1590, 830, 65), 28, MUTED)
    text_box(d, '練習用例文・実際の速報ではありません', (90, 1660, 830, 65), 27, MUTED)
    text_box(d, '合成音声使用  /  試作 2026.10.29', (90, 1725, 830, 60), 27, MUTED)
    d.rectangle((90, 1810, 920, 1817), fill=LINE)
    d.rectangle((90, 1810, 90+int(830*(index+1)/total), 1817), fill=TEAL)
    return im


def speech(text, lang, target):
    raw = target.with_suffix('.aiff')
    run(['say', '-v', 'Samantha' if lang == 'en' else 'Kyoko', '-r',
         '145' if lang == 'en' else '205', '-o', str(raw), text])
    run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(raw),
         '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le', str(target)])
    with wave.open(str(target), 'rb') as w:
        audio = w.readframes(w.getnframes())
    if len(audio) < 9600 or not any(audio):
        raise RuntimeError(f'Empty/silent speech from macOS: {target}. Check access to the local speech service.')
    return audio


def stamp(seconds):
    millis = round(seconds*1000)
    return f'{millis//3600000:02}:{millis//60000%60:02}:{millis//1000%60:02},{millis%1000:03}'


def read_pcm(path):
    with wave.open(str(path), 'rb') as w:
        if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (48000, 1, 2):
            raise ValueError(f'Expected 48kHz mono PCM16: {path}')
        pcm = w.readframes(w.getnframes())
    if len(pcm) < 9600 or not any(pcm):
        raise ValueError(f'Empty speech: {path}')
    return pcm


def render(video, root, japanese_provider='macos', english_source=None):
    target = root / video['id']
    target.mkdir(parents=True, exist_ok=True)
    scenes = [
        ('hook', video['hook_audio'], 'ja', 5, video['hook'], None),
        ('listen', video['english'], 'en', 4.5, '[英語音声：正解で英文を表示]', None),
        ('question', video['question'], 'ja', 2.5, video['question'], None),
        *[('countdown', '', 'ja', 1, str(n), n) for n in range(4, 0, -1)],
        ('answer', video['answer_audio'], 'ja', 5.5,
         f'正解 {video["answer"]} / {video["english"]}\n{video["translation"]}', None),
        ('explanation', video['explanation_audio'], 'ja', 9, video['explanation'], None),
        ('repeat_intro', 'では、もう一度聞いてみましょう。', 'ja', 2.5,
         'では、もう一度聞いてみましょう。', None),
        ('repeat', video['english'], 'en', 5, video['english'], None),
        ('end', 'ほかの問題も、無料の教材で試してみてください。', 'ja', 4.5,
         '音声・クイズ付き無料教材 econenglish.jp', None),
    ]
    concat, pcm, captions, timeline = [], bytearray(), [], []
    offset = 0.0
    for i, (kind, spoken, lang, minimum, caption, count) in enumerate(scenes):
        image = target / f'{i:02}-{kind}.png'
        frame(video, 'repeat' if kind == 'repeat_intro' else kind, i, len(scenes), count).save(image)
        wav = target/f'{i:02}-voice.wav'
        if not spoken:
            audio = b''
        elif lang == 'en' and english_source:
            original = english_source / video['id']
            source_timeline = json.loads((original/'timeline.json').read_text())
            matches = [(j, s) for j, s in enumerate(source_timeline)
                       if s['scene'] == kind and s['narration'] == spoken]
            if len(matches) != 1:
                raise ValueError('Original English text must match exactly before reusing audio.')
            source = original/f'{matches[0][0]:02}-voice.wav'
            audio = read_pcm(source)
            shutil.copyfile(source, wav)
        elif lang == 'ja' and japanese_provider == 'openai':
            from japanese_voice_samples import generate
            generated = target/f'{i:02}-japanese-generated.wav'
            generate(spoken, video['japanese_voice'], generated)
            run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(generated),
                 '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le', str(wav)])
            audio = read_pcm(wav)
        else:
            audio = speech(spoken, lang, wav)
        duration = max(minimum, len(audio)/96000 + 0.8)
        # Frame-quantized scene boundaries keep video and narration synchronized.
        duration = math.ceil(duration*30)/30
        lead = bytes(24000) if audio else b''  # 0.25s before speech
        pcm.extend(lead + audio + bytes(round(duration*48000)*2-len(lead)-len(audio)))
        concat.extend([f"file '{image.name}'", f'duration {duration:.9f}'])
        captions.append(f'{i+1}\n{stamp(offset)} --> {stamp(offset+duration)}\n{caption}\n')
        timeline.append({'scene': kind, 'start': round(offset, 3), 'duration': duration,
                         'narration': spoken, 'language': lang})
        offset += duration
    concat.append(f"file '{image.name}'")
    (target/'frames.txt').write_text('\n'.join(concat)+'\n')
    # Storyboard text is not a verbatim accessibility transcript and is not uploaded.
    (target/'storyboard.srt').write_text('\n'.join(captions))
    (target/'timeline.json').write_text(json.dumps(timeline, ensure_ascii=False, indent=2))
    with wave.open(str(target/'narration.wav'), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(48000)
        w.writeframes(pcm)
    movie = target / f'{video["id"]}.mp4'
    run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0',
         '-i', str(target/'frames.txt'), '-i', str(target/'narration.wav'),
         '-vf', 'fps=30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '22',
         '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
         '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-t', str(offset),
         '-movflags', '+faststart', str(movie)])
    # Decode the complete encoded video/audio rather than only checking existence.
    run([FFMPEG, '-v', 'error', '-i', str(movie), '-f', 'null', '-'])
    metadata = {
        'title': video['title'], 'privacyStatus': 'private',
        'description': f'{video["title"]}\n\n経済英語の練習用例文です。実際の速報・統計値・政策決定を伝える動画ではありません。\n合成音声使用。\n\n概念の参考資料（原文・画像・音声の転載ではありません）：\n{video["source_url"]}\n\n無料教材：\n{video["lesson_url"]}\n\n#経済英語 #英語リスニング #Shorts',
        'upload_performed': False,
        'source_reviewed_on': '2026-10-29',
        'duration_seconds': offset,
        'sha256': hashlib.sha256(movie.read_bytes()).hexdigest(),
        'voices': {'ja': (f'OpenAI gpt-4o-mini-tts / {video["japanese_voice"]}'
                          if japanese_provider == 'openai' else 'macOS Kyoko'),
                   'en': 'macOS Samantha'},
        'english_audio_reused': bool(english_source),
    }
    (target/'upload-draft.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
    print(f'{movie}: {offset:.2f}s', flush=True)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('output/shorts-pilots'))
    parser.add_argument('--japanese-provider', choices=['macos', 'openai'], default='macos')
    parser.add_argument('--allow-paid-speech', action='store_true')
    parser.add_argument('--reuse-english-from', type=Path)
    args = parser.parse_args()
    if args.japanese_provider == 'openai' and not args.allow_paid_speech:
        parser.error('OpenAI speech requires --allow-paid-speech explicitly.')
    if args.reuse_english_from and args.output.resolve() == args.reuse_english_from.resolve():
        parser.error('Use a separate output directory to preserve the original audio.')
    if (args.japanese_provider == 'macos' or not args.reuse_english_from) and not shutil.which('say'):
        raise SystemExit('This local preview renderer requires macOS say.')
    data = json.loads(Path(__file__).with_name('pilots.json').read_text())
    paths = [render(video, args.output.resolve(), args.japanese_provider,
                    args.reuse_english_from.resolve() if args.reuse_english_from else None)
             for video in data['videos']]
    sheet = Image.new('RGB', (1080, 1920), BG)
    for row, kind in enumerate(['hook', 'question', 'answer']):
        for col, path in enumerate(paths):
            image = next(path.glob(f'*-{kind}.png'))
            with Image.open(image) as im:
                sheet.paste(im.resize((360, 640)), (col*360, row*640))
    sheet.save(args.output/'contact-sheet.jpg', quality=92)


if __name__ == '__main__':
    main()
