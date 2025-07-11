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
    # Extract and clean answer lines, remove numeric prefixes (e.g., "1. ")
    answers = [
        line.strip() for line in ans.strip().splitlines()
        if line.strip() and not line.startswith("###")
    ]
    answers = [re.sub(r'^\d+\.\s*', '', a) for a in answers]

    # Vocabulary section
    vocab_html = "<ul class='list-unstyled'>"
    for line in vocab.strip().splitlines():
        if ":" not in line:
            continue
        word, definition = line.split(":", 1)
        word = word.strip()
        definition = definition.strip()

        m = re.match(r"^(.*?)(?:（日本語訳：(.+?)）)$", definition)
        if m:
            eng_def, jp_def = m.group(1).strip(), m.group(2).strip()
        else:
            eng_def, jp_def = definition, ""

        vocab_html += "<li class='mb-3'>"
        vocab_html += f"<strong>{word}</strong>: {eng_def}"
        if jp_def:
            vocab_html += (
                "<details class='mt-1'>"
                "<summary class='text-primary'>▼ 日本語の意味を見る</summary>"
                f"<div class='mt-1'>{jp_def}</div>"
                "</details>"
            )
        vocab_html += "</li>"
    vocab_html += "</ul>"

    # Grammar Point section
    raw_gp = gp.strip()
    if "（" in raw_gp and raw_gp.endswith("）"):
        main_part, jp_part = raw_gp.rsplit("（", 1)
        jp_part = jp_part.rstrip("）")
    else:
        main_part, jp_part = raw_gp, ""

    grammar_html = markdown(main_part, extensions=["extra"])
    if jp_part:
        grammar_html += (
            "<details class='mt-2'>"
            "<summary class='text-primary'>▼ 文法の日本語補足を見る</summary>"
            f"<div class='mt-1'>{jp_part}</div>"
            "</details>"
        )

    # Listening Questions with static answers
    listen_html = markdown(lq, extensions=["extra"])
    listen_html += (
        "<details class='mt-3'>"
        "<summary class='text-primary'>🔑 Listening Answersを見る</summary>"
        "<ol>"
        f"<li>{answers[0] if len(answers) > 0 else ''}</li>"
        f"<li>{answers[1] if len(answers) > 1 else ''}</li>"
        f"<li>{answers[2] if len(answers) > 2 else ''}</li>"
        "</ol>"
        "</details>"
    )

    # Reading Questions with static answers
    reading_html = markdown(rq, extensions=["extra"])
    reading_html += (
        "<details class='mt-3'>"
        "<summary class='text-primary'>🔑 Reading Answersを見る</summary>"
        "<ol>"
        f"<li>{answers[3] if len(answers) > 3 else ''}</li>"
        f"<li>{answers[4] if len(answers) > 4 else ''}</li>"
        f"<li>{answers[5] if len(answers) > 5 else ''}</li>"
        "</ol>"
        "</details>"
    )

    # Japanese Economic Insight section
    jp_html = ""
    clean_jp = re.sub(r"[“`]+$", "", jp.strip())
    if clean_jp:
        jp_html = (
            "<h2>🇯🇵 日本語での経済ニュース解説</h2>"
            + markdown(clean_jp, extensions=["extra"])
        )

    # Build full HTML, trim whitespace
    html = (
        "<html>"
        "<head>"
        "<meta charset='utf-8'>"
        "<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>"
        "</head>"
        "<body class='container my-4'>"

        "<h2>🎧 Audio</h2>"
        f"<audio controls src='{audio_url}'></audio>"

        "<h2>📖 Script</h2>"
        + markdown(script, extensions=["extra"]) +

        "<h2>📝 Vocabulary</h2>"
        + vocab_html +

        "<h2>✏️ Grammar Point</h2>"
        + grammar_html +

        "<h2>❓ Listening Questions</h2>"
        + listen_html +

        "<h2>📚 Reading Questions</h2>"
        + reading_html +

        jp_html +

        f"<p class='text-muted'>Source: <a href='{url}'>{url}</a></p>"

        "</body></html>"
    )
    return html.strip()
