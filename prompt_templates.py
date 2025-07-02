"""
Build GPT-4o prompt for CEFR-aligned news lessons (B1+ / B2).
Returns a single markdown-specification prompt string.
"""

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
   • Target length ≈ 380‑420 words (B1+) / 480‑540 words (B2) → ~4 min audio.  
5. Add **Vocabulary** – 5 key words with brief definitions (word : meaning).  
6. Add **Listening Questions** – 3 items (MCQ or T/F) *without answers*.  
7. Add **Reading Questions** – 3 items *without answers*.  
8. Add **Answers** – model answers for all 6 questions (just the answers).  
9. Add **Japanese Economic Insight** – 2‑3 sentences (Japanese) linking the story to the wider economy / markets.  
10. Identify one **Grammar Point** that appears in the SCRIPT and is suitable for {level}. Give a one‑sentence explanation **and quote the sentence**.

### OUTPUT FORMAT  
```md
### Script
...

### Vocabulary
- word : meaning
...

### Listening Questions
1.
2.
3.

### Reading Questions
1.
2.
3.

### Answers
1.
...

### Grammar Point
**<Name of structure>** – “<quoted sentence>”

### 日本語での経済ニュース解説
...
```
INPUT  
Headline: {title}  
Summary: {summary}  
URL: {url}
"""
```