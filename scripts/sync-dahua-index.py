#!/usr/bin/env python3
"""
同步 output/ 目录下的大白话 .md 文件到 metadata/ 的 JSON 索引中。
使用方式：
    python3 scripts/sync-dahua-index.py --subject 会计
    python3 scripts/sync-dahua-index.py --subject 会计 --dry-run  # 只检查，不写入
"""
import argparse
import json
import os
import re
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def extract_anchor_key(filename):
    """
    从文件名提取锚点键。
    文件名格式：XXX_科目-第X章-第Y节-标题.md
    提取为：科目-第X章-第Y节-标题
    """
    # 去掉前缀数字和下划线，去掉 .md 后缀
    base = os.path.basename(filename)
    # 去掉 .md 后缀
    base = base[:-3] if base.endswith('.md') else base
    # 去掉前缀的数字和下划线，如 "063_"
    match = re.match(r'^\d+_(.+)$', base)
    if match:
        return match.group(1)
    return base


def sync_subject(subject, dry_run=False):
    output_dir = os.path.join(PROJECT_ROOT, 'output', subject)
    index_path = os.path.join(PROJECT_ROOT, 'metadata', f'{subject}_大白话索引.json')

    if not os.path.exists(output_dir):
        print(f'错误: output 目录不存在: {output_dir}')
        return False

    if not os.path.exists(index_path):
        print(f'错误: 索引文件不存在: {index_path}')
        return False

    # 读取索引
    with open(index_path, 'r', encoding='utf-8') as f:
        index_data = json.load(f)

    # 扫描 output 目录
    md_files = sorted([f for f in os.listdir(output_dir) if f.endswith('.md')])

    updated = 0
    unchanged = 0
    missing_keys = []

    for md_file in md_files:
        anchor_key = extract_anchor_key(md_file)
        md_path = os.path.join(output_dir, md_file)

        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if anchor_key not in index_data:
            missing_keys.append(anchor_key)
            print(f'  ⚠️ 索引中无此键: {anchor_key} (来自 {md_file})')
            continue

        if index_data.get(anchor_key) != content:
            if not dry_run:
                index_data[anchor_key] = content
            print(f'  ✅ 已更新: {anchor_key} ({len(content)} 字节)')
            updated += 1
        else:
            unchanged += 1

    print(f'\n结果: 更新 {updated} 篇, 未变化 {unchanged} 篇, 索引缺失 {len(missing_keys)} 篇')

    if missing_keys:
        print(f'\n索引缺失的键（需要检查是否为旧键或键名不匹配）:')
        for k in missing_keys:
            print(f'  - {k}')

    if dry_run:
        print('\n🔥 dry-run 模式，未写入文件')
        return True

    # 写回索引
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    print(f'\n✅ 已保存: {index_path}')
    return True


def main():
    parser = argparse.ArgumentParser(description='同步大白话 .md 文件到 JSON 索引')
    parser.add_argument('--subject', required=True, help='科目名，如会计、审计等')
    parser.add_argument('--dry-run', action='store_true', help='只检查不写入')
    args = parser.parse_args()

    success = sync_subject(args.subject, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
