# Econenglish Shorts: local pilot

The daily Mac chain is now in `daily_worker.py`: published source bundle,
live primary-source usage check, rendering, then private upload. See
[daily worker operation](../docs/shorts-daily-worker.md) for activation and limits.

YouTube uploader is now implemented separately in `youtube_upload.py`.
It defaults to reviewed **private** uploads, verifies the Econenglish channel,
and prevents duplicate/ambiguous insert retries using SQLite. OAuth and a live
upload have not been completed; no scheduler is enabled. See
[setup and commands](../docs/youtube-upload-setup.md). Historical pilot notes
below describe the earlier preview stages.

**Latest source policy (v6): use the actual Podcast script.**
The current difficulty/CTA preview is v7 under `output/shorts-podcast-v7/`:
`enter merger discussions`, with a blog-first continuation. See the
[operating plan](../docs/shorts-operating-plan.md) for the proposed Japan 19:00
release time (not scheduled). Source provenance and the explicit application
stage are retained. Bare basic-word candidates are no longer accepted.
Run `from_podcast.py` on a reviewed excerpt bundle, then pass its output with
`--manifest` to the renderer. See
[Podcast source workflow](../docs/shorts-podcast-source.md). The normal rendering
path now rejects invented standalone example manifests. Historical v1–v5 examples
below are preserved for comparison and require `--allow-original-examples` to
regenerate. The same-expression rule and explicit language-application stage
remain in place. A source-backed sample is in `output/shorts-podcast-v6/`.

**Current direction: consistent example, then explicit application (v5).** Use `render_vocabulary.py` and
`vocabulary-pilots.json` for the latest previews. The earlier sections describe
the preserved economics-comprehension experiments, not the current format.

```sh
python shorts/render_vocabulary.py --allow-paid-speech
```

Current output is `output/shorts-vocabulary-v5/`. It introduces a familiar
Japanese economic term, offers one English expression, plays an original short
example containing that same expression, translates it, introduces a clearly
labeled application (verb form or collocation), and replays the original example. It does not
explain monetary policy, prices, market consequences, or economic mechanisms.
Marin / Cedar / Marin are assigned per video; English remains macOS Samantha,
with new word and example recordings to match the new teaching content.
The introduction is framed as one possible way to say it, without marking other
valid expressions wrong. Additional knowledge remains in an explicitly labeled
application scene after the original example and translation; it does not replace
the first expression inside that example.
`scenes_for` rejects an example which does not contain the full introduced
expression, ignoring sentence capitalization. For instance, introducing
`a rate cut` requires an example such as `The central bank announced a rate cut.`;
an example using only `cut interest rates` is rejected before speech generation.
The target expression is also repeated above the example on screen.
The application scene says, for example, `応用：動詞で言うなら`, retains the
original noun phrase as a reference, and introduces `cut interest rates` with a
Japanese spoken transition. The original `a rate cut` example remains intact.
This command explicitly enables billed Japanese speech. English generation is
local. Identical audio is cached within the run and for subsequent runs. Earlier
versions and their videos are preserved; the production pipeline is unchanged.
Use `--audio-cache output/shorts-vocabulary-v3/voice-cache` to reuse unchanged
audio from the preceding preview. Regression checks:
`python -m unittest discover -s shorts -p 'test_*.py'`.

See [editorial policy](editorial-policy.md) for the agreed educational scope.

Three original economic-English exercises, reviewed 2026-10-29. This directory is
separate from the daily production Lambda. It does **not** authenticate to Google,
upload to YouTube, modify the channel, or enable scheduled publishing.

## Deliverables

Run from the repository root on macOS:

```sh
python -m pip install -r shorts/requirements-preview.txt
python shorts/render_previews.py
```

The installed macOS voices `Kyoko` (Japanese) and `Samantha` (English) are needed.
The speech service must be accessible; the renderer rejects empty audio rather
than silently producing a silent video. No external speech API or generation
service is called. FFmpeg is supplied by the pinned `imageio-ffmpeg` package.
Fonts are the local Hiragino Kaku Gothic W6 and Avenir Next fonts.

Files are generated under ignored `output/shorts-pilots/`:

- `01-inflation/01-inflation.mp4`: positive inflation slowing vs prices falling.
- `02-rate-cut/02-rate-cut.mp4`: an interest-rate cut vs a rate rise.
- `03-export-growth/03-export-growth.mp4`: exports rising vs slower growth.
- `contact-sheet.jpg`: opening, question, answer for all three videos.
- Each video's folder also contains source frames, local narration, a timed
  storyboard, timeline, and an **unsubmitted** upload metadata draft.

Videos are 1080×1920 H.264/AAC, 30 fps. Speech determines minimum scene length;
4 seconds are reserved for answering. All speech is generated locally. No
existing broadcast or podcast recording is reused. There is no background music.
`storyboard.srt` is a scene-text review aid, **not** a verbatim accessibility
caption track. A production uploader would need a separate caption workflow.

## Editorial review

`pilots.json` is the inspectable script and answer source. The examples are
fictional exercises, not current news claims. Numbers in the inflation example
are invented and explicitly labeled as exercises. Existing lesson themes helped
choose the topics, but older lesson facts/audio were not treated as verified
current news. The export pilot links to the lesson library rather than promoting
the older source lesson as current reporting.

