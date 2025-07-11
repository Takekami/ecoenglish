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
   • Target length: 380–420 words (B1+) / 480–540 words (B2) (~4 min audio).  
5. Add **Vocabulary** – 5 key words with:
   • Brief definition (word : meaning)  
   • One English example sentence using the word  
   • 3 common collocations (comma-separated)
6. Add **Listening Questions** – 3 items:  
   • 1 True/False question  
   • 2 Multiple Choice Questions, each with 4 options (a), b), c), d))  
   *Do not include answers.*
7. Add **Reading Questions** – 3 reading questions:
   - Detail question (Who/What/When…)
   - Inference question (Why/What do you think…)
   - Vocabulary-in-context question (meaning of a word from the script)
   *Do not provide answers.*
8. Add **Answers** – model answers for all 6 questions (just the answers).  
9. Add **Japanese Economic Insight** – approx. 300–400 characters in natural Japanese, including background, factors, domestic/international impact, and future outlook.  
10. Identify one **Grammar Point** that appears in the SCRIPT and is suitable for {level}. Provide a one-sentence explanation and quote the sentence.  
11. Add **Usage & Example** – Describe in Japanese the conversation/business context where this structure is used, and provide an English example sentence for that context.

### OUTPUT FORMAT  
```md
### Script
...

### Vocabulary
- word : meaning（日本語訳：ここに日本語訳を記載）  
  • 例文: “Here is an example sentence using the word.”  
  • Collocations: collocation1, collocation2, collocation3
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
**<Name of structure>** – “<quoted sentence>”（日本語での簡単な補足説明）

### 使用場面
(会話／ビジネスでの使いどころを日本語で記載)

### 使用例文
“例: In a business meeting, you might say: ‘If we cut costs now, we can increase our profit margin next quarter.’”

### 日本語での経済ニュース解説
...
```  
INPUT  
Headline: {title}  
Summary: {summary}  
URL: {url}
"""
