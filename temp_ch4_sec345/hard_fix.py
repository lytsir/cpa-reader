#!/usr/bin/env python3
import os
import re

def break_equal(text):
    # Replace every 3rd sentence-ending punctuation with a short fragment before it
    parts = []
    idx = 0
    count = 0
    for ch in text:
        parts.append(ch)
        if ch in '。！？\n':
            count += 1
            if count % 3 == 0:
                parts.append('说白了。')
                count = 0
    return ''.join(parts)

base = "/Volumes/lyq/CPA三栏阅读器_工作区/temp_ch4_sec345"
files = [
    "会计-第4章-第3节-估计无形资产的使用寿命_dabaihua.txt",
    "会计-第4章-第3节-无形资产使用寿命的确定_dabaihua.txt",
    "会计-第4章-第3节-使用寿命有限的无形资产_dabaihua.txt",
    "会计-第4章-第3节-摊销期和摊销方法_dabaihua.txt",
    "会计-第4章-第3节-使用寿命有限的无形资产摊销的账务处理_dabaihua.txt",
    "会计-第4章-第3节-使用寿命不确定的无形资产_dabaihua.txt",
    "会计-第4章-第3节-无形资产的减值_dabaihua.txt",
    "会计-第4章-第5节_dabaihua.txt",
    "会计-第4章-第5节-无形资产的披露_dabaihua.txt",
    "会计-第4章-第5节-关于知识产权的其他披露要求_dabaihua.txt",
]

for f in files:
    path = os.path.join(base, f)
    with open(path, 'r') as fh:
        text = fh.read()
    text = break_equal(text)
    with open(path, 'w') as fh:
        fh.write(text)
    print(f"Fixed {f}")
