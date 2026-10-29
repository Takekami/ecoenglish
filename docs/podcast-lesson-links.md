# Podcast lesson links

After source and lesson quality gates pass, the existing pipeline publishes audio
to Spreaker and a matching lesson to WordPress. Once WordPress returns its public
HTTPS permalink, the pipeline updates **only** that episode's description using
Spreaker's documented `POST /v2/episodes/{id}` API. Japanese show notes link to the
matching lesson with `utm_source=spreaker`, `utm_medium=podcast`,
`utm_campaign=news_lessons` and the episode ID in `utm_content`.

The generated S3 RSS item also includes a direct tracked lesson link, with source
`podcast_rss`. XML values are escaped, including the ampersands in tracked URLs.
The existing RSS file still contains the current episode only; feed-history
redesign is outside this change. Spreaker's own feed is managed by Spreaker.

A WordPress failure never publishes a guessed lesson link. A Spreaker metadata
update failure logs `podcast_lesson_link=FAILED` with the episode ID and exception
type, leaving the already-published episode intact; it does not fail the handler
and invite a duplicate upload on retry. Its original Japanese description links
to the library. Successful updates log `podcast_lesson_link=UPDATED`.

There is a short interval between initial audio publication and the final lesson
link update. This is not a transaction across services. Past episodes are not
bulk-edited. If metadata update fails, the logged episode can be repaired manually.

No extra model call, credential scope, subscription or service was added. One
small metadata request is added per successful publication. Do not run the handler
as a test: it publishes and incurs existing generation/audio charges.

Reference: https://developers.spreaker.com/api/episodes/
