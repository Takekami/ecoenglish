from markdown import markdown

def build_blog_post_html(level, title, url, script, lq, rq, gp, audio_url):
    md = f"""
## 🎧 Audio
<audio controls src="{audio_url}"></audio>

## 📖 Script
{script}

<details><summary>Listening Questions</summary>

{lq}
</details>

<details><summary>Reading Questions</summary>

{rq}
</details>

## Grammar Point
{gp}

---

Source: [{url}]({url})
"""
    return markdown(md, extensions=["extra"])
