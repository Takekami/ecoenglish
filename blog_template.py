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
    usage: str,
    example_usage: str,
    jp: str,
    audio_url: str,
) -> str:
    # Clean answers
    answers = [line.strip() for line in ans.strip().splitlines() if line.strip() and not line.startswith("###")]
    answers = [re.sub(r'^\d+\.\s*', '', a) for a in answers]

    # Vocabulary section
    vocab_html = "<ul class='list-unstyled'>"
    # Split on list items
    entries = re.split(r'(?m)^-\s+', vocab.strip())[1:]
    for entry in entries:
        lines = entry.splitlines()
        header = lines[0]
        if ':' not in header:
            continue
        word, definition = header.split(':', 1)
        word = word.strip()
        definition = definition.strip()
        # Extract English def and JP term
        m = re.match(r"^(.*?)(?:（日本語訳：(.+?)）)$", definition)
        if m:
            eng_def, jp_term = m.group(1).strip(), m.group(2).strip()
        else:
            eng_def, jp_term = definition, ''
        # Parse example and collocations
        example = ''
        colls = []
        for line in lines[1:]:
            line = line.strip()
            if line.startswith('例文:'):
                example = line[len('例文:'):].strip().strip('“”"')
            elif line.startswith('Collocations:'):
                coll_list = line.split(':',1)[1]
                colls = [c.strip() for c in coll_list.split(',') if c.strip()]
        # Build HTML
        vocab_html += "<li class='mb-3'>"
        vocab_html += f"<strong>{word}</strong>: {eng_def}"
        if example:
            vocab_html += f"<div class='mt-1'><em>例文:</em> “{example}”</div>"
        if colls:
            vocab_html += (
                "<details class='mt-1'>"
                "<summary class='text-primary'>▼ Collocationsを見る</summary>"
                "<ul>"
                + ''.join(f"<li>{c}</li>" for c in colls)
                + "</ul></details>"
            )
        if jp_term:
            vocab_html += (
                "<details class='mt-1'>"
                "<summary class='text-primary'>▼ 日本語の意味を見る</summary>"
                f"<div class='mt-1'>{jp_term}</div>"
                "</details>"
            )
        vocab_html += "</li>"
    vocab_html += "</ul>"

    # Grammar Point section
    raw_gp = gp.strip()
    if '（' in raw_gp and raw_gp.endswith('）'):
        main_part, jp_part = raw_gp.rsplit('（', 1)
        jp_part = jp_part.rstrip('）')
    else:
        main_part, jp_part = raw_gp, ''
    grammar_html = markdown(main_part, extensions=['extra'])
    if jp_part:
        grammar_html += (
            "<details class='mt-2'>"
            "<summary class='text-primary'>▼ 文法の日本語補足を見る</summary>"
            f"<div class='mt-1'>{jp_part}</div>"
            "</details>"
        )
    # Usage and Example (always expanded)
    if usage.strip():
        grammar_html += f"<h3>💡 使用場面</h3><p>{usage.strip()}</p>"
    if example_usage.strip():
        ex = example_usage.strip().strip('“”"')
        grammar_html += f"<h3>📝 使用例文</h3><p><em>“{ex}”</em></p>"

    # Japanese Economic Insight
    jp_html = ''
    clean_jp = re.sub(r'[“`]+$', '', jp.strip())
    if clean_jp:
        jp_html = '<h2>🇯🇵 日本語での経済ニュース解説</h2>' + markdown(clean_jp, extensions=['extra'])

    # Build full HTML
    html = (
        '<html><head>'
        '<meta charset="utf-8">'
        '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">'
        '</head><body class="container my-4">'

        '<h2>🎧 Audio</h2>'
        f'<audio controls src="{audio_url}"></audio>'

        '<h2>📖 Script</h2>' + markdown(script, extensions=['extra']) +
        '<h2>📝 Vocabulary</h2>' + vocab_html +
        '<h2>✏️ Grammar Point</h2>' + grammar_html +
        '<h2>❓ Listening Questions</h2>' +
        markdown(lq, extensions=['extra']) +
        '<h2>📚 Reading Questions</h2>' +
        markdown(rq, extensions=['extra']) +

        jp_html +
        f'<p class="text-muted">Source: <a href="{url}">{url}</a></p>' +
        '</body></html>'
    )
    return html.strip()
