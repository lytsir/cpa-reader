#!/usr/bin/env python3
import re
import os

anchors_sec3 = [
    "会计-第4章-第3节",
    "会计-第4章-第3节-无形资产后续计量的原则",
    "会计-第4章-第3节-估计无形资产的使用寿命",
    "会计-第4章-第3节-无形资产使用寿命的确定",
    "会计-第4章-第3节-无形资产使用寿命的复核",
    "会计-第4章-第3节-使用寿命有限的无形资产",
    "会计-第4章-第3节-摊销期和摊销方法",
    "会计-第4章-第3节-残值的确定",
    "会计-第4章-第3节-使用寿命有限的无形资产摊销的账务处理",
    "会计-第4章-第3节-使用寿命不确定的无形资产",
    "会计-第4章-第3节-无形资产的减值",
]

anchors_sec4 = [
    "会计-第4章-第4节",
    "会计-第4章-第4节-无形资产的出售",
    "会计-第4章-第4节-无形资产的报废",
]

anchors_sec5 = [
    "会计-第4章-第5节",
    "会计-第4章-第5节-无形资产的列示",
    "会计-第4章-第5节-无形资产的披露",
    "会计-第4章-第5节-关于知识产权的其他披露要求",
    "会计-第4章-第5节-关于确认为无形资产的数据资源的披露要求",
]

def extract(html_path, anchors, out_dir):
    with open(html_path, 'r', encoding='utf-8') as f:
        text = f.read()
    # Find all anchor positions
    positions = []
    for a in anchors:
        pattern = f'<div id="{a}" class="section-anchor"></div>'
        m = text.find(pattern)
        if m == -1:
            # try looser
            pattern2 = f'id="{a}"'
            m = text.find(pattern2)
            if m == -1:
                print(f"WARN: anchor not found: {a}")
                continue
        positions.append((m, a))
    positions.sort()
    
    # Extract between anchors
    for i, (pos, a) in enumerate(positions):
        if i + 1 < len(positions):
            end = positions[i+1][0]
        else:
            end = len(text)
        fragment = text[pos:end]
        # Strip HTML tags for plain text
        plain = re.sub(r'<[^>]+>', '', fragment)
        plain = re.sub(r'\n+', '\n', plain).strip()
        # Save
        safe_name = a.replace('/', '_') + '.txt'
        out_path = os.path.join(out_dir, safe_name)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(plain)
        print(f"Saved {safe_name}: {len(plain)} chars")

out_dir = "/Volumes/lyq/CPA三栏阅读器_工作区/temp_ch4_sec345"
extract("/Volumes/lyq/CPA三栏阅读器_工作区/metadata/精修片段/会计/第4章/第3节.html", anchors_sec3, out_dir)
extract("/Volumes/lyq/CPA三栏阅读器_工作区/metadata/精修片段/会计/第4章/第4节.html", anchors_sec4, out_dir)
extract("/Volumes/lyq/CPA三栏阅读器_工作区/metadata/精修片段/会计/第4章/第5节.html", anchors_sec5, out_dir)
