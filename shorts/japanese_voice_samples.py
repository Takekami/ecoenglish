"""Generate two small paid Japanese voice auditions; never upload or publish.

Credentials are read locally at runtime and never printed. Only the original
non-sensitive audition script is sent to the existing OpenAI speech endpoint.
"""
import array
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import urllib.error
import urllib.request
import wave

MODEL = 'gpt-4o-mini-tts'
SCRIPT = (
    'インフレが鈍化したとき、物価は下がったのでしょうか。'
    '物価が下がったとは限りません。'
    '上昇率がプラスなら、物価は上がっています。'
    '上がるペースが緩やかになった、という意味です。'
)
INSTRUCTIONS = (
    '日本語を母語とする話者として、自然な標準日本語で話してください。'
    '落ち着いた、親しみやすい大人向けの学習動画です。'
    'ニュース速報や広告のように煽らず、穏やかに説明してください。'
    '一語ずつ区切る機械的な読み方を避け、意味のまとまりで滑らかに。'
    '自然な東京式アクセントと、日本語として自然な短い間を使ってください。'
    '少しテンポよく、ただし早口にはしないでください。'
    '入力された本文のみを読み上げ、言い換えや前置きは追加しないでください。'
)


def key_from_environment():
    key = os.environ.get('OPENAI_API_KEY')
    if key:
        return key
    env = Path(__file__).resolve().parents[1] / '.env'
    if env.exists():
        for line in env.read_text().splitlines():
            name, sep, value = line.partition('=')
            if sep and name.strip() in ('OPENAI_API_KEY', 'export OPENAI_API_KEY'):
                parts = shlex.split(value, comments=True)
                if len(parts) == 1:
                    return parts[0]
    raise RuntimeError('OpenAI API key is not configured locally.')


def generate(text, voice, path):
    """Generate one cached Japanese clip. Caller explicitly authorizes paid use."""
    output = path.parent
    payload = {'model': MODEL, 'voice': voice, 'input': text,
               'instructions': INSTRUCTIONS, 'response_format': 'wav'}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    receipt = path.with_suffix('.json')
    if path.exists() and receipt.exists():
        saved = json.loads(receipt.read_text())
        if saved.get('payload_sha256') == digest and saved.get('audio_sha256') == hashlib.sha256(path.read_bytes()).hexdigest():
            print(f'Reused cached speech: {path}', flush=True)
            return
    raw_path = output / f'{path.stem}-response.wav'
    pending = output / f'{path.stem}-pending.json'
    # No retries: avoid unintentionally duplicating paid generation.
    if raw_path.exists() and pending.exists() and json.loads(pending.read_text()).get('payload_sha256') == digest:
        audio = raw_path.read_bytes()
        request_id = json.loads(pending.read_text()).get('request_id')
    else:
        req = urllib.request.Request(
            'https://api.openai.com/v1/audio/speech',
            data=json.dumps(payload).encode(),
            headers={'Authorization': f'Bearer {key_from_environment()}',
                     'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                audio = response.read()
                request_id = response.headers.get('x-request-id')
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f'Speech request failed: HTTP {exc.code}; credentials and response body omitted.') from None
        except urllib.error.URLError:
            raise RuntimeError('Speech request could not connect; no automatic retry performed.') from None
    output.mkdir(parents=True, exist_ok=True)
    # Preserve a successful paid response before validation, so it can be repaired
    # locally if a streaming WAV uses an indefinite-length header.
    raw_path.write_bytes(audio)
    pending.write_text(json.dumps({'payload_sha256': digest, 'request_id': request_id}))
    with wave.open(io.BytesIO(audio)) as w:
        params = w.getparams()
        if w.getsampwidth() != 2:
            raise RuntimeError('Unexpected sample width.')
        pcm = w.readframes(w.getnframes())
        duration = len(pcm)/(w.getframerate()*w.getnchannels()*w.getsampwidth())
        samples = array.array('h', pcm)
    peak = max(map(abs, samples), default=0)
    if duration < 0.2 or duration > 60 or peak < 100:
        raise RuntimeError(f'Generated audition failed duration/signal validation: {duration:.2f}s, peak={peak}. Response saved locally.')
    with wave.open(str(path), 'wb') as w:
        w.setparams(params._replace(nframes=0))
        w.writeframes(pcm)
    receipt.write_text(json.dumps({
        'model': MODEL, 'voice': voice, 'synthetic_voice': True,
        'script': text, 'instructions': INSTRUCTIONS,
        'duration_seconds': duration, 'peak': peak,
        'payload_sha256': digest, 'audio_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'request_id': request_id, 'paid_api_request': True,
        'billed_amount': 'not returned by speech endpoint; consult provider usage',
        'uploaded': False,
    }, ensure_ascii=False, indent=2))
    print(f'{path}: {duration:.2f}s, voice={voice}', flush=True)


def audition(voice, output):
    generate(SCRIPT, voice, output / f'japanese-{voice}.wav')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=Path('output/shorts-voice-auditions'))
    p.add_argument('--generate-paid-samples', action='store_true')
    args = p.parse_args()
    if not args.generate_paid_samples:
        p.error('Use --generate-paid-samples explicitly to make the two billed API calls.')
    for voice in ('marin', 'cedar'):
        audition(voice, args.output.resolve())


if __name__ == '__main__':
    main()
