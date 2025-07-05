import os, mimetypes, requests
from pathlib import Path
import boto3

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_TTS_ENDPOINT = "https://api.openai.com/v1/audio/speech"

auth = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type":"application/json"}
_s3 = boto3.client("s3")

def synthesize_speech(text, filename, voice="shimmer", model="tts-1"):
    data = {"model": model, "input": text, "voice": voice, "response_format": "mp3"}
    r = requests.post(OPENAI_TTS_ENDPOINT, headers=auth, json=data)
    r.raise_for_status()
    path = f"/tmp/{filename}"
    Path(path).write_bytes(r.content)
    return path

def upload_to_s3(local_path:str, bucket:str, folder:str|None=None):
    key = f"{folder}/{Path(local_path).name}" if folder else Path(local_path).name
    _s3.upload_file(local_path, bucket, key, ExtraArgs={"ContentType": mimetypes.guess_type(local_path)[0] or "application/octet-stream"})
    return _s3.generate_presigned_url(
    "get_object",
    Params={"Bucket": bucket, "Key": key},
    ExpiresIn=60*60*6
)