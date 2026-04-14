#!/usr/bin/env python3
from bs4 import BeautifulSoup
import json
import os
import sys

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
    soup = BeautifulSoup(f.read(), "html.parser")

def extract_segment(anchor_id, expected_chars):
    elem = soup.find(id=anchor_id)
    if not elem:
        return None, f"未找到锚点 {anchor_id}"
    
    content = []
    for tag in elem.find_all_next():
        tag_id = tag.get("id")
        if tag_id and tag_id != anchor_id:
            break
        if tag.name in ["p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "table", "ul", "ol", "li", "pre", "span", "b", "strong", "i"]:
            text = tag.get_text(strip=True)
            if text and text not in content:
                content.append(text)
    
    full_text = "\n".join(content)
    max_len = max(expected_chars * 2, 3000)
    if len(full_text) > max_len:
        full_text = full_text[:max_len]
    return full_text, None

# 保存提取结果
os.makedirs(os.path.join(work_dir, "temp_segments"), exist_ok=True)
for s in selected:
    anchor_id = s["anchor"]
    text, err = extract_segment(anchor_id, s["char_count"])
    if err:
        print(f"[{s['idx']}] {s['title']} ERROR: {err}")
        continue
    out_path = os.path.join(work_dir, "temp_segments", f"{s['idx']:04d}_{s['title'][:30]}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[{s['idx']}] {s['title']} -> {len(text)} chars (expected {s['char_count']})")

print(f"TOTAL_SELECTED={len(selected)}")
print(f"TOTAL_CHARS={total_chars}")
print(f"NEXT_IDX={selected[-1]['idx'] + 1 if selected else start_idx}")
