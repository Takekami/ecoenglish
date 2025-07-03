# blog_template.py
from markdown import markdown

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
    # Extract answers for JS validation (very basic assumption: one answer per line in order)
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
    const user2 = document.querySelector("input[name='lq2']:checked");
    const user3 = document.querySelector("input[name='lq3']:checked");

    let result = "";
    result += "1. " + (user1 === ans.lq1 ? "✅ Correct" : "❌ Incorrect (Correct: " + ans.lq1 + ")") + "<br>";
    result += "2. " + (user2?.value === ans.lq2 ? "✅ Correct" : "❌ Incorrect (Correct: " + ans.lq2 + ")") + "<br>";
    result += "3. " + (user3?.value === ans.lq3 ? "✅ Correct" : "❌ Incorrect (Correct: " + ans.lq3 + ")") + "<br>";

    document.getElementById("lq-feedback").innerHTML = result;
    }}
    </script>
    """


    md = f"""
## 🎧 Audio
<audio controls src="{audio_url}"></audio>

## 📖 Script
{script}

## 📝 Vocabulary
{vocab}

## ✏️ Grammar Point
{gp}

## ❓ Listening Questions
{lq}
<ol>
  <li>
    <input type="radio" name="lq1" value="True"> True<br>
    <input type="radio" name="lq1" value="False"> False<br>
  </li>
  <li>
    <input type="radio" name="lq2" value="a"> a)<br>
    <input type="radio" name="lq2" value="b"> b)<br>
    <input type="radio" name="lq2" value="c"> c)<br>
    <input type="radio" name="lq2" value="d"> d)<br>
  </li>
  <li>
    <input type="radio" name="lq3" value="a"> a)<br>
    <input type="radio" name="lq3" value="b"> b)<br>
    <input type="radio" name="lq3" value="c"> c)<br>
    <input type="radio" name="lq3" value="d"> d)<br>
  </li>
</ol>
<button onclick="checkListening()">Submit Answers</button>
<p id="lq-feedback"></p>

## 📚 Reading Questions
{rq}
<ol>
  <li>
    <textarea rows="2" cols="60"></textarea>
    <details><summary>🗝️ 模範解答を表示</summary>{answers[3] if len(answers) > 3 else ''}</details>
  </li>
  <li>
    <textarea rows="2" cols="60"></textarea>
    <details><summary>🗝️ 模範解答を表示</summary>{answers[4] if len(answers) > 4 else ''}</details>
  </li>
  <li>
    <textarea rows="2" cols="60"></textarea>
    <details><summary>🗝️ 模範解答を表示</summary>{answers[5] if len(answers) > 5 else ''}</details>
  </li>
</ol>

## 🇯🇵 日本語での経済ニュース解説
{jp}

---
Source: [{url}]({url})
{js_script}
"""
    return markdown(md, extensions=["extra"])
