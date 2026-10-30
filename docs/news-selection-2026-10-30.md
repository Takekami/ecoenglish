# News selection and repair rollout — 2026-10-30

## Existing lessons

Backups and verification receipts are in ignored `output/selection-fixes-2026-10-30/`.
WordPress posts 1940 and 1941 now explain the actual quoted grammar, with practice
examples demonstrating that structure and dated correction notes. Post 1947 now
says Semiconductors, not Semiconductor shares, when referring to parts inside
electronic devices. Its original Podcast audio is retained and the lesson openly
notes the earlier spoken error. All three corrections were read back through the
public WordPress API. This is targeted remediation, not a full historical fact audit.

## New production selection flow

1. Read the last 30 public WordPress lessons, extracting source URLs and titles.
   Fail closed when history cannot be read, avoiding blind duplicate selection.
2. Fetch each of the 3 existing feeds once, bounded by HTTP timeouts. Select up to
   6 unique recent candidates per feed, exclude published URLs, and reject known
   dates older than 7 days or more than 6 hours in the future. Unknown dates are
   explicitly recorded rather than silently represented as fresh.
3. Compare all candidates in one classifier call. Economic centrality, reusable
   intermediate learning value, comprehensibility and recent-topic novelty use
   an explicit editorial rubric. These points are ranking aids, not calibrated
   confidence, learner-outcome evidence or formal CEFR ratings. Politics/security
   with incidental economic context do not meet the economic centrality threshold.
4. Try up to 3 ranked eligible candidates. Retrieve actual source text; retain the
   existing source sufficiency gate and article/RSS fallback policy.
5. Generate a source-supported lesson. On structural or semantic rejection, allow
   one correction per candidate, then re-run ALL structural and independent review
   gates. A still-invalid candidate or explicit generation SKIP moves to the next
   candidate. Never fall back after external publication has started.
6. Respect the existing 300-second Lambda limit: reserve time for review and
   publication; a depleted time budget produces an explicit hold outcome. API
   calls have a 45-second client timeout and no automatic SDK retries. Candidate
   fallback cannot guarantee daily output, and the retry cap is deliberately finite.

The original speech, Spreaker, WordPress and RSS publishing path remains after the
new preparation gate. Optional Shorts source export remains controlled by its
existing environment flag; this rollout does not enable YouTube scheduling.

## Decision logs

One JSON object per event with `system=ecoenglish`, `schema_version=1`, `run_id`,
`stage`, candidate ID and source URL when applicable. Stages include feed/history
availability, candidate collection/rejection, ranking scores and brief reasons,
source HTTP status/word counts, validation/review failures, repair, next candidate,
lesson readiness and final outcome. Full article bodies, drafts and credentials
are not logged. Model-generated explanations remain fallible; reasons are
recorded evidence of the decision, not proof that it was correct.

Known terminal outcomes include HISTORY_UNAVAILABLE, NO_CANDIDATES, RANKING_FAILED,
MODEL_CONFIGURATION_ERROR, TIME_BUDGET, TIME_BUDGET_BEFORE_PUBLISH,
NO_ELIGIBLE_LESSON, DRY_RUN_READY, SUCCESS and WORDPRESS_FAILED.

## Verification and operational use

Offline tests mock model calls, source fetches and all publication writers. Tests
cover comparison coverage/types, duplicate/stale URL filtering, source fallback,
generation SKIP, one repair followed by complete re-review, failed repair moving
on, the grammar regression, history/time budget failures and zero publishing
side effects in dry-run mode.

The new explicit `{"dry_run":true}` handler event exercises selection, generation,
validation and semantic review, then returns BEFORE TTS/S3/Spreaker/WordPress/RSS
writes. It may incur bounded text-model usage. Only this documented event is safe
for production preflight; do not invoke the handler with an empty event as a test.

The daily schedule is not changed. Generation/repair usage can rise compared with
the earlier first-match pipeline; no new recurring infrastructure is provisioned.

Official OpenAI JSON-mode reference consulted:
https://developers.openai.com/api/docs/guides/structured-outputs
JSON mode is parsed and validated explicitly; missing/malformed ranking or review
fields never permit publication.
