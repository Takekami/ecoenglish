# Publishing quality gates

2026-11-11: active inputs are Statistics Bureau of Japan's dated English updates,
MOF Japan's English RSS, BEA news RSS, and FRB monetary-policy and speech RSS.
Reuse notices are recorded in `source_catalog.py`; published lessons credit the
issuer, link its terms, and identify Econenglish's editing/translation. Images,
logos and separately restricted third-party works are not licensed by that notice.
Nikkei Asia, CNBC and CNA feeds have been removed from active selection. Their
hosts remain recognized for historical lesson links and compatibility.
China-related events are prioritized, but no direct Chinese issuer feed has yet
passed this review. Australia has no preferential source or ranking treatment.

Official bodies are fetched before ranking (at most four concurrent requests).
Ranking reads a bounded source excerpt; the full fetched text is reused for
generation/review. Core learning value includes basic/contextual vocabulary,
grammar, listening and reading; transferable collocations apply only to optional
Shorts. Source periods, units, revisions and issuer attribution must be preserved.
The Statistics Bureau's changing result URLs are deduplicated per release date,
stored in the source attribution, so a previous month's lesson does not suppress
a new release. The seven-day freshness and factual publication checks still apply.

2026-10-30: source selection compares candidates across feeds and
supports a bounded correction/next-candidate path. See
[selection and recovery](news-selection-2026-10-30.md) for ranking, decision logs
and the explicit non-publishing dry-run event. Existing factual gates remain.

The pipeline now runs these checks **before TTS, S3, Spreaker or WordPress writes**:

1. Extract the linked official text with trafilatura, requesting only HTTPS URLs on configured hosts. Redirects are not followed and downloads are bounded.
2. Require at least 120 words of source text. If article extraction fails, sufficiently long RSS content may be used. Headlines and short summaries are never expanded into a lesson. This threshold is a heuristic, not a guarantee of source quality.
3. Generate learner material using only source-supported claims, preserving uncertainty. A shorter lesson is preferable to invented detail. Produce Japanese title, description and introduction too.
4. Require all sections, an actual grammar sentence copied from the script and quoted by the explanation, five vocabulary items, three listening questions (one T/F, two four-option MCQs), three reading questions and six numbered answers. Japanese metadata must be bounded plain text.
5. Independently review the source and lesson for source sufficiency, unsupported facts, grammar correctness, answer correctness/ambiguity and metadata accuracy. Only five explicit JSON booleans set to true permit publication. This LLM review is fallible and is not independent real-world fact verification.

A rejected/undersourced lesson logs `INSUFFICIENT_SOURCE`, `QUALITY_SKIP` or `REVIEW_SKIP` and produces no external publishing side effects. Review/API failures also stop before publication. Some days will have no episode, particularly when publishers provide only headlines or block extraction. No full article bodies or credentials are logged or included in the published post.

The WordPress title uses the Japanese Title; the manual excerpt uses Meta Description. The current AIOSEO configuration derives its description from that excerpt (verified on the manually improved Royal Mail article). Introduction is rendered at the start of each new post. Existing posts are not bulk-rewritten. Theme/SEO settings must continue to use the excerpt; this integration needs post-deployment verification on one new post.

Run offline tests: `python -m unittest discover -s tests -v`. They mock all paid API and publishing calls. Deployment remains the repository's manual GitHub Actions workflow. Only the explicit `handler({"dry_run": true})` event is a non-publishing preflight; it still uses text-model calls. Never run `handler()` with an empty/default event as a smoke test: that path publishes.
