from markdown import markdown
import re

def build_blog_post_html(
    level: str,
    title: str,
    url: str,
    script: str,
    vocab: str,
    lq: str,
    rq: str,
    ans: str,
    gp: str,
    jp: str,
    audio_url: str,
) -> str:
    answers = [line.strip() for line in ans.strip().splitlines() if line.strip() and not line.startswith("###")]

    # Vocabulary
    vocab_html = "<ul class='list-unstyled'>"
    for line in vocab.strip().splitlines():
        if ":" not in line:
            continue
        word, definition = line.split(":", 1)
        word = word.strip()
        definition = definition.strip()

        m = re.match(r"^(.*?)(?:（日本語訳：(.+?)）)$", definition)
        if m:
            eng_def = m.group(1).strip()
            jp_def  = m.group(2).strip()
        else:
            eng_def = definition
            jp_def  = ""

        vocab_html += f"""
        <li class=\"mb-3\">\n  <strong>{word}</strong>: {eng_def}"""
        if jp_def:
            vocab_html += f"""
  <details class=\"mt-1\">\n    <summary class=\"text-primary\">日本語の意味を見る</summary>\n    <div class=\"mt-1\">{jp_def}</div>\n  </details>"""
        vocab_html += "\n        </li>"
    vocab_html += "</ul>"

    # Grammar Point
    raw_gp = gp.strip()
    if "（" in raw_gp and raw_gp.endswith("）"):
        main_part, jp_part = raw_gp.rsplit("（", 1)
        jp_part = jp_part.rstrip("）")
    else:
        main_part, jp_part = raw_gp, ""

    grammar_html = markdown(main_part, extensions=["extra"])
    if jp_part:
        grammar_html += f"""
<details class=\"mt-2\">\n  <summary class=\"text-primary\">文法の日本語補足を見る</summary>\n  <div class=\"mt-1\">{jp_part}</div>\n</details>"""

    # Listening Questions (static answers)
    listen_html = markdown(lq, extensions=["extra"])
    listen_html += f"""
<details class=\"mt-3\">\n  <summary class=\"text-primary\">🔑 Listening Answersを見る</summary>\n  <ol>\n    <li>{answers[0] if len(answers) > 0 else ''}</li>\n    <li>{answers[1] if len(answers) > 1 else ''}</li>\n    <li>{answers[2] if len(answers) > 2 else ''}</li>\n  </ol>\n</details>"""

    # Reading Questions (static answers)
    reading_html = markdown(rq, extensions=["extra"])
    reading_html += f"""
<details class=\"mt-3\">\n  <summary class=\"text-primary\">🔑 Reading Answersを見る</summary>\n  <ol>\n    <li>{answers[3] if len(answers) > 3 else ''}</li>\n    <li>{answers[4] if len(answers) > 4 else ''}</li>\n    <li>{answers[5] if len(answers) > 5 else ''}</li>\n  </ol>\n</details>"""

    # Japanese Economic Insight
    jp_html = ""
    if jp.strip():
        jp_html = f"<h2>🇯🇵 日本語での経済ニュース解説</h2>\n" + markdown(jp, extensions=['extra'])

    # Build full HTML
    html = f"""
<html>
<head>
  <meta charset=\"utf-8\">
  <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
</head>
<body class=\"container my-4\">

<h2>🎧 Audio</h2>
<audio controls src=\"{audio_url}\"></audio>

<h2>📖 Script</h2>
{markdown(script, extensions=["extra"]) }

<h2>📝 Vocabulary</h2>
{vocab_html}

<h2>✏️ Grammar Point</h2>
{grammar_html}

<h2>❓ Listening Questions</h2>
{listen_html}

<h2>📚 Reading Questions</h2>
{reading_html}

{jp_html}

<p class=\"text-muted\">Source: <a href=\"{url}\">{url}</a></p>

</body>
</html>
"""
    return html