# Publishing quality gates

The pipeline now runs these checks **before TTS, S3, Spreaker or WordPress writes**:

1. Extract the linked news article with trafilatura, requesting only HTTPS URLs on the three configured publishers. Redirects are not followed, downloads are bounded, and no paywalls/login barriers are bypassed.
2. Require at least 120 words of source text. If article extraction fails, sufficiently long RSS content may be used. Headlines and short summaries are never expanded into a lesson. This threshold is a heuristic, not a guarantee of source quality.
3. Generate learner material using only source-supported claims, preserving uncertainty. A shorter lesson is preferable to invented detail. Produce Japanese title, description and introduction too.
4. Require all sections, an actual grammar sentence copied from the script and quoted by the explanation, five vocabulary items, three listening questions (one T/F, two four-option MCQs), three reading questions and six numbered answers. Japanese metadata must be bounded plain text.
5. Independently review the source and lesson for source sufficiency, unsupported facts, grammar correctness, answer correctness/ambiguity and metadata accuracy. Only five explicit JSON booleans set to true permit publication. This LLM review is fallible and is not independent real-world fact verification.

A rejected/undersourced lesson logs `INSUFFICIENT_SOURCE`, `QUALITY_SKIP` or `REVIEW_SKIP` and produces no external publishing side effects. Review/API failures also stop before publication. Some days will have no episode, particularly when publishers provide only headlines or block extraction. No full article bodies or credentials are logged or included in the published post.

The WordPress title uses the Japanese Title; the manual excerpt uses Meta Description. The current AIOSEO configuration derives its description from that excerpt (verified on the manually improved Royal Mail article). Introduction is rendered at the start of each new post. Existing posts are not bulk-rewritten. Theme/SEO settings must continue to use the excerpt; this integration needs post-deployment verification on one new post.

Run offline tests: `python -m unittest discover -s tests -v`. They mock all paid API and publishing calls. Deployment remains the repository's manual GitHub Actions workflow. Verify source selection and one generated lesson without invoking the publishing handler before a production rollout. Never run `handler()` as a smoke test: it publishes.
