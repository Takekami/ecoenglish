# utils/blog_template.py
def build_blog_post_html(content, audio_url, level):
    # Extract content sections
    sections = {}
    current = None
    for line in content.splitlines():
        if line.startswith("### "):
            current = line.replace("### ", "").strip()
            sections[current] = []
        elif current:
            sections[current].append(line)

    def section_html(title, body):
        return f"""
<h2>{title}</h2>
<p>{'<br>'.join(body)}</p>
"""

    def qa_accordion(title, questions):
        html = f"<h3>{title}</h3>\n"
        for i, q in enumerate(questions):
            html += f"""
<details>
<summary>Q{i+1}</summary>
<p>{q}</p>
</details>
"""
        return html

    html_parts = []

    # Title and audio
    html_parts.append(f"<h1>{level} 英語ニュース教材</h1>")
    html_parts.append(f"<audio controls><source src=\"{audio_url}\" type=\"audio/mpeg\"></audio>")

    # Script
    html_parts.append(section_html("Script（スクリプト）", sections.get("Script", [])))
    
    # Vocabulary
    html_parts.append(section_html("Vocabulary（単語解説）", sections.get("Vocabulary Notes", [])))

    # Grammar
    html_parts.append(section_html("Grammar Point（文法ポイント）", sections.get("Grammar Focus", [])))

    # Listening Questions
    html_parts.append(section_html("Listening Questions（リスニング問題）", sections.get("Listening Questions", [])))

    # Reading Questions
    html_parts.append(section_html("Reading Questions（読解問題）", sections.get("Reading Comprehension Questions", [])))

    # Answer Key（折りたたみ）
    html_parts.append(qa_accordion("解答と解説（クリックで表示）", sections.get("Answer Key", [])))

    # Japanese Explanation
    html_parts.append(section_html("日本語での経済ニュース解説", sections.get("Japanese Explanation", [])))

    return "\n".join(html_parts)