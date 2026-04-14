#!/usr/bin/env python3
from bs4 import BeautifulSoup
import json
import os
import sys
import re

work_dir = "/Volumes/lyq/CPA三栏阅读器_工作区"

with open(os.path.join(work_dir, "metadata/会计_锚点映射.json"), "r", encoding="utf-8") as f:
    anchors = json.load(f)

start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 123

selected = []
total_chars = 0
for i in range(start_idx, len(anchors)):
    anchor = anchors[i]
    char_count = anchor["char_count"]
    if total_chars + char_count > 15000 and len(selected) >= 5:
        break
    selected.append({"idx": i, **anchor})
    total_chars += char_count
    if len(selected) >= 10:
        break

html_path = os.path.join(work_dir, "metadata/会计_带锚点.html")
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

def get_heading_level(tag):
    if tag and tag.name and tag.name.startswith("h") and len(tag.name) == 2:
        try:
            return int(tag.name[1])
        except:
            pass
    return 99

def extract_segment(anchor_id, expected_chars):
    elem = soup.find(id=anchor_id)
    if not elem:
        return None, f"未找到锚点 {anchor_id}"
    
    # 如果elem是空div（用于锚点定位），取它的下一个有效元素
    if elem.name == "div" and not elem.get_text(strip=True):
        elem = elem.find_next_sibling()
        if not elem:
            return None, f"锚点 {anchor_id} 后无内容"
    
    start_level = get_heading_level(elem)
    content = []
    
    # 先加入当前元素
    text = elem.get_text(strip=True)
    if text:
        content.append(text)
    
    # 遍历后续兄弟元素
    for sibling in elem.find_next_siblings():
        sid = sibling.get("id")
        if sid and sid != anchor_id:
            # 遇到另一个锚点，结束
            break
        
        slevel = get_heading_level(sibling)
        if slevel <= start_level and start_level < 99:
            # 遇到同级或更高级标题，结束
            break
        
        # 提取文本
        stext = sibling.get_text(strip=True)
        if stext and stext not in content:
            content.append(stext)
    
    full_text = "\n".join(content)
    # 如果内容太少，可能是嵌套结构，尝试从父元素提取
    if len(full_text) < expected_chars * 0.3:
        # 尝试在elem之后找所有内容直到下一个id
        content2 = [text]
        for tag in elem.find_all_next():
            tid = tag.get("id")
            if tid and tid != anchor_id:
                break
            ttext = tag.get_text(strip=True)
            if ttext and ttext not in content2:
                content2.append(ttext)
        full_text = "\n".join(content2)
    
    max_len = max(expected_chars * 3, 5000)
    if len(full_text) > max_len:
        full_text = full_text[:max_len]
    
    return full_text, None

os.makedirs(os.path.join(work_dir, "temp_segments"), exist_ok=True)
for s in selected:
    anchor_id = s["anchor"]
    text, err = extract_segment(anchor_id, s["char_count"])
    if err:
        print(f"[{s['idx']}] {s['title']} ERROR: {err}")
        continue
    safe_title = re.sub(r'[\\/:*?"<>|]', '_', s['title'])[:40]
    out_path = os.path.join(work_dir, "temp_segments", f"{s['idx']:04d}_{safe_title}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[{s['idx']}] {s['title']} -> {len(text)} chars (expected {s['char_count']})")

print(f"TOTAL_SELECTED={len(selected)}")
print(f"TOTAL_CHARS={total_chars}")
print(f"NEXT_IDX={selected[-1]['idx'] + 1 if selected else start_idx}")