The following primary references were checked on 2026-10-29:

1. [ONS: inflation](https://www.ons.gov.uk/aboutus/usingpublicdatatoproducestatistics/learningaboutdata/learnmoreaboutwhoweareandwhatwedo/whatisinflationandhowdowecalculateit):
   distinguishes lower inflation from falling prices.
2. [Bank of England: interest rates](https://www.bankofengland.co.uk/explainers/what-are-interest-rates):
   explains interest rates and central-bank policy rates. No current rate or
   actual policy decision is reproduced in the exercise.
3. [BEA: trade in goods and services](https://www.bea.gov/data/intl-trade-investment/international-trade-goods-and-services):
   used only as a reference for the exports concept. It is not attributed as
   the source of the fictional English example or a current export-growth claim.

The references are not sponsors, endorsers, or sources of reused media.
In-video labels identify the concept reference, exercise status, synthetic voice
and preview date. Full links are included in the unsubmitted description draft.
The graphics and wording avoid alarmist headlines, investment recommendations,
score guarantees, or invented personal experience.

## Validation and publication boundary

- All text boxes must fit the reserved area or generation fails.
- Synthesized speech must contain nonzero audio or generation fails.
- The complete encoded output is decoded by FFmpeg; decode failure stops the run.
- Inspect the contact sheet and encoded-video frames; confirm the correct option
  against the script. Listen to the preview before authorizing public posting.
- These checks do not constitute independent fact-checking of future generated
  news. Automatic generation from daily news and semantic review are not built.
- Metadata drafts explicitly specify `private`; no upload has been performed.

Before automated public posting, connect the intended Google/YouTube identity,
verify the uploaded channel ID, test a private upload, and implement durable
duplicate prevention, credentials storage, publication controls, and failure
reporting. API requirements must be checked at that time. Profile links must be
set up separately; Shorts description URLs should not be treated as clickable.

This pilot adds no recurring cloud resources or paid API calls. Future rendering,
hosting, and posting infrastructure costs have not been estimated or enabled.

## Japanese voice auditions (follow-up)

The user found the macOS Japanese voice unnatural and requested natural Japanese
narration as well as English. The original three local videos remain unchanged
for comparison. `japanese_voice_samples.py` makes **two paid OpenAI speech calls**
only when invoked with `--generate-paid-samples`; it is not part of the default
renderer or any scheduled task. Thus the no-paid-call statement above applies
only to the original local pilot rendering, not these later voice auditions.

The auditions use `gpt-4o-mini-tts` voices `marin` and `cedar`, the same Japanese
exercise text, and instructions for natural standard-Japanese educational speech.
The English audio is not regenerated. Payload-hash caching avoids paying again
for an identical completed sample. There are no automatic network retries.
API errors omit credentials and response bodies. Credentials are loaded locally
at runtime, never written to output receipts. The generated WAV and receipt stay
under ignored `output/shorts-voice-auditions/`. The actual billed amount is not
returned by the speech endpoint; do not claim a measured cost from duration alone.

Official guide consulted 2026-10-29:
https://developers.openai.com/api/docs/guides/text-to-speech

These are voice-selection samples; the final Japanese voice and its subjective
naturalness need user listening feedback before replacing all three videos.

The initial audition session made **three** paid speech requests in total: the
first Marin response hit a local WAV-header validation problem and was not
retained; the second Marin response was preserved and repaired locally; Cedar
completed on its first request. Streaming WAV headers can advertise indefinite
length, so duration is calculated from actual PCM bytes and a standard WAV header
is rewritten with the correct frame count. Successful raw responses are now
preserved with a payload-hash sidecar before normalization. Re-running the same
auditions reuses completed/cached responses. Final audible sample durations:
Marin 15.20s, Cedar 17.85s. Signal checks confirm nonzero PCM in both files; voice
preference and naturalness remain for the user to judge by listening.

## Conversational scripts and alternating voices (v2)

The user approved both audition voices, alternating by video while keeping one
Japanese voice throughout each video. `pilots.json` v2 assigns Marin / Cedar /
Marin and rewrites spoken Japanese as conversational narration. Concise on-screen
text and the spoken script are separate; artificial katakana readings of English
vocabulary were removed. English examples and answers have not changed.

```sh
python shorts/render_previews.py \
  --output output/shorts-pilots-v2 \
  --japanese-provider openai --allow-paid-speech \
  --reuse-english-from output/shorts-pilots
```

This opt-in path makes paid speech requests for Japanese only, uses the approved
audition model/style instructions, and caches each generated clip with a payload
hash. Re-rendering an unchanged clip does not make another generation request.
The default renderer still uses local macOS voices and does not call an API.
The original MP4s remain available for comparison. English WAVs are copied from
their corresponding original listen/repeat scenes after exact script matching;
they are not regenerated. An added Japanese transition introduces the replay.
All durations are recalculated from the resulting audio, so speech is not cut
off to force the original runtime. No scheduled generation or YouTube upload is
enabled. Daily deterministic alternation is a future scheduling concern; this
pilot alternates by the order of the three videos.
