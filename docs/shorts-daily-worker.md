# Published lesson -> private Short (Mac worker)

2026-10-30. User approved this Mac as the renderer/uploader host. Public publishing
is not part of this chain. Existing English macOS Samantha is preserved;
Japanese Marin/Cedar alternate by the lesson's recorded publication date.

## Chain

1. The existing Podcast Lambda publishes audio, WordPress lesson and RSS. Only a
   valid verbatim Shorts selection approved separately by the independent reviewer
   is exported when `SHORTS_DRAFT_EXPORT=1`. S3 prefix: `shorts/drafts/` in the
   existing Podcast bucket. A failed draft export never retries the Podcast.
2. A per-user Mac LaunchAgent (`jp.econenglish.shorts-private-worker`) runs every
   15 minutes and at login. It reads only objects created since activation.
   One eligible job is processed per poll; a file lock prevents concurrent runs.
3. The worker fetches the matching PUBLIC WordPress lesson, checks publication
   time, independent-review status, the exact Script and source excerpt hashes.
   It does not substitute another lesson or Vocabulary practice examples.
4. Usage check: reuse an exact-expression reference catalog when available,
   otherwise discover candidate URLs using an actual OpenAI web-search call
   restricted to dictionaries and selected official company/issuer domains. URLs
   must be actual search source/citation records; output prose is not a URL source.
   If necessary, one further company-only search is allowed. Fetch up to four
   returned pages per search without following redirects/access workarounds.
   Require the exact expression in fetched article text or its official title.
   A second model checks contextual sense, Japanese translations, optional
   extension and reuse in at least two contexts. This is automated review, not
   a claim of human inspection or proof of usage frequency.
5. Generate with the existing renderer, reusing speech caches. It checks text
   fitting, PCM duration/signal and full FFmpeg decode. The description links to
   the same lesson, using its Script anchor where an expression card does not exist.
6. Recheck the MP4 hash/provenance and exact YouTube channel, then upload PRIVATE
   with subscriber notifications disabled and no `publishAt`. The persistent
   YouTube ledger prevents repeat uploads, including ambiguous network failures.
   An automated-check receipt explicitly says human audio/video review is false.

## Limits and recovery

- This Mac must be logged in, awake and connected. Missed intervals run after
  resumption; unprocessed source objects up to three days old can be caught up.
  Older objects are marked expired, not presented as today's news.
- No suitable selection, changed/unpublished Script, no live attestation or failed
  context review -> held. Rendering/API errors -> failed. Interrupted jobs remain
  started. These states DO NOT auto-retry paid generation or uncertain uploads.
  Inspect the local state and Studio before an explicit repair/reset.
- Source domains are deliberately limited. Many legitimate expressions will be
  held because an exact accessible reference cannot be found. Dictionary HTTP
  403 and search results without attestation were observed in preflight and held.
- Google OAuth is currently configured by the user; expiry/revocation can stop
  uploads and require reauthentication. Credentials remain local under ignored
  `.youtube-secrets/`; no OAuth token is sent to AWS, GitHub or a public webpage.
- No new cloud service or paid hosting is provisioned. Text/search/speech API
  calls plus ordinary S3 requests/storage are metered. Search is capped at two
  requests per candidate; successful clips and evidence are cached per job.
- Daily Podcast source selection may still skip. No lesson publication means no
  new Short job. The worker does not create fake source episodes to fill a day.

## Commands

```sh
.venv-youtube/bin/python shorts/daily_worker.py --check
.venv-youtube/bin/python shorts/daily_worker.py --status
.venv-youtube/bin/python shorts/daily_worker.py
.venv-youtube/bin/python shorts/install_worker.py --remove
```

Config: ignored `.youtube-secrets/worker.json`. Job states/manifests/evidence:
ignored `output/shorts-daily/`. Logs: `worker.log` and `worker-error.log` there.
Removing the agent preserves credentials, evidence and the duplicate ledger.
To stop incoming drafts, unset `SHORTS_DRAFT_EXPORT` on the existing Lambda,
preserving all other configuration. No schedule/YouTube public upload is enabled.

## Verification

Root offline tests cover the export boundary and its nonfatal failure handling.
Worker tests cover the source->usage->render->private-upload order, publication
provenance rejection, held jobs without paid rendering, repeated jobs with no
second upload, untrusted reference hosts and actual-page phrase requirements.
S3 list/read and YouTube channel authentication were checked using existing local
credentials. macOS Samantha produced an actual local clip. A live Nasdaq issuer
title and independent language review passed for `enter merger discussions`.
The actual search API also ran; inaccessible dictionary pages stopped safely.
No new lesson or video was fabricated as a production test. A real new uploaded
Short from this chain still depends on the next eligible published lesson.

Activation receipt: source export was set to `1` on the existing Lambda with its
revision ID and all other environment values preserved. The LaunchAgent is
registered in the logged-in user's GUI domain, interval 900 seconds; first run
exited 0 with `queue_empty` / zero new objects. Root tests: 37 passed; local Shorts
tests: 16 passed. Existing upload ledger and Google credentials were retained.

Official API reference checked:
https://developers.openai.com/api/docs/guides/tools-web-search
