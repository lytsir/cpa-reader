#!/usr/bin/env python3
"""
将 output/<科目>/ 下的 Markdown 大白话文件同步到 metadata/<科目>_大白话索引.json
解决索引与 Markdown 不同步的根治问题。

执行: python3 scripts/build_translate_index.py
"""

import glob
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
METADATA_DIR = os.path.join(BASE_DIR, "metadata")

SUBJECTS = ["会计", "审计", "财务成本管理", "公司战略与风险管理", "经济法", "税法"]


def build_index_for_subject(subject):
    """为单个科目构建大白话索引"""
    md_dir = os.path.join(OUTPUT_DIR, subject)
    if not os.path.isdir(md_dir):
        print(f"  跳过: {subject} 目录不存在")
        return None

    index = {}
    files = glob.glob(os.path.join(md_dir, "*.md"))

    for filepath in sorted(files):
        basename = os.path.basename(filepath)

        # 移除编号前缀，如 "001_" 或 "sec4_00_"
        name_part = re.sub(r'^\d+_', '', basename)
        name_part = re.sub(r'^sec\d+_\d+_', '', name_part)
        name_part = name_part.replace('.md', '')

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content:
            continue

        index[name_part] = content

    index_path = os.path.join(METADATA_DIR, f"{subject}_大白话索引.json")
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    return len(index)


def main():
    print("【构建大白话索引】")
    total = 0
    for subject in SUBJECTS:
        count = build_index_for_subject(subject)
        if count is not None:
            print(f"  ✅ {subject}: {count} 篇")
            total += count
    print(f"\n总计: {total} 篇")


if __name__ == '__main__':
    main()
