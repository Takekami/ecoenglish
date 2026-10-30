# Shorts sourced from the Podcast script

**2026-10-30 update:** reviewed S3 draft export is now enabled on the existing
Lambda and a Mac worker runs every 15 minutes. It verifies live usage, renders
and uploads private previews. See [active worker](shorts-daily-worker.md).
The preview implementation history below predates that activation.

Implemented locally 2026-10-29. **Not deployed or enabled in AWS. No YouTube upload.**

Current expression rubric and proposed release/CTA strategy are documented in
[the operating plan](shorts-operating-plan.md). Selections now require 2–6 words;
the generator and reviewer prioritize reusable intermediate-level collocations
over bare common nouns or rare jargon. The minimum length is a mechanical gate,
not a sufficient measure of difficulty.

## Source of truth

The Podcast audio and WordPress script already receive the same `sections["Script"]`
in `main.py`. Shorts now select a useful expression and one complete sentence from
that exact string. Vocabulary example sentences are not a source: they may be
independent invented practice examples.

The generation prompt adds an optional JSON `Shorts Candidate` section in the
existing lesson-generation response. It contains an expression, its contextual
Japanese meaning, a verbatim sentence and its Japanese translation, plus an
optional explicitly introduced language application. No extra generation request
is added. Additional prompt/output tokens still have their usual cost.

`shorts_source.py` checks exact substring matching, expression boundaries,
sentence boundaries, length and Japanese fields. It records the full script's
SHA-256 and character offsets for both the sentence and the expression. It copies
the expression's actual surface form, retaining articles/plurals/verb forms.
Changing the source script, example or target after selection invalidates the
rendering input. These mechanical checks establish provenance, not factual truth
or translation quality.

The existing independent lesson review now returns a separate boolean
`shorts_accurate`, covering sentence completeness, contextual meaning, Japanese
translation, tense, negation, uncertainty and any extension. False/missing/string
values reject only the Shorts selection; the core lesson's five review checks
continue separately. An unsuitable day produces no Shorts draft rather than a
newly invented example. The source lesson itself still needs its ordinary source
and publication gates.

## Optional production draft export

After Podcast, WordPress and RSS publication, `SHORTS_DRAFT_EXPORT=1` permits a
reviewed selection to be saved in the existing S3 bucket under `shorts/drafts/`.
Default is **off**. The bundle includes the full source script, exact selection,
review status, episode ID, public lesson URL, article URL and recorded publication
time in Australia/Brisbane. A deterministic episode/script-hash filename keeps
different scripts distinct. A draft export failure is caught at this optional
boundary so it cannot fail an already published Podcast and encourage duplicate
episode retries. No renderer, paid Shorts speech or YouTube API is run in Lambda.
S3 storage/requests would have their ordinary cost if export is enabled.

This change has not been deployed. Activation requires deploying the code and
setting the explicit flag; neither was performed in this preview task. Rollback
of export is unsetting the flag. Existing publication idempotency limitations
outside this added boundary are unchanged.

## Local conversion and rendering

```sh
python shorts/from_podcast.py --bundle /path/to/draft.json \
  --usage-review /path/to/checked-usage.json \
  --output /path/to/manifest.json --voice marin
python shorts/render_vocabulary.py --manifest /path/to/manifest.json \
  --output output/shorts-podcast-preview --allow-paid-speech
```

The default renderer requires a Podcast-backed manifest; archived invented
examples require a deliberate `--allow-original-examples` override. It verifies
source hashes and offsets again before any paid speech call. Japanese speech is
the already approved OpenAI voice; English is the same macOS Samantha voice with
the selected sentence synthesized exactly. **Audio is not a timed cut from the
original episode recording.** Word-for-word text reuse and audio-clip extraction
are distinct capabilities; this implementation provides the former.

External usage is now a required, separate editorial stage. The draft exporter
marks new bundles `pending_primary_source_check`. Before conversion, provide a
record from actually reading a dictionary or issuer announcement, including a
short attesting excerpt, date and at least two reuse contexts. The record is tied
to the expression and script hash. It is not an automated page fetch, frequency
measurement or a claim that generation has browsed sources. A candidate's own
`usage_review` field is discarded. Missing/mismatched evidence prevents conversion
and rendering; it does not prevent the core Podcast from publishing. The current
checked reference is `shorts/reviews/enter-merger-discussions.json`.

Podcast-derived videos display `Podcast教材の一文を、そのまま使用` and the source
lesson's publication date; they do not label real source sentences as invented
practice examples. Full lesson links are kept in the description draft. Historical
materials are not presented as today's news. Manual-preview review status can be
used for a human-reviewed historical sample; it does not assert that the old
lesson passed the newer automated fact-checking pipeline.

## Historical preview

One sample uses the publicly displayed Podcast script from WordPress post 1931,
published 2026-10-02, associated with Spreaker episode 75497643. It selects:

> By merging, the banks can reduce costs and increase their profitability.

The target is `reduce costs`; the Japanese translation preserves `can`. The
application introduces `cost reduction` separately as a noun expression. Public
WordPress JSON and the extracted script are preserved under ignored
`output/shorts-podcast-source/`. This is the site's published transcript; the old
episode audio was not retranscribed or independently aligned against it.

Offline tests cover altered modality, fabricated Vocabulary examples, cut
clauses, changed expressions, source-hash changes, optional skips, independent
Shorts review, disabled export, failed WordPress publication, and nonfatal S3
draft failures. All external publishing and paid model calls are mocked in tests.
