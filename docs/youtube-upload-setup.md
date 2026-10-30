# YouTube Shorts upload setup

2026-10-30: OAuth/channel verification and a private test upload succeeded;
the [daily Mac private-preview worker](shorts-daily-worker.md) is now active.
The initial setup notes below are retained for reauthentication/manual operation.

Implemented 2026-10-29. No Google project, OAuth grant, upload or daily schedule
has been created by this implementation. The initial flow uploads **private**
videos for human inspection. Rendering stays on macOS (the current English voice
depends on macOS); this is not a Lambda deployment.

## One-time Google setup

1. In Google Cloud Console, select/create an Econenglish project. Enable
   **YouTube Data API v3** in APIs & Services → Library.
2. Configure Google Auth Platform branding/audience. If External/Testing, add
   your Google account as a test user. Testing grants can expire; resolve the
   appropriate production/verification configuration before unattended use.
3. Create an OAuth client with application type **Desktop app**. Download its
   JSON to `.youtube-secrets/client.json` in this repository. Do not paste its
   contents in chat or commit it. No service account or API key replaces the
   channel owner's OAuth authorization.
4. Install the isolated uploader dependencies and authenticate:

```sh
python3 -m venv .venv-youtube
.venv-youtube/bin/pip install -r shorts/requirements-youtube.txt
.venv-youtube/bin/python shorts/youtube_upload.py auth --client .youtube-secrets/client.json
```

The system browser opens Google's consent screen. Choose the account/brand
channel for Econenglish. Requested scopes: video upload and read-only YouTube
access (needed to verify channel/video identity). OAuth callback binds to a
loopback address. Refresh credentials are saved mode 0600, with no secrets printed.
Expected channel: `UC4UkE1AqN_XWkyW3LqChlyQ`. A mismatch stops upload.

## Each reviewed rendered video

Use the source-backed renderer described in `shorts-podcast-source.md` first.
Its `upload-draft.json` must contain the externally verified usage evidence and
the rendered video's SHA-256. Old drafts without that evidence must be regenerated
from their reviewed manifest; do not bypass the checks.

```sh
.venv-youtube/bin/python shorts/youtube_upload.py prepare \
  --video output/VIDEO/VIDEO.mp4 --draft output/VIDEO/upload-draft.json \
  --review output/VIDEO/youtube-review.json
```

Watch/listen to the actual MP4, inspect the title, description, lesson link and
source date in the review file. Confirm the matching Podcast/blog are live and
the expression section exists. Change `approved` and `audio_and_video_checked`
to true in that file. They attest human review; the tool does not infer audio or
semantic quality. Any subsequent video or metadata change invalidates the review.

```sh
.venv-youtube/bin/python shorts/youtube_upload.py upload \
  --video output/VIDEO/VIDEO.mp4 --draft output/VIDEO/upload-draft.json \
  --review output/VIDEO/youtube-review.json
```

The uploader reuses refresh credentials, checks source/usage provenance, checks
the exact channel, and uploads privately. It prints the video ID on success.
Open YouTube Studio and verify playback, captions/text, audience settings and
processing. Educational English for adult learners is marked not made for kids.
Synthetic voice is disclosed in the description; assess Studio's altered-content
setting for the actual video before public release.

## Explicit reservation for public release

After inspecting the private upload, this command reserves 19:00 JST:

```sh
.venv-youtube/bin/python shorts/youtube_upload.py schedule \
  --video-id VIDEO_ID --publish-at 2026-10-30T19:00:00+09:00 \
  --confirm-public-release
```

Past/naive timestamps, another channel's video, or an unprocessed/non-private
video are rejected. Confirm the reservation in Studio. API eligibility and account
restrictions can affect publication; no project-audit eligibility is assumed.

## Failure recovery and daily operation

`output/youtube/uploads.sqlite3` is the durable local ledger. Preserve it across
runs and backups. One episode or identical MP4 can be inserted only once, even
if a timeout leaves the result uncertain. This deliberately prefers a held video
to a duplicate. There are no automatic insert retries. For `pending` entries,
inspect Studio first; reconcile the remote video manually before changing state.
Do not delete the ledger to retry. For multiple machines, use a shared atomic
ledger before enabling workers; this SQLite ledger supports one persistent host.

No background scheduler has been enabled. Initially run the private-upload step
after each reviewed render. Once OAuth, one private upload, public scheduling,
profile navigation and the daily source/render path work, enable a daily worker
on a continuously available host with retained credentials and ledger. The worker
must hold ineligible/unreviewed days and report failures, not silently substitute
old lessons. This implementation does not make the existing paid speech renderer
or source-draft exporter run automatically.

Official references consulted:
- https://developers.google.com/youtube/data/guides/auth/installed-apps
- https://developers.google.com/youtube/data/reference/rest/v3/videos/insert
- https://developers.google.com/youtube/data/reference/rest/v3/videos
