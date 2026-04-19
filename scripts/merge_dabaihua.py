#!/usr/bin/env python3
"""
合并大白话v2文件到索引，自动清理阶段标记混入。
作为数据管道的最后一道防线。
"""
import json
import os
import re
import sys

STAGE_MARKERS = [
    r'#+\s*阶段[一二三四][：:\s].*?\n',
    r'#+\s*第[1234]阶段.*?\n',
    r'#+\s*难点扫描.*?\n',
    r'#+\s*具象化方案.*?\n',
    r'#+\s*自检.*?\n',
    r'#+\s*小白卡点.*?\n',
    r'\*\*阶段[一二三四].*?\*\*\n+',
    r'\*\*难点扫描.*?\*\*\n+',
    r'\*\*具象化方案.*?\*\*\n+',
    r'【阶段[一二三四].*?】\n+',
    r'【难点扫描[^】]*】\n+',
    r'【具象化方案[^】]*】\n+',
    r'【自检[^】]*】\n+',
    r'【小白卡点[^】]*】\n+',
    r'阶段[一二三四][：:\s].*?\n+',
    r'---\n+阶段[一二三四].*?\n+',
    r'---\n+自检报告.*?\n+',
    r'---\n+【?自检.*?】?.*$',
]

# 允许保留的加粗模式（结构性标记）
KEEP_BOLD_PATTERNS = [
    r'条件翻译[：:]',
    r'思路拆解[：:]',
    r'数字推导[：:]',
    r'陷阱提示[：:]',
    r'表格全貌[：:]',
    r'逐行解读[：:]',
    r'纵向逻辑[：:]',
    r'借[：:]',
    r'贷[：:]',
    r'例\d+[-－]\d+',
    r'【例',
]


def clean_stages(text):
    """清理所有阶段标记"""
    original = text
    for pattern in STAGE_MARKERS:
        text = re.sub(pattern, '\n', text, flags=re.DOTALL)
    # 清理表格中的自检行
    text = re.sub(r'\|[^\n]*开头有难点扫描[^\n]*\|\n?', '', text)
    text = re.sub(r'\|[^\n]*自检[^\n]*\|\n?', '', text)
    text = re.sub(r'\|[-:]+\|\n?', '', text)
    # 清理多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def clean_bold(text):
    """清理非结构性的加粗"""
    def replacer(m):
        content = m.group(1)
        for pattern in KEEP_BOLD_PATTERNS:
            if re.search(pattern, content):
                return m.group(0)  # 保留结构性标记
        return content  # 去除加粗，保留内容
    return re.sub(r'\*\*([^*]+)\*\*', replacer, text)


def extract_body(content):
    """从v2文件中提取正文（去掉锚点ID行和自检报告）"""
    lines = content.split('\n')
    # 找到锚点ID行之后
    start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('锚点ID:'):
            start_idx = i + 1
            break
    # 找到自检报告开始的位置
    end_idx = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith('【自检报告】') or lines[i].startswith('自检报告') or '自检' in lines[i]:
            end_idx = i
            break
    body = '\n'.join(lines[start_idx:end_idx]).strip()
    body = clean_stages(body)
    body = clean_bold(body)
    return body


def merge_files(index_path, v2_files):
    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)

    updated = 0
    cleaned = 0
    for aid, path in v2_files:
        if not os.path.exists(path):
            print(f'❌ 不存在: {path}')
            continue
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        body = extract_body(content)

        # 检查是否清理了标记
        has_markers = any(marker in body for marker in ['阶段一', '阶段二', '阶段三', '难点扫描', '具象化方案'])
        if has_markers:
            print(f'⚠ 清理后仍有标记残留: {aid}')

        if aid in index:
            old_len = len(index[aid])
            new_len = len(body)
            if body != index[aid]:
                index[aid] = body
                updated += 1
                print(f'✓ {aid[:50]}...: {old_len}字 → {new_len}字')
        else:
            print(f'⚠ 索引中不存在: {aid[:50]}')

    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f'\n已更新 {updated} 篇')
    return updated


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python merge_dabaihua.py <index.json> <v2_file1> <v2_file2> ...')
        sys.exit(1)

    index_path = sys.argv[1]
    v2_files = []
    for arg in sys.argv[2:]:
        # 解析 "aid:path" 格式
        if ':' in arg:
            aid, path = arg.split(':', 1)
            v2_files.append((aid, path))
        else:
            # 从文件名推断aid
            basename = os.path.basename(arg)
            aid = basename.replace('_大白话_v2.md', '').replace('_', '-')
            v2_files.append((aid, arg))

    merge_files(index_path, v2_files)
