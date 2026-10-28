# Econenglish learning navigation

Standalone WordPress plugin; deploying the Lambda container does **not** install it.
Package only `wordpress/econenglish-learning/` into `econenglish-learning.zip`, upload
through WordPress Plugins > Add Plugin > Upload, and activate. No credentials are
bundled. No new third-party service or tracking tag is installed.

## Public behavior

- Reuses the published `howtousethisblogandpodcast` post/page as the guide. Its saved
  title, URL and original body are preserved; `the_content` renders the new guide.
  Deactivation restores the original display. If absent, creates `/start-here/`.
- Creates `/lesson-library/` with `[econenglish_library]`; 12 lessons per page,
  six topic filters, ordinary anchor links and explicit publication dates.
- Detects published posts with audio/Spreaker embed and a Script heading; ordinary
  blog posts and drafts are excluded. The guide is not indexed as a lesson.
- Existing post IDs are snapshotted at activation and indexed 60 at a time via
  WP-Cron. Tools > 教材ナビ allows remaining batches to be processed manually.
  The queue is retained on deactivation; no posts are deleted.
- New posts are indexed on `save_post_post`. Headline matches weigh more than
  script matches; vocabulary/question boilerplate is not used. Topics are a
  deterministic heuristic, not an editorial accuracy guarantee. Up to two themes
  are assigned. The taxonomy is private (no extra thin taxonomy archives).
- Same-topic lessons are selected by publication date, excluding the current
  article. If none exist, the heading explicitly changes to a general next-lesson
  list. Individual difficulty scores are not inferred.
- Homepage entry links are server-rendered in the footer and moved before the
  main content by JS; they remain accessible in the footer without JS.
- Royal Mail post 1469 is used as a starter only when it is a published lesson;
  the other two suggestions are labeled as recent, not individually reviewed.

## Measurement

Uses the existing Site Kit `gtag` function, targeting existing GA4 destination
`G-EMJ73ZY8ZW`, and inherits its consent configuration. Does not initialize a second
Google tag or bypass blocked/denied Analytics. Logged-in editors/admins are
excluded. Event handlers never block navigation or audio playback.

| Event | Meaning |
| --- | --- |
| `guide_click`, `library_click` | Guide/library navigation click |
| `topic_select`, `library_page` | Topic/page navigation |
| `starter_lesson_click`, `lesson_select`, `related_lesson_click` | Lesson selection by placement |
| `lesson_audio_start` | First native HTML audio play per player/page |
| `lesson_audio_complete` | First native HTML audio ended per player/page |
| `lesson_answer_open` | First opening of each answer disclosure per page |

Custom parameters contain only lesson IDs, enumerated topic/placement/group and
player type. No learner answers, email addresses or free text are captured.
Spreaker iframe playback is cross-origin and **not** counted as a native audio play.
Counts do not prove comprehension or learning outcomes. GA4 realtime receipt must
be verified separately from unit tests; registering event-scoped custom dimensions
is needed to report custom parameters through standard GA4 explorations.

## Verification and rollback

`node --test wordpress/tests/learning.test.cjs` tests event semantics. The GitHub
`Verify WordPress learning navigation` workflow lints PHP and runs integration
checks against a fresh WordPress/MariaDB database, with no production secrets.

After activation, verify a logged-out guide, all/filter/page-2 library views,
Royal Mail's related section, homepage placement and narrow viewport layout.
Check Tools > 教材ナビ reaches zero remaining queue items. Verify new posts are
classified via the save hook without running the production publishing handler.

To roll back, deactivate this plugin, clear WP Fastest Cache, and remove any menu
links manually added for the library. The new library page can be moved to Trash
if no longer needed; original guide content remains in the database. This plugin
does not change parent theme files, existing SEO ownership or Lambda behavior.

Weekly email and monetization are deferred by user choice until a service and
approved affiliate/donation destination exist; no nonfunctional signup or payment
buttons are published.
