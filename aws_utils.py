# utils/aws_utils.py
import os
import uuid
import requests
from pathlib import Path

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_TTS_ENDPOINT = "https://api.openai.com/v1/audio/speech"

def synthesize_speech(text, filename, voice="shimmer", model="tts-1"):
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

    response = requests.post(OPENAI_TTS_ENDPOINT, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(f"TTS failed: {response.status_code} - {response.text}")

    audio_path = f"/tmp/{filename}"
    with open(audio_path, "wb") as f:
        f.write(response.content)

    return audio_path

import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")

def upload_to_s3(file_path, bucket_name, folder="audio"):
    s3_key = f"{folder}/{uuid.uuid4().hex}_{Path(file_path).name}"
    try:
        s3.upload_file(
            file_path,
            bucket_name,
            s3_key,
            ExtraArgs={"ContentType": "audio/mpeg"}
        )
    except ClientError as e:
        print("S3 upload failed:", e)
        return None

    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
    return s3_url