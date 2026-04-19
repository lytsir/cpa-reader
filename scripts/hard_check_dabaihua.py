#!/usr/bin/env python3
"""
大白话硬校验脚本 - v3（经第1章62篇验证）
命中任何一条即返回重写，不得交付

新增检查项（2026-04-19）：
- 阶段标记泄漏
- 虚构人物
- 非结构性加粗
- 中文数字（金额类）
- 禁用词扩展
- 自检报告位置
"""
import re
import sys
import json
import os

# ========== 配置项 ==========
STRUCTURAL_BOLD = [
    '条件翻译：', '思路拆解：', '数字推导：', '陷阱提示：',
    '表格全貌：', '逐行解读：', '纵向逻辑：',
    '借：', '贷：',
]

def is_structural_bold(content):
    """判断加粗内容是否是结构性标记"""
    for marker in STRUCTURAL_BOLD:
        if content.strip().startswith(marker):
            return True
    # 例编号也是结构性的
    if re.match(r'【例\d+-\d+】', content.strip()):
        return True
    if re.match(r'【例\d+-\d+详解】', content.strip()):
        return True
    return False

def check(text, original_text="", anchor_id=""):
    errors = []
    
    # 分离正文和自检报告
    report_idx = text.find('【自检报告】')
    if report_idx == -1:
        report_idx = text.find('自检报告')
    body = text[:report_idx] if report_idx > 0 else text
    report = text[report_idx:] if report_idx > 0 else ""
    
    # ===== 1. 禁用词组（原有） =====
    forbidden_patterns = [
        r'第[一二三四五六七八九十\d]+[/、,，]',
        r'首先.*其次.*最后',
        r'一是.*二是.*三是',
        r'一方面.*另一方面',
        r'还有一个方面',
        r'具体来说',
        r'综上所述',
        r'由此可见',
        r'值得注意的是',
        r'不容忽视',
        r'起到了积极作用',
        r'对于.*至关重要',
        r'真正服务好.*的发展需要',
        r'有机统一',
        r'是.*的基石',
        r'是.*的灵魂',
        r'主要规范',
        r'主要包括',
    ]
    for pat in forbidden_patterns:
        matches = re.findall(pat, body)
        if matches:
            errors.append(f"[禁用词组] 命中 '{pat}': {matches[:2]}")
    
    # ===== 2. 列表符号（原有） =====
    list_symbols = re.findall(r'[（(][1-9\d]+[）)]|[①②③④⑤⑥⑦⑧⑨⑩]|\n\d+\.', body)
    if list_symbols:
        errors.append(f"[列表符号] 发现 {len(list_symbols)} 处: {list_symbols[:5]}")
    
    # ===== 3. 义务词连发（原有） =====
    duty_words = re.findall(r'应当|不得|不能|必须|要求', body)
    if len(duty_words) >= 5:
        errors.append(f"[义务词连发] 发现 {len(duty_words)} 次义务词")
    
    # ===== 4. em dash（原有） =====
    if '—' in body:
        errors.append(f"[em dash] 发现 {body.count('—')} 处")
    
    # ===== 5. 字数不达标（原有，阈值提升到0.8） =====
    if original_text:
        orig_len = len(original_text.strip())
        dabai_len = len(body.strip())
        if orig_len > 300:
            min_ratio = 0.8
        elif orig_len > 100:
            min_ratio = 1.5
        else:
            min_ratio = 8.0
        ratio = dabai_len / orig_len if orig_len > 0 else 999
        if ratio < min_ratio:
            errors.append(f"[字数不足] 原文{orig_len}字，大白话{dabai_len}字，比例{ratio:.2%} < {min_ratio}")
    
    # ===== 6. 无比喻（原有） =====
    bijuyu_words = ['比如', '例如', '相当于', '就好比', '就像', '好比']
    if not any(w in body for w in bijuyu_words):
        errors.append("[无比喻] 全文未发现具象化比喻词")
    
    # ===== 7. 口语词密度（原有） =====
    oral_words = ['你要知道', '问题是', '不过']
    chunks = [body[i:i+150] for i in range(0, len(body), 150)]
    for i, chunk in enumerate(chunks):
        if not any(w in chunk for w in oral_words):
            # 放宽：如果片段很短或主要是例题，不报错
            if len(chunk) > 100 and '【例' not in chunk:
                errors.append(f"[口语词不足] 第{i+1}个150字片段缺少口语衔接词")
                break
    
    # ===== 8. "其实"滥用（原有） =====
    qishi_count = body.count('其实')
    if qishi_count > 3:
        errors.append(f"['其实'滥用] 出现 {qishi_count} 次")
    paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]
    for i in range(len(paragraphs) - 1):
        if paragraphs[i].startswith('其实') and paragraphs[i+1].startswith('其实'):
            errors.append("['其实'连用] 连续两段以'其实'开头")
            break
    
    # ===== 9. 教材案例关键词（原有） =====
    textbook_cases = re.findall(r'甲公司|乙公司|某企业|例如甲', body)
    if textbook_cases:
        errors.append(f"[教材案例照搬] 发现 {textbook_cases}")
    
    # ===== 10. 英文词（原有） =====
    english_words = re.findall(r'\b[a-zA-Z]{3,}\b', body)
    allowed = {'W7', 'PPP', 'CPA', 'HTML', 'JSON', 'URL', 'API'}
    illegal = [w for w in english_words if w not in allowed]
    if illegal:
        errors.append(f"[英文词] 发现: {illegal[:5]}")
    
    # ===== 新增检查项（2026-04-19） =====
    
    # 11. 阶段标记泄漏
    stage_markers = ['阶段一', '阶段二', '阶段三', '阶段四',
                     '难点扫描', '具象化方案', '小白卡点']
    for marker in stage_markers:
        if marker in body:
            errors.append(f"[阶段标记泄漏] 发现 '{marker}'")
    
    # 12. 虚构人物
    fake_people = ['老王', '小李', '小张', '小明', '小红']
    for person in fake_people:
        if person in body:
            errors.append(f"[虚构人物] 发现 '{person}'")
    
    # 13. 非结构性加粗
    bold_matches = re.findall(r'\*\*([^*]{2,80})\*\*', body)
    non_structural = [m for m in bold_matches if not is_structural_bold(m)]
    if non_structural:
        errors.append(f"[非结构性加粗] 发现 {len(non_structural)} 处: {non_structural[:3]}")
    
    # 14. 中文数字（金额类）
    # 匹配 "X万"、"X亿"、"X千" 前面的中文数字，但不匹配成语
    chinese_num_pattern = r'[一二两三四五六七八九十百千万亿]+(?:万|亿|千|百)(?:元|股|份|户|张|笔)?'
    chinese_nums = re.findall(chinese_num_pattern, body)
    # 过滤掉可能是成语的部分（长度<3或不含万/亿/千/百）
    real_chinese_nums = [n for n in chinese_nums if len(n) >= 3 and any(u in n for u in ['万', '亿', '千', '百'])]
    if real_chinese_nums:
        errors.append(f"[中文数字] 发现 {len(real_chinese_nums)} 处金额类中文数字: {real_chinese_nums[:3]}")
    
    # 15. 禁用词扩展
    extra_forbidden = ['讲真', '说白了', '上述', '计算得出', '如表所示', '根据相关规定']
    for word in extra_forbidden:
        if word in body:
            errors.append(f"[禁用词] 发现 '{word}'")
    
    # 16. 自检报告位置
    if report_idx == -1:
        errors.append("[自检报告缺失] 文件末尾未发现自检报告")
    elif report_idx < len(text) * 0.7:
        errors.append("[自检报告位置异常] 自检报告不在文件末尾（可能在正文中间）")
    
    return errors


