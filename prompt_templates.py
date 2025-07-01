def get_prompt_for_level(level, title, summary, url):
    return f"""
### ROLE
You are an ELT writer creating CEFR-{level} materials.

### TASK
1. Read the news headline & summary.  
2. Decide if the topic is **“economically / socially significant”** (yes / no).  
   *Say “no” for celebrity gossip etc.*  
3. If **no**, reply exactly: `SKIP`  
4. If **yes**, rewrite the summary into a {level} learner-friendly **SCRIPT**  
   (130–160 words B1+, 180–220 words B2).  
5. Add 3 **Listening Questions** (MCQ or T/F) *without answers*.  
6. Add 3 **Reading Comprehension Questions** *without answers*.  
7. Identify one **grammar point** that appears in the SCRIPT and is appropriate  
   to {level}. Give a one-sentence explanation **and quote the sentence**.

### OUTPUT FORMAT
```md
### Script
...

### Listening Questions
1.
2.
3.

### Reading Questions
1.
2.
3.

### Grammar Point
**<Name of structure>** – “<quoted sentence>”
```

### INPUT  
Headline: {title}  
Summary: {summary}  
URL: {url}
"""
