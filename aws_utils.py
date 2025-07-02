# aws_utils.py
import os, uuid, mimetypes, requests, boto3
from pathlib import Path
from botocore.exceptions import ClientError

# ---------- OpenAI ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing")

OPENAI_TTS_ENDPOINT = "https://api.openai.com/v1/audio/speech"

# ---------- AWS ----------
s3 = boto3.client("s3")

# ---------- TTS ----------
def synthesize_speech(text: str, filename: str,
                      voice: str = "shimmer", model: str = "tts-1") -> str:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "input": text,
        "voice": voice,
        "response_format": "mp3"
    }
    res = requests.post(OPENAI_TTS_ENDPOINT, headers=headers, json=data, timeout=60)
    if res.status_code != 200:
        raise RuntimeError(f"TTS failed {res.status_code}: {res.text}")

    out_path = Path("/tmp") / filename
    out_path.write_bytes(res.content)
    return str(out_path)

# ---------- S3 ----------
def upload_to_s3(local_path: str, bucket: str, folder: str | None = None,
                 expires: int = 60 * 60 * 24 * 7) -> str:
    key = f"{folder.rstrip('/')}/{Path(local_path).name}" if folder else Path(local_path).name
    content_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"

    s3.upload_file(local_path, bucket, key, ExtraArgs={"ContentType": content_type})

    # presigned URL
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires
    )
