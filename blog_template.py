from markdown import markdown

def build_blog_post_html(level,title,url,script,vocab,lq,rq,ans,gp,jp,audio_url):
    md = f"""
## 🎧 Audio
<audio controls src=\"{audio_url}\"></audio>

## 📖 Script
{script}

## 📝 Vocabulary
{vocab}

## ❓ Listening Questions
{lq}

## 📚 Reading Questions
{rq}

<details><summary>解答と解説（クリックで表示）</summary>

### Answers
{ans}

### Grammar Point
{gp}

### 日本語での経済ニュース解説
{jp}

</details>

---
Source: [{url}]({url})
"""
    return markdown(md, extensions=["extra"])