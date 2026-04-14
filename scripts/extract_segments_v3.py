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
    soup = BeautifulSoup(f.read(), "html.parser")

def get_heading_level(tag):
    if tag and tag.name and tag.name.startswith("h") and len(tag.name) == 2:
        try:
            return int(tag.name[1])
        except:
            pass
    return 99

def is_section_anchor(tag):
    return tag.get("class") == ["section-anchor"]

def extract_segment(anchor_id, expected_chars):
    elem = soup.find(id=anchor_id)
    if not elem:
        return None, f"未找到锚点 {anchor_id}"
    
    # 从锚点元素开始，找到实际内容起始点
    current = elem
    # 跳过空div
    while current and current.name == "div" and not current.get_text(strip=True):
        current = current.find_next_sibling()
    
    if not current:
        return None, f"锚点 {anchor_id} 后无内容"
    
    start_level = get_heading_level(current)
    content = []
    
    # 收集当前及后续兄弟
    while current:
        # 遇到下一个section-anchor，结束
        if is_section_anchor(current):
            break
        
        # 如果当前不是起始元素，且遇到同级或更高级heading，结束
        if content:
            clevel = get_heading_level(current)
            if clevel <= start_level and start_level < 99:
                break
        
        text = current.get_text(strip=True)
        if text and text not in content:
            content.append(text)
        
        current = current.find_next_sibling()
    
    full_text = "\n".join(content)
    
    # 清理：移除过短的碎片（可能是页眉页脚）
    lines = [l for l in full_text.split('\n') if len(l) > 3]
    full_text = "\n".join(lines)
    
    max_len = max(expected_chars * 3, 5000)
    if len(full_text) > max_len:
        full_text = full_text[:max_len]
    
    return full_text, None

os.makedirs(os.path.join(work_dir, "temp_segments"), exist_ok=True)
results = []
for s in selected:
    anchor_id = s["anchor"]
    text, err = extract_segment(anchor_id, s["char_count"])
    if err:
        print(f"[{s['idx']}] {s['title']} ERROR: {err}")
        results.append({"idx": s["idx"], "status": "ERROR", "error": err})
        continue
    safe_title = re.sub(r'[\\/:*?"<>|]', '_', s['title'])[:40]
    out_path = os.path.join(work_dir, "temp_segments", f"{s['idx']:04d}_{safe_title}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[{s['idx']}] {s['title']} -> {len(text)} chars (expected {s['char_count']})")
    results.append({"idx": s["idx"], "status": "OK", "chars": len(text), "path": out_path})

# 保存元数据
with open(os.path.join(work_dir, "temp_segments", "batch_meta.json"), "w", encoding="utf-8") as f:
    json.dump({
        "selected": selected,
        "results": results,
        "next_idx": selected[-1]["idx"] + 1 if selected else start_idx,
        "total_chars": total_chars
    }, f, ensure_ascii=False, indent=2)

print(f"TOTAL_SELECTED={len(selected)}")
print(f"TOTAL_CHARS={total_chars}")
print(f"NEXT_IDX={selected[-1]['idx'] + 1 if selected else start_idx}")
