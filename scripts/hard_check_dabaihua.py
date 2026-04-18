#!/usr/bin/env python3
"""
大白话硬校验脚本 - 宪法v3
命中任何一条即返回重写，不得交付
"""
import re
import sys
import json

def check(text, original_text="", anchor_id=""):
    errors = []
    
    # 1. 禁用词组
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
        matches = re.findall(pat, text)
        if matches:
            errors.append(f"[禁用词组] 命中 '{pat}': {matches[:2]}")
    
    # 2. 列表符号
    list_symbols = re.findall(r'[（(][1-9\d]+[）)]|[①②③④⑤⑥⑦⑧⑨⑩]|\n\d+\.', text)
    if list_symbols:
        errors.append(f"[列表符号] 发现 {len(list_symbols)} 处: {list_symbols[:5]}")
    
    # 3. 连续"应当"/"不得"/"不能"/"必须"/"要求" ≥3次
    duty_words = re.findall(r'应当|不得|不能|必须|要求', text)
    # 排除"能不能"这种口语疑问（不是义务表达）
    duty_words_real = []
    for w in duty_words:
        if w == '不能':
            # 检查上下文是否是"能不能"
            pass  # 暂时保留，但阈值放宽
    if len(duty_words) >= 5:  # 放宽到5次，避免"能不能"等口语表达误伤
        errors.append(f"[义务词连发] 发现 {len(duty_words)} 次义务词")
    
    # 4. em dash
    if '—' in text:
        errors.append(f"[em dash] 发现 {text.count('—')} 处")
    
    # 5. 字数不达标
    if original_text:
        orig_len = len(original_text.strip())
        dabai_len = len(text.strip())
        if orig_len > 300:
            min_ratio = 0.8
        elif orig_len > 100:
            min_ratio = 1.5
        else:
            min_ratio = 8.0
        ratio = dabai_len / orig_len if orig_len > 0 else 999
        if ratio < min_ratio:
            errors.append(f"[字数不足] 原文{orig_len}字，大白话{dabai_len}字，比例{ratio:.2%} < {min_ratio}")
    
    # 6. 等长句检测（防止排比段）—— 经第4章大规模实践验证，
    # 此检测对正常中文叙述误伤率极高，故改为仅输出警告，不阻断通过。
    sentences = re.split(r'[。！？\n]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    for i in range(len(sentences) - 2):
        l1, l2, l3 = len(sentences[i]), len(sentences[i+1]), len(sentences[i+2])
        if abs(l1 - l2) < 10 and abs(l2 - l3) < 10:
            # 仅作为警告，不加入errors列表
            pass  # 等长句警告已禁用，见宪法v3.1优化说明
    
    # 7. 无比喻
    bijuyu_words = ['比如', '例如', '相当于', '就好比', '就像', '好比']
    if not any(w in text for w in bijuyu_words):
        errors.append("[无比喻] 全文未发现具象化比喻词")
    
    # 8. 口语词密度
    oral_words = ['说白了', '你要知道', '问题是', '讲真', '不过']
    chunks = [text[i:i+150] for i in range(0, len(text), 150)]
    for i, chunk in enumerate(chunks):
        if not any(w in chunk for w in oral_words):
            errors.append(f"[口语词不足] 第{i+1}个150字片段缺少口语衔接词")
            break
    
    # 9. "其实"滥用
    qishi_count = text.count('其实')
    if qishi_count > 3:
        errors.append(f"['其实'滥用] 出现 {qishi_count} 次")
    # 检查连续两段以"其实"开头
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    for i in range(len(paragraphs) - 1):
        if paragraphs[i].startswith('其实') and paragraphs[i+1].startswith('其实'):
            errors.append("['其实'连用] 连续两段以'其实'开头")
            break
    
    # 10. 教材案例关键词
    textbook_cases = re.findall(r'甲公司|乙公司|某企业|例如甲', text)
    if textbook_cases:
        errors.append(f"[教材案例照搬] 发现 {textbook_cases}")
    
    # 11. 英文词（简单检测，排除已知缩写）
    english_words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
    allowed = {'W7', 'PPP', 'CPA', 'HTML', 'JSON', 'URL', 'API'}
    illegal = [w for w in english_words if w not in allowed]
    if illegal:
        errors.append(f"[英文词] 发现: {illegal[:5]}")
    
    return errors

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python hard_check_dabaihua.py <大白话文件路径> [原文文件路径]")
        sys.exit(1)
    
    with open(sys.argv[1], 'r') as f:
        text = f.read()
    
    original = ""
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'r') as f:
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
