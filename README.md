# EcoEnglish Learning

Automated pipeline that turns Asia-Pacific business news into daily English listening lessons for Japanese intermediate learners (B1–B2). Each run produces a podcast episode, a WordPress blog post with full study materials, and an RSS feed update.

Published at [Econenglish](https://econenglish.jp/category/english-learning/).

## What it does

1. **Select article** — Picks a business news item from a rotating RSS feed (Nikkei Asia or BBC Business), with up to 5 retries if nothing suitable is found.
2. **Filter** — Uses GPT-3.5-turbo to check whether the story is economically or socially significant (Asia-Pacific business preferred).
3. **Generate lesson** — Uses GPT-4o to produce a structured lesson: script, vocabulary, listening/reading questions, answers, grammar point, and Japanese commentary.
4. **Synthesize audio** — Converts the script to MP3 via OpenAI TTS and uploads it to S3.
5. **Publish podcast** — Uploads the episode to Spreaker and retrieves a stream URL.
6. **Publish blog** — Posts an HTML lesson page to WordPress with an embedded audio player.
7. **Update RSS** — Writes a podcast RSS file and uploads it to S3.

## Architecture

```
RSS (Nikkei Asia / BBC Business)
        │
        ▼
   AWS Lambda (container)
   ┌──────────────────────────────────────────────┐
   │  Article selection → GPT filter → GPT lesson │
   │       → OpenAI TTS → S3                      │
   │       → Spreaker → WordPress → S3 (RSS)      │
   └──────────────────────────────────────────────┘
        │
        ├── Spreaker (podcast)
        ├── WordPress / econenglish.jp (blog + quizzes)
        └── S3 (audio + RSS)
```

## Project structure


| File                                   | Purpose                              |
| -------------------------------------- | ------------------------------------ |
| `main.py`                              | Lambda handler and orchestration     |
| `prompt_templates.py`                  | GPT prompts for lesson generation    |
| `blog_template.py`                     | WordPress HTML builder               |
| `aws_utils.py`                         | OpenAI TTS and S3 upload             |
| `wp_poster.py`                         | WordPress REST API client            |
| `spreaker_uploader.py`                 | Spreaker episode upload (OAuth2)     |
| `rss_generator.py`                     | iTunes-compatible RSS generator      |
| `Dockerfile`                           | Lambda container image (Python 3.12) |
| `.github/workflows/deploy_podcast.yml` | Manual deploy to AWS                 |


## Requirements

- Python 3.12 (matches the Lambda runtime)
- AWS account with Lambda, S3, and ECR configured
- OpenAI API key
- WordPress site with Application Password enabled
- Spreaker show with OAuth2 credentials

## Environment variables

Set these on the Lambda function (or in a local `.env` for development). Do not commit secrets.


| Variable                 | Required | Description                                                                  |
| ------------------------ | -------- | ---------------------------------------------------------------------------- |
| `OPENAI_API_KEY`         | Yes      | OpenAI API key (GPT + TTS)                                                   |
| `S3_BUCKET_NAME`         | Yes      | S3 bucket for audio and RSS files                                            |
| `WP_URL`                 | Yes      | WordPress REST API endpoint (e.g. `https://example.com/wp-json/wp/v2/posts`) |
| `WP_USER`                | Yes      | WordPress username                                                           |
| `WP_APP_PASS`            | Yes      | WordPress application password                                               |
| `SPREAKER_SHOW_ID`       | Yes      | Spreaker show ID                                                             |
| `SPREAKER_OAUTH_TOKEN`   | Yes*     | Spreaker access token (*refreshed automatically if expired)                  |
| `SPREAKER_REFRESH_TOKEN` | Yes      | Spreaker OAuth2 refresh token                                                |
| `SPREAKER_CLIENT_ID`     | Yes      | Spreaker OAuth2 client ID                                                    |
| `SPREAKER_CLIENT_SECRET` | Yes      | Spreaker OAuth2 client secret                                                |


`main.py` validates the first eight variables at startup. Spreaker client credentials are read when uploading an episode.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file with the variables above, then load them before running:

```bash
export $(grep -v '^#' .env | xargs)
python -c "from main import handler; print(handler())"
```

## Deployment

Deployment is **manual** via GitHub Actions — pushing to GitHub does **not** auto-deploy.

1. Push your changes to GitHub.
2. Open **Actions → Deploy EcoEnglish Lambda Container → Run workflow**.
3. The workflow will:
  - Authenticate to AWS via OIDC (`AWS_ROLE_ARN` secret)
  - Build the Docker image for `linux/amd64`
  - Push to ECR (`ap-southeast-2`, repository `ecoenglish`)
  - Update the Lambda function `ecoenglish` with the new image

Lambda environment variables are managed separately in AWS and are not updated by the workflow.

## Scheduling

The Lambda function is intended to run on a schedule (e.g. AWS EventBridge). Schedule configuration lives in AWS, not in this repository.

## News sources

Two RSS feeds rotate daily:


| Feed         | URL                                              |
| ------------ | ------------------------------------------------ |
| Nikkei Asia  | `https://asia.nikkei.com/rss/feed/nar`           |
| BBC Business | `https://feeds.bbci.co.uk/news/business/rss.xml` |


Nikkei Asia entries may contain only a headline (no summary). The pipeline falls back to the title when a summary is missing.

## Generated content

Each successful run produces:

- **Script** — ~380–420 words, CEFR B1+ level
- **Vocabulary** — 5 words with definitions, example sentences, and collocations
- **Listening questions** — 1 True/False + 2 multiple choice
- **Reading questions** — Detail, inference, and vocabulary-in-context
- **Grammar point** — With usage notes in Japanese
- **Japanese economic commentary** — Background and outlook (~300–400 characters)

## License

All rights reserved unless otherwise specified.