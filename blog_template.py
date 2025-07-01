from html import escape

def build_blog_post_html(level, headline, source_url,
                         script, listen_q, read_q, grammar, audio_url):
    def details_block(title, body_md):
        body = "<br>".join(map(escape, body_md.splitlines()))
        return f"<details><summary>{title}</summary><div>{body}</div></details>"

    # 質問は “正答なし” バージョンを本文に入れ、
    # 別途 Answers セクションで折りたたむ
    lq_no_ans = "\n".join(
        line for line in listen_q.splitlines() if not line.strip().startswith("–")
    )
    rq_no_ans = "\n".join(
        line for line in read_q.splitlines() if not line.strip().startswith("–")
    )

    answer_block = details_block("解答と解説 (クリックで表示)", listen_q + "\n" + read_q)

    html = f"""
<h2>🎧 Audio</h2>
<audio controls src="{audio_url}"></audio>

<h2>📖 Script</h2>
<pre>{escape(script)}</pre>

<h2>◇ Listening Questions （リスニング問題）</h2>
<pre>{escape(lq_no_ans)}</pre>

<h2>◇ Reading Questions （読解問題）</h2>
<pre>{escape(rq_no_ans)}</pre>

{answer_block}

<h2>✏️ Grammar Point</h2>
<pre>{escape(grammar)}</pre>

<hr>
<p>Source: <a href="{source_url}" target="_blank" rel="noopener noreferrer">{headline}</a></p>
"""
    return html
