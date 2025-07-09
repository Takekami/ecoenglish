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

    js_script = f"""
<script>
function checkListening() {{
    const ans = {{
        lq1: "{answers[0] if len(answers) > 0 else ''}",
        lq2: "{answers[1] if len(answers) > 1 else ''}",
        lq3: "{answers[2] if len(answers) > 2 else ''}"
    }};
    const user1 = document.querySelector("input[name='lq1']:checked")?.value;
    const user2 = document.querySelector("input[name='lq2']:checked")?.value;
    const user3 = document.querySelector("input[name='lq3']:checked")?.value;

    const fb1 = document.getElementById("fb-lq1");
    const fb2 = document.getElementById("fb-lq2");
    const fb3 = document.getElementById("fb-lq3");

    let correctCount = 0;
    const total = 3;

    if (user1 === ans.lq1) {{ correctCount++; fb1.innerHTML = "✅ <span class='text-success'>正解</span>"; }}
    else {{ fb1.innerHTML = "❌ <span class='text-danger'>不正解</span>（正答: " + ans.lq1 + ")"; }}

    if (user2 === ans.lq2) {{ correctCount++; fb2.innerHTML = "✅ <span class='text-success'>正解</span>"; }}
    else {{ fb2.innerHTML = "❌ <span class='text-danger'>不正解</span>（正答: " + ans.lq2 + ")"; }}

    if (user3 === ans.lq3) {{ correctCount++; fb3.innerHTML = "✅ <span class='text-success'>正解</span>"; }}
    else {{ fb3.innerHTML = "❌ <span class='text-danger'>不正解</span>（正答: " + ans.lq3 + ")"; }}

    document.getElementById("lq-summary").innerHTML =
      <div class='alert alert-${{correctCount === total ? "success" : "info"}} mt-3'>
       ${{total}}問中${{correctCount}}問正解！${{correctCount === total ? "🎉 Great!" : "Keep practicing!"}}
      </div>;
}}
</script>
"""

    vocab_html = "<ul class='list-unstyled'>"
    for line in vocab.strip().splitlines():
        if ":" in line:
            word, definition = line.split(":", 1)
            vocab_html += f"""
            <li class="mb-2">
                <strong>{word.strip()}</strong>: {definition.strip()}
                <details class="mt-1"><summary class="text-primary">▼ 日本語の意味を見る</summary>
                    <span class="text-muted">（ここに日本語訳を追加できます）</span>
                </details>
            </li>"""
    vocab_html += "</ul>"

    grammar_html = markdown(gp, extensions=["extra"])
    grammar_html += """
<details class="mt-2"><summary class="text-primary">▼🈁 文法の日本語補足を表示</summary>
<p class="text-muted">（ここに「現在完了進行形は“ずっと〜してきた”を表す」などを補足）</p>
</details>
"""

    jp_html = ""
    if jp.strip():
        jp_html = f"<h2>🇯🇵 日本語での経済ニュース解説</h2>\n{markdown(jp, extensions=['extra'])}"

    html = f"""
<html>
<head>
  <meta charset="utf-8">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="container my-4">

<h2>🎧 Audio</h2>
<audio controls src="{audio_url}"></audio>

<h2>📖 Script</h2>
{markdown(script, extensions=["extra"])}

<h2>📝 Vocabulary</h2>
{vocab_html}

<h2>✏️ Grammar Point</h2>
{grammar_html}

<h2>❓ Listening Questions</h2>
{markdown(lq, extensions=["extra"])}
<ol>
  <li>
    <input type="radio" name="lq1" value="True"> True<br>
    <input type="radio" name="lq1" value="False"> False<br>
    <div id="fb-lq1" class="mt-2"></div>
  </li>
  <li>
    <input type="radio" name="lq2" value="a"> a)<br>
    <input type="radio" name="lq2" value="b"> b)<br>
    <input type="radio" name="lq2" value="c"> c)<br>
    <input type="radio" name="lq2" value="d"> d)<br>
    <div id="fb-lq2" class="mt-2"></div>
  </li>
  <li>
    <input type="radio" name="lq3" value="a"> a)<br>
    <input type="radio" name="lq3" value="b"> b)<br>
    <input type="radio" name="lq3" value="c"> c)<br>
    <input type="radio" name="lq3" value="d"> d)<br>
    <div id="fb-lq3" class="mt-2"></div>
  </li>
</ol>
<button onclick="checkListening()" class="btn btn-primary mt-3">Submit</button>
<div id="lq-summary"></div>

<h2>📚 Reading Questions</h2>
{markdown(rq, extensions=["extra"])}
<ol>
  <li>
    <textarea class="form-control mb-2" rows="2"></textarea>
    <details><summary class="text-primary">🔑 解答を見る</summary>{answers[3] if len(answers) > 3 else ''}</details>
    <br><br>
  </li>
  <li>
    <textarea class="form-control mb-2" rows="2"></textarea>
    <details><summary class="text-primary">🔑 解答を見る</summary>{answers[4] if len(answers) > 4 else ''}</details>
    <br><br>
  </li>
  <li>
    <textarea class="form-control mb-2" rows="2"></textarea>
    <details><summary class="text-primary">🔑 解答を見る</summary>{answers[5] if len(answers) > 5 else ''}</details>
  </li>
</ol>

{jp_html}

<p class="text-muted">Source: <a href="{url}">{url}</a></p>

{js_script}
</body>
</html>
"""
    return html