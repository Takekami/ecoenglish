# Econenglish learning navigation

Standalone WordPress plugin; deploying the Lambda container does **not** install it.
Package only `wordpress/econenglish-learning/` into `econenglish-learning.zip`, upload
through WordPress Plugins > Add Plugin > Upload, and activate. No credentials are
bundled. No new third-party service or tracking tag is installed.

## Version 1.2 shared lesson entries

- Every lesson has a common `#eel-start` menu for full audio, full script,
  expression/vocabulary review and the existing quiz. Only available destinations
  are linked. The menu is visible without JS. No flow is labeled as exclusive to
  Podcast or short-video visitors.
- Study-mode/completion controls, site-wide learning links and the theme's long
  TOC are optional disclosures. Stored original lesson content is preserved.
- Post 1931 has a reviewed `#eel-expressions` section after the full script. It
  quotes the exact source sentence, gives its Japanese translation, includes a
  same-origin MP3 of that one sentence with optional looping, explains a related
  expression separately, and links to the actual issuer usage reference.
  The quote must still occur in that post's Script or the card is not displayed.
  Other lessons link to their existing Vocabulary section; no unreviewed or empty
  expression cards are fabricated. New reviewed cards currently require updating
  the curated data in `expressions.php`; daily automatic import is not enabled.
- Sentence audio is synthesized learning audio, explicitly labeled. It is not a
  cut aligned to the original episode. No new TTS request was made for this
  rollout: the already approved preview's exact sentence recording was encoded
  as an 84KB MP3 and bundled with the plugin.
- `expression_audio_start/complete` are separate from full-episode audio events;
  repeat toggles and common-menu clicks use bounded enumerated parameters.
- Podcast link generation now targets `#eel-start`; the local Shorts manifest
  converter targets `#eel-expressions`. Lambda code/link changes require their
  separate deployment and are not activated by a WordPress plugin upload.

## Version 1.1 growth features

- A study toolbar offers listening/questions first, with reversible hiding of the
  script, vocabulary, grammar, reading and Japanese commentary. Existing content
  is not rewritten. Anchor/TOC links reveal a hidden destination before navigating.
  Without JS, full content remains visible. Missing sections disable mode links.
- A completion mark is stored only in this browser's localStorage under
  `econenglish.completed.v1` (maximum 200 numeric post IDs). It is reversible,
  is shown on lesson cards and is not an assessment or cross-device account.
  Blocked storage displays a message while leaving learning features usable.
- Tools > 教材ナビ > `解説3本と週次復習ページを公開・確認` idempotently creates
  three original evergreen guides and `/weekly-review/`. Activation also creates
  these pages. Unrelated pages with the same slug are never overwritten.
- Weekly review uses the previous calendar week in the WordPress site timezone,
  selects up to three published lessons and copies their first existing T/F
  question and answer. Unsupported markup/answers are skipped, never guessed.
  There is an explicit empty state. No new AI calls, email or audio publishing
  occur. New weeks are computed on render; the page opts out of full page caching,
  and a Monday 06:00 WP-Cron task also clears the existing cache. WP-Cron runs when
  WordPress receives traffic, not as an exact-time scheduler.
- New events: `lesson_mode_change`, `lesson_mark_complete`, `weekly_answer_open`,
  `weekly_lesson_click`, `weekly_click`, `learning_guide_click`, `guide_lesson_click`.
  These use the existing GA4 tag, and contain no written learner answers.
- New articles: `/study-english-with-economic-news/`,
  `/english-news-listening-practice/`, `/inflation-news-english-vocabulary/`.
  Original content is in `learning-content.php`; examples are explicitly exercises.
  The guides link to actual lessons, each other and primary reference sources.

Tests: `NODE_PATH=/private/tmp/eel-js-test/node_modules node --test wordpress/tests/*.test.cjs`
after installing `jsdom@26.1.0` into that temporary prefix. CI installs the pinned
test dependency and verifies against isolated WordPress/MariaDB.

On rollback, deactivate the plugin and move these shortcode pages to Trash or
replace their content. Browser marks can be removed through site-data settings.

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
