#!/usr/bin/env python3
"""
进度检查脚本v2 - 以索引为准，不再只看文件系统
读取 metadata/会计_语义锚点映射.json 和 metadata/会计_大白话索引.json
统计真实完成进度
"""

import json
import os
import sys

def check_progress(subject="会计"):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 读取语义锚点映射
    mapping_path = os.path.join(base_dir, f'metadata/{subject}_语义锚点映射.json')
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    # 读取大白话索引
    index_path = os.path.join(base_dir, f'metadata/{subject}_大白话索引.json')
    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    # 统计
    total = len(mapping)
    done = 0
    missing = []
    
    chapter_stats = {}
    
    for item in mapping:
        anchor_id = item['anchor_id']
        chapter = item.get('chapter', '')
        
        if chapter not in chapter_stats:
            chapter_stats[chapter] = {'total': 0, 'done': 0}
        chapter_stats[chapter]['total'] += 1
        
        if anchor_id in index and len(index[anchor_id]) > 50:
            done += 1
            chapter_stats[chapter]['done'] += 1
        else:
            missing.append(anchor_id)
    
    # 输出
    print(f"\n{'='*60}")
    print(f"📊 {subject} 大白话进度检查（以索引为准）")
    print(f"{'='*60}")
    print(f"总锚点数: {total}")
    print(f"已完成: {done} ({done/total*100:.1f}%)")
    print(f"待补齐: {total - done}")
    
    if missing:
        print(f"\n缺失列表（前20个）:")
        for m in missing[:20]:
            print(f"  - {m}")
    
    print(f"\n按章统计:")
    for ch in sorted(chapter_stats.keys(), key=lambda x: int(x.replace('第','').replace('章','')) if x.startswith('第') else 999):
        s = chapter_stats[ch]
        print(f"  {ch}: {s['done']}/{s['total']} ({s['done']/s['total']*100:.1f}%)")
    
    print(f"{'='*60}\n")
    
    return done, total, missing

if __name__ == '__main__':
    subject = sys.argv[1] if len(sys.argv) > 1 else "会计"
    check_progress(subject)
