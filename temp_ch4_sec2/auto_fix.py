# -*- coding: utf-8 -*-
import os
import re

def check_equal_length(text):
    sentences = re.split(r'[。！？\n]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    for i in range(len(sentences) - 2):
        l1, l2, l3 = len(sentences[i]), len(sentences[i+1]), len(sentences[i+2])
        if l1 > 0 and l2 > 0 and l3 > 0:
            avg = (l1 + l2 + l3) / 3
            if all(abs(len(s) - avg) / avg < 0.15 for s in [sentences[i], sentences[i+1], sentences[i+2]]):
                return i, l1, l2, l3, sentences[i], sentences[i+1], sentences[i+2]
    return None

def check_oral(text):
    oral_words = ['说白了', '你要知道', '问题是', '讲真', '不过']
    chunks = [text[i:i+150] for i in range(0, len(text), 150)]
    for i, chunk in enumerate(chunks):
        if not any(w in chunk for w in oral_words):
            return i, chunk[:50]
    return None

def check_forbidden(text):
    duty = len(re.findall(r'应当|不得|不能|必须|要求', text))
    return duty

def auto_fix(text):
    # Try to fix equal length by inserting ultra-short sentences between problematic ones
    # Replace every third 。 with 。+short_sentence+，
    # But this is risky. Instead, let's just detect and report.
    return text

# Read all files and report issues
for fname in sorted(os.listdir('temp_ch4_sec2/dabaihua')):
    if not fname.endswith('.txt'):
        continue
    path = f'temp_ch4_sec2/dabaihua/{fname}'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    el = check_equal_length(text)
    oral = check_oral(text)
    duty = check_forbidden(text)
    
    issues = []
    if el:
        i, l1, l2, l3, s1, s2, s3 = el
        issues.append(f"等长句@{i}: {l1},{l2},{l3}")
    if oral:
        issues.append(f"口语词不足@chunk{oral[0]}: {oral[1]}...")
    if duty >= 5:
        issues.append(f"义务词{duty}次")
    
    if issues:
        print(f"❌ {fname}: {' | '.join(issues)}")
    else:
        print(f"✅ {fname}")
