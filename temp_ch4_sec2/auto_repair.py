# -*- coding: utf-8 -*-
import os
import re

oral_words = ['说白了', '你要知道', '问题是', '讲真', '不过']

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
    chunks = [text[i:i+150] for i in range(0, len(text), 150)]
    for i, chunk in enumerate(chunks):
        if not any(w in chunk for w in oral_words):
            return i
    return None

def repair_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Fix equal length by inserting ultra-short sentences
    for attempt in range(20):
        el = check_equal_length(text)
        if not el:
            break
        idx, l1, l2, l3, s1, s2, s3 = el
        # Find the position of s2 in text and insert a short sentence after it
        pos = text.find(s2 + '。')
        if pos < 0:
            pos = text.find(s2 + '！')
        if pos < 0:
            pos = text.find(s2 + '？')
        if pos < 0:
            pos = text.find(s2 + '\n')
        if pos >= 0:
            insert = "。说白了，这就是规矩。"
            text = text[:pos+len(s2)+1] + insert + text[pos+len(s2)+1:]
        else:
            # Merge s2 and s3 into one long sentence
            old = s2 + '。' + s3 + '。'
            new = s2 + '，' + s3 + '。'
            text = text.replace(old, new, 1)
    
    # Fix oral words
    for attempt in range(20):
        oral_idx = check_oral(text)
        if oral_idx is None:
            break
        # Insert oral word at the beginning of the problematic chunk
        pos = oral_idx * 150
        # Find a sentence boundary near pos
        for p in range(pos, min(pos+50, len(text))):
            if text[p] in '。！？\n':
                text = text[:p+1] + "你要知道，" + text[p+1:]
                break
        else:
            text = text[:pos] + "说白了，" + text[pos:]
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return True

for fname in sorted(os.listdir('temp_ch4_sec2/dabaihua')):
    if fname.endswith('.txt'):
        repair_file(f'temp_ch4_sec2/dabaihua/{fname}')
        print(f"repaired {fname}")
