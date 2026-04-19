#!/usr/bin/env python3
"""
CPA大白话致命违规扫描脚本 v2
使用方法: python scripts/hard_check_dabaihua_v2.py
扫描 metadata/会计_大白话索引.json，输出所有致命错误
"""

import json
import re
import sys

BANNED_WORDS = ['讲真', '说白了', '你要知道', '简单说', '主要规范', '计算得出',
                  '如表所示', '根据相关规定', '上述', '首先', '其次', '最后']
FAKE_PEOPLE = ['老王', '小李', '小张', '小明', '小红']
STAGE_MARKERS = ['阶段一', '阶段二', '阶段三', '阶段四', '难点扫描', '具象化方案', '小白卡点']
STRUCTURAL_BOLD = ['条件翻译：', '思路拆解：', '数字推导：', '陷阱提示：',
                     '表格全貌：', '逐行解读：', '纵向逻辑：', '借：', '贷：',
                     '【题干】', '【答案】', '【分录】', '【拆解】']
GUIDE_PHRASES = ['你可能会问：', '这里容易晕：', '不少人会搞混：', '你可能会漏掉：']

def hard_check(aid, text):
    """对单篇大白话进行致命违规扫描，返回错误列表"""
    errors = []
    
    # 1. 四块结构检查
    if '## 这段到底在讲什么？' not in text:
        errors.append('缺"## 这段到底在讲什么？"')
    if '## 你可能会卡在这里' not in text:
        errors.append('缺"## 你可能会卡在这里"')
    if '## 逐一破解' not in text:
        errors.append('缺"## 逐一破解"')
    
    # 2. 子标题格式检查
    if re.search(r'(?<!#)#\s+\S', text):  # 单#标题（不含##）
        errors.append('使用了#单级标题（应改为##）')
    if '### ' in text:
        errors.append('使用了###子标题（应改为卡点N：）')
    if re.search(r'卡点[一二三四五六七八九十][：:]', text):
        errors.append('中文数字卡点（应改为阿拉伯数字）')
    
    # 3. 禁用词检查
    for word in BANNED_WORDS:
        if word in text:
            errors.append(f'禁用词：{word}')
    
    # 4. 中文数字检查（金额/数量/百分比/年限）
    chinese_nums = re.findall(
        r'[一二两三四五六七八九十百千万亿]+(?:万|亿|千|百|十)(?:元|股|份|户|张|笔|年|月|日|%|％)?',
        text
    )
    real = [n for n in chinese_nums 
            if len(n) >= 3 and any(u in n for u in ['万', '亿', '千', '百'])]
    if real:
        errors.append(f'中文数字金额：{real[:2]}')
    
    # 5. 非结构性加粗检查
    bold_matches = re.findall(r'\*\*([^*]{2,80})\*\*', text)
    for bm in bold_matches:
        is_structural = (
            any(bm.strip().startswith(s) for s in STRUCTURAL_BOLD) or
            re.match(r'【例\d+-\d+】', bm.strip())
        )
        if not is_structural:
            errors.append(f'非结构性加粗：{bm[:30]}')
            break
    
    # 6. 虚构人物检查
    for person in FAKE_PEOPLE:
        if person in text:
            errors.append(f'虚构人物：{person}')
            break
    
    # 7. 阶段标记检查
    for marker in STAGE_MARKERS:
        if marker in text:
            errors.append(f'阶段标记：{marker}')
            break
    
    # 8. 分录格式检查
    # 科目名加引号
    if re.search(r'[""][\u4e00-\u9fa5]+(?:清理|折旧|准备|损益|摊销)[""]', text):
        errors.append('分录科目名加引号')
    # 借/贷格式检查：检测是否贷方未缩进
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('贷：') and not line.startswith('    '):
            # 检查上一行是否是借方
            if i > 0 and ('借：' in lines[i-1] or '贷：' in lines[i-1]):
                errors.append('贷方未缩进')
                break
    
    # 9. 自检报告残留检查
    if '【自检报告】' in text:
        errors.append('自检报告残留（【自检报告】）')
    if '自检报告' in text and any(k in text for k in ['阶段标记', '虚构人物', '篇幅检查', '核心提炼']):
        errors.append('自检报告残留（自检报告）')
    
    # 10. Markdown表格检查
    table_lines = [l for l in text.split('\n') if l.strip().startswith('|') and l.strip().endswith('|')]
    if len(table_lines) >= 3:
        errors.append(f'Markdown表格（{len(table_lines)}行）')
    
    # 11. 段落式引导语检查
    if re.search(r'^(你可能会问|这里容易晕|不少人会搞混|你可能会漏掉)[，,：:]', text, re.MULTILINE):
        errors.append('残留段落式引导语')
    
    # 12. 英文检查（正文）
    # 简单检测：连续2个以上英文字母（专有名词除外）
    english_words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
    # 过滤掉常见专有名词（含可持续信息披露和AI审计领域）
    allowed = ['IFRS', 'GAAP', 'SPPI', 'OCI', 'FVOCI', 'FVTPL', 'HTML', 'JSON',
               'URL', 'API', 'ID', 'v3', 'vs', 'eg', 'i.e', 'e.g',
               'ESG', 'ESRS', 'ISSB', 'IPCC', 'CEO', 'OCR']
    illegal = [w for w in english_words if w not in allowed]
    if illegal:
        errors.append(f'英文混入：{illegal[:3]}')
    
    # 13. 例题四块检查（正文中提到教材例题【例X-X】时）
    # 只检查真正的教材例题编号，不检查子代理自编的【例题】
    has_real_example = re.search(r'【例\d+[-－]\d+】', text) or re.search(r'\[例\d+[-－]\d+\]', text)
    if has_real_example:
        example_blocks = ['条件翻译', '思路拆解', '数字推导', '陷阱提示']
        missing = [b for b in example_blocks if b not in text]
        if missing:
            errors.append(f'例题拆解缺块：{missing}')
    
    # 14. 表格三块检查（正文中提到表格时）
    if '表格全貌' in text or '逐行解读' in text:
        table_blocks = ['表格全貌', '逐行解读', '纵向逻辑']
        missing = [b for b in table_blocks if b not in text]
        if missing:
            errors.append(f'表格解读缺块：{missing}')
    
    # 15. 分录详解检查（正文中有分录时）
    if '借：' in text and '贷：' in text:
        # 检查是否有经济含义解释（借方/贷方/含义等关键词）
        has_explanation = any(k in text for k in ['借方', '贷方', '含义', '意思是', '表示'])
        if not has_explanation:
            errors.append('分录缺经济含义解释')
        # 检查科目名是否加引号
        if re.search(r'[""][\u4e00-\u9fa5]+(?:清理|折旧|准备|损益|摊销|减值)[""]', text):
            errors.append('分录科目名加引号')
    
    return errors


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', default='metadata/会计_大白话索引.json', help='索引文件路径')
    parser.add_argument('--chapter', default='会计-第', help='章节前缀过滤')
    args = parser.parse_args()
    
    with open(args.index, 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    total = 0
    error_count = 0
    error_details = []
    
    for aid, text in index.items():
        if not aid.startswith(args.chapter):
            continue
        total += 1
        errors = hard_check(aid, text)
        if errors:
            error_count += 1
            error_details.append((aid, errors))
    
    print(f"扫描完成：{total} 篇 | 违规 {error_count} 篇 | 通过 {total - error_count} 篇")
    print()
    
    if error_details:
        print("=" * 60)
        print("违规详情（前20篇）：")
        print("=" * 60)
        for aid, errors in error_details[:20]:
            print(f"\n{aid}")
            for e in errors:
                print(f"  ❌ {e}")
        if len(error_details) > 20:
            print(f"\n... 还有 {len(error_details) - 20} 篇")
        sys.exit(1)
    else:
        print("✅ 全部通过，0 致命违规")
        sys.exit(0)


if __name__ == '__main__':
    main()
