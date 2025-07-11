def get_prompt_for_level(level: str, title: str, summary: str, url: str) -> str:
    return f"""
### ROLE
You are an ELT writer creating CEFR-{level} materials.

### TASK
1. Read the news headline & summary.
2. Decide if the topic is **“economically / socially significant”** (yes / no).  
   *Say “no” for celebrity gossip etc.*
3. If **no**, reply exactly: `SKIP`  
4. If **yes**, rewrite the summary into a {level} learner‑friendly **SCRIPT**  
   • Target length ≈ 380 ‑420 words (B1+) / 480 ‑540 words (B2) → ~4 min audio.  
5. Add **Vocabulary** – 5 key words with brief definitions (word : meaning).  
6. Add **Listening Questions** – 3 items:  
   • 1 True/False question  
   • 2 Multiple Choice Questions, each with 4 options (a), b), c), d))  
   *Do not include answers.*
7. Add **Reading Questions** – 3 reading questions:
- 1 Detail question (Who/What/When…)
- 1 Inference question (Why/What do you think…)
- 1 Vocabulary-in-context question (meaning of a word from the script)
Do not provide answers.
8. Add **Answers** – model answers for all 6 questions (just the answers).  
9. Add **Japanese Economic Insight** – **約300～400字**で、記事の背景・要因・国内外への影響・今後の見通しなどを含め、自然な日本語でしっかり深掘りした解説。
10. Identify one **Grammar Point** that appears in the SCRIPT and is suitable for {level}. Give a one‑sentence explanation **and quote the sentence**.

### OUTPUT FORMAT  
```md
### Script
...

### Vocabulary
- word : meaning（日本語訳：ここに日本語訳を記載）
...

### Listening Questions
1. True/False:
2. MCQ:
    a) ...
    b) ...
    c) ...
    d) ...
3. MCQ:
    a) ...
    b) ...
    c) ...
    d) ...

### Reading Questions
1.
2.
3.

### Answers
1.
...

### Grammar Point
**<Name of structure>** – “<quoted sentence>”（ここに一文で文法ポイントの日本語補足を記載）

### 日本語での経済ニュース解説
...
```
INPUT  
Headline: {title}  
Summary: {summary}  
URL: {url}
"""
