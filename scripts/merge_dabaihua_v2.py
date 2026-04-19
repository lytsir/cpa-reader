#!/usr/bin/env python3
"""
CPA大白话合并脚本 v2
功能：
1. 从 temp_第X章/ 读取大白话v3文件
2. 自动清洗（自检报告/阶段标记/虚构人物/中文数字/表格/引导语/加粗）
3. 合并到 metadata/会计_大白话索引.json
4. 自动确保四块结构

使用方法: python scripts/merge_dabaihua_v2.py 第3章
"""

import json
import os
import re
import sys
import glob

try:
    import cn2an
    HAS_CN2AN = True
except ImportError:
    HAS_CN2AN = False
    print("警告：未安装 cn2an，中文数字转换功能受限")


# ===== 清洗规则 =====

SELF_REPORT_MARKERS = ['【自检报告】', '自检报告', '---自检报告']
STAGE_MARKERS = ['阶段一', '阶段二', '阶段三', '阶段四', '难点扫描', '具象化方案', '小白卡点']
FAKE_PEOPLE = ['老王', '小李', '小张', '小明', '小红']
GUIDE_PHRASES = ['你可能会问：', '这里容易晕：', '不少人会搞混：', '你可能会漏掉：']
BANNED_WORDS = {'讲真': '实际上', '说白了': '也就是说', '你要知道': '', '简单说': '概括来说',
                '主要规范': '', '计算得出': '', '如表所示': '从表中可以看出'}
STRUCTURAL_BOLD = ['条件翻译：', '思路拆解：', '数字推导：', '陷阱提示：',
                     '表格全貌：', '逐行解读：', '纵向逻辑：', '借：', '贷：',
                     '【题干】', '【答案】', '【分录】', '【拆解】']


def strip_self_report(text):
    """剥离自检报告"""
    for marker in SELF_REPORT_MARKERS:
        idx = text.find(marker)
        if idx > 0:
            text = text[:idx].rstrip()
    return text


def clean_stage_markers(text):
    """清理阶段标记"""
    for marker in STAGE_MARKERS:
        text = text.replace(marker, '')
    return text


def clean_fake_people(text):
    """清理虚构人物"""
    for person in FAKE_PEOPLE:
        text = text.replace(person, '')
    return text


def clean_banned_words(text):
    """清理禁用词"""
    for word, replacement in BANNED_WORDS.items():
        text = text.replace(word, replacement)
    return text


def clean_guide_phrases(text):
    """清理段落式引导语"""
    for phrase in GUIDE_PHRASES:
        text = text.replace(phrase, '')
    return text


def convert_chinese_numbers(text):
    """中文数字→阿拉伯数字（金额/数量/百分比）"""
    if HAS_CN2AN:
        # 使用cn2an转换金额
        def replace_amount(match):
            cn = match.group(0)
            try:
                # 尝试转换
                num = cn2an.cn2an(cn.replace('元', '').replace('股', '').replace('份', ''), 'smart')
                unit = ''
                for u in ['万元', '亿元', '千元', '百元', '元', '股', '份']:
                    if cn.endswith(u):
                        unit = u
                        break
                return f"{num}{unit}"
            except:
                return cn
        
        # 匹配金额模式
        text = re.sub(r'[一二两三四五六七八九十百千万亿]+(?:万|亿|千|百|十)(?:元|股|份|户|张|笔)?',
                      replace_amount, text)
    return text


def convert_tables(text):
    """Markdown表格→文字列表"""
    lines = text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('|') and line.strip().endswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                table_lines.append(lines[i])
                i += 1
            
            if len(table_lines) >= 3:
                header = [c.strip() for c in table_lines[0].split('|')[1:-1]]
                data_rows = []
                for row in table_lines[2:]:
                    cells = [c.strip() for c in row.split('|')[1:-1]]
                    if len(cells) == len(header):
                        data_rows.append(cells)
                
                if len(header) == 2 and data_rows:
                    items = [f"{j+1}. {row[0]}——{row[1]}" for j, row in enumerate(data_rows)]
                    result.append('\n'.join(items))
                elif len(header) == 3 and data_rows:
                    items = [f"{j+1}. {row[0]}：{row[1]}，{row[2]}" for j, row in enumerate(data_rows)]
                    result.append('\n'.join(items))
                elif data_rows:
                    items = []
                    for j, row in enumerate(data_rows):
                        item_text = '，'.join([f"{header[k]}：{row[k]}" for k in range(min(len(header), len(row)))])
                        items.append(f"{j+1}. {item_text}")
                    result.append('\n'.join(items))
                continue
        
        result.append(line)
        i += 1
    
    return '\n'.join(result)


