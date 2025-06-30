# utils/prompt_templates.py
def get_prompt_for_level(level, title, summary, url):
    return f"""
You are an English education content generator. Your task is to create learning material for {level} learners using a current economic news article.

---
Title: {title}
Summary: {summary}
Original URL: {url}
---

Please generate the following structured content based on the article:

### Script
Rewrite or summarize the article into approximately 400 words of spoken English suitable for a CEFR {level} learner. Keep the vocabulary and grammar within the target level. Use clear and concise language. Avoid long, complex sentences. Keep the tone informative yet conversational.

### Vocabulary Notes
List 5–10 keywords or phrases with short, simple English explanations. Format:
- word: explanation

### Grammar Focus
Pick one grammar structure or phrase used in the script and briefly explain it (within {level} level understanding).

### Listening Questions
1 True/False question based on the script content
2 Multiple Choice Questions (with 3 options each)

### Reading Comprehension Questions
1 Detail question (What/Who/When...)
1 Inference question (Why/What do you think...)
1 Vocabulary question (meaning of a word in context)

### Answer Key
Provide brief answers to each question. Include a short explanation.

### Japanese Explanation
Write a short explanation in Japanese (3–5 sentences) summarizing the main point of the news and why it's economically relevant.
"""