def check_index(index_path, chapter_prefix=None):
    """扫描整个大白话索引，返回违规统计"""
    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    total = 0
    passed = 0
    failed = 0
    failed_details = []
    
    for aid, text in index.items():
        if chapter_prefix and not aid.startswith(chapter_prefix):
            continue
        
        total += 1
        errors = check(text, "", aid)
        
        if errors:
            failed += 1
            failed_details.append({
                'aid': aid,
                'errors': errors
            })
        else:
            passed += 1
    
    print(f"\n{'='*60}")
    print(f"扫描结果: 总计 {total} 篇 | 通过 {passed} 篇 | 失败 {failed} 篇")
    print(f"通过率: {passed/total*100:.1f}%" if total > 0 else "N/A")
    print(f"{'='*60}")
    
    if failed_details:
        print(f"\n❌ 违规详情（{failed} 篇）:")
        for item in failed_details[:20]:  # 最多显示20篇
            print(f"\n  {item['aid']}")
            for e in item['errors']:
                print(f"    {e}")
        if len(failed_details) > 20:
            print(f"\n  ... 还有 {len(failed_details) - 20} 篇未显示")
    
    return failed == 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python hard_check_dabaihua.py <大白话文件路径> [原文文件路径]")
        print("  python hard_check_dabaihua.py --index <索引json路径> [章节前缀]")
        sys.exit(1)
    
    # 索引扫描模式
    if sys.argv[1] == '--index':
        index_path = sys.argv[2]
        chapter_prefix = sys.argv[3] if len(sys.argv) > 3 else None
        ok = check_index(index_path, chapter_prefix)
        sys.exit(0 if ok else 1)
    
    # 单文件模式
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        text = f.read()
    
    original = ""
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            original = f.read()
    
    errors = check(text, original, sys.argv[1])
    
    if errors:
        print(f"❌ 校验失败: {sys.argv[1]}")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print(f"✅ 校验通过: {sys.argv[1]}")
        sys.exit(0)