def clean_nonstructural_bold(text):
    """清理非结构性加粗"""
    bold_matches = list(re.finditer(r'\*\*([^*]{2,80})\*\*', text))
    for match in reversed(bold_matches):
        bm = match.group(1)
        is_structural = (
            any(bm.strip().startswith(s) for s in STRUCTURAL_BOLD) or
            re.match(r'【例\d+-\d+】', bm.strip())
        )
        if not is_structural:
            text = text[:match.start()] + bm + text[match.end():]
    return text


def ensure_structure(text):
    """确保四块结构"""
    # 如果有"## 这段到底在讲什么？"但缺其他结构，尝试修复
    if '## 这段到底在讲什么？' in text:
        if '## 你可能会卡在这里' not in text:
            # 提取问题句作为卡点列表
            questions = []
            for q in re.findall(r'([^\n。]*？)', text):
                q = q.strip()
                if 10 < len(q) < 80 and ('什么' in q or '为什么' in q or '怎么' in q):
                    questions.append(q)
            seen = set()
            unique_q = []
            for q in questions:
                if q not in seen:
                    seen.add(q)
                    unique_q.append(q)
            if unique_q:
                kadian = '\n'.join(f'- {q}' for q in unique_q[:4])
                text = re.sub(r'(## 这段到底在讲什么？[\s\S]+?)(\n\n## 逐一破解|\n\n逐一破解)',
                              lambda m: m.group(1) + '\n\n## 你可能会卡在这里\n\n' + kadian + '\n\n' + m.group(2).replace('逐一破解', '## 逐一破解'),
                              text)
        
        if '## 逐一破解' not in text:
            text = re.sub(r'(## 你可能会卡在这里[\s\S]+?)(?=\n\n## |\Z)',
                          lambda m: m.group(1) + '\n\n## 逐一破解\n\n卡点1：核心要点\n\n',
                          text)
    
    return text


def clean_v3(text):
    """完整清洗流水线"""
    text = strip_self_report(text)
    text = clean_stage_markers(text)
    text = clean_fake_people(text)
    text = clean_banned_words(text)
    text = clean_guide_phrases(text)
    text = convert_chinese_numbers(text)
    text = convert_tables(text)
    text = clean_nonstructural_bold(text)
    text = ensure_structure(text)
    
    # 清理多余空行
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r'\n{3}', '\n\n', text)
    text = text.strip()
    
    return text


def merge_chapter(chapter_name):
    """合并指定章节的大白话到索引"""
    dir_path = f'/Volumes/lyq/CPA三栏阅读器_工作区/temp_{chapter_name}'
    if not os.path.exists(dir_path):
        print(f"错误：目录不存在 {dir_path}")
        return
    
    with open('/Volumes/lyq/CPA三栏阅读器_工作区/metadata/会计_大白话索引.json', 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    updated = 0
    added = 0
    
    # 收集该章节的v3文件（去重：取最大文件）
    v3_files = {}
    for f in os.listdir(dir_path):
        if not f.endswith('_大白话_v3.md'):
            continue
        base = f.replace('_大白话_v3.md', '')
        aid = base.replace('_', '-')
        path = os.path.join(dir_path, f)
        if aid not in v3_files or os.path.getsize(path) > os.path.getsize(v3_files[aid][1]):
            v3_files[aid] = (f, path)
    
    for aid, (fname, path) in v3_files.items():
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取正文（去掉锚点ID行）
        lines = content.split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('锚点ID:'):
                start_idx = i + 1
                break
        
        body = '\n'.join(lines[start_idx:]).strip()
        
        # 清洗
        body = clean_v3(body)
        
        if aid in index:
            index[aid] = body
            updated += 1
        else:
            index[aid] = body
            added += 1
    
    with open('/Volumes/lyq/CPA三栏阅读器_工作区/metadata/会计_大白话索引.json', 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {chapter_name} 合并完成：更新 {updated} 篇 | 新增 {added} 篇")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python scripts/merge_dabaihua_v2.py 第3章")
        sys.exit(1)
    
    chapter = sys.argv[1]
    merge_chapter(chapter)
