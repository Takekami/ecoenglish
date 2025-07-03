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

## 📚 Reading Questions
{rq}

<details><summary>🗝️ 解答（クリックで表示）</summary>

{ans}

</details>

## 🇯🇵 日本語での経済ニュース解説
{jp}

---
Source: [{url}]({url})
"""
    # Python-Markdown で <details> を維持するために "extra" 拡張を使う
    return markdown(md, extensions=["extra"])