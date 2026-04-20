#!/usr/bin/env python3
"""
大白话质量自检脚本v3
覆盖宪法v2 + 用户四步要求
"""
import os, re, sys

BANNED_WORDS = ['讲真', '说白了', '你要知道', '简单说', '上述', '计算得出', '如表所示', '根据相关规定']
CONCRETE_MARKERS = ['比如', '例如', '相当于', '就好比', '好比', '就像', '打个比方']
FORMAL_WORDS = ['首先', '其次', '最后', '综上所述', '一是', '二是', '三是', '第一', '第二', '第三']
FICTION_NAMES = ['小明', '老王', '小李', '小张', '小红']

def check_file(path, original_chars):
    fname = os.path.basename(path)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    ratio = cn_chars / original_chars if original_chars else 0
    
    # 1. 结构检查
    has_jiang = '##这段到底在讲什么？' in content
    has_kan = '##你可能会卡在这里' in content
    has_po = '##逐一破解' in content
    if not has_jiang: issues.append("❌ 缺'讲什么'")
    if not has_kan: issues.append("❌ 缺'卡在哪'")
    if not has_po: issues.append("❌ 缺'逐一破解'")
    
    # 2. 卡点对应检查
    kan_lines = [l for l in content.split('\n') if l.strip().startswith('- ') and '##逐一破解' not in content[:content.index(l)]]
    po_lines = [l for l in content.split('\n') if l.strip().startswith('卡点') and '：' in l]
    if len(kan_lines) != len(po_lines):
        issues.append(f"❌ 卡点不对应: 第二步{len(kan_lines)}个, 第三步{len(po_lines)}个")
    else:
        issues.append(f"✅ 卡点对应: {len(kan_lines)}/{len(po_lines)}")
    
    # 3. 具象化检查（宪法6.3强制要求）
    concrete = [m for m in CONCRETE_MARKERS if m in content]
    concrete_count = sum(content.count(m) for m in CONCRETE_MARKERS)
    if concrete_count < len(po_lines):
        issues.append(f"❌ 具象化不足: {concrete_count}处, 要求≥{len(po_lines)}处(每卡点至少1处)")
    else:
        issues.append(f"✅ 具象化: {concrete_count}处 ({', '.join(set(concrete))})")
    
    # 4. "为什么"深度检查
    why_count = content.count('为什么')
    if why_count < len(po_lines):
        issues.append(f"❌ '为什么'不足: {why_count}次, 要求≥{len(po_lines)}次(每卡点至少1次)")
    else:
        issues.append(f"✅ '为什么': {why_count}次")
    
    # 5. 口语化检查 - 超长句
    long_sentences = []
    for sent in re.findall(r'[^。！？\n]{50,}', content):
        if len(sent) > 50 and '##' not in sent:
            long_sentences.append(sent[:40] + "...")
    if len(long_sentences) > 5:
        issues.append(f"⚠️ 超长句({len(long_sentences)}处): 建议拆分")
    else:
        issues.append(f"✅ 超长句: {len(long_sentences)}处")
    
    # 6. 书面语检查
    formal = [w for w in FORMAL_WORDS if w in content]
    if formal:
        issues.append(f"⚠️ 书面语残留: {set(formal)}")
    else:
        issues.append(f"✅ 书面语: 无")
    
    # 7. 禁用词
    found_banned = [w for w in BANNED_WORDS if w in content]
    if found_banned:
        issues.append(f"❌ 禁用词: {found_banned}")
    else:
        issues.append(f"✅ 禁用词: 无")
    
    # 8. 英文
    eng = re.findall(r'[a-zA-Z]{3,}', content)
    if eng:
        issues.append(f"❌ 英文: {eng}")
    else:
        issues.append(f"✅ 英文: 无")
    
    # 9. 虚构人物
    fiction = [w for w in FICTION_NAMES if w in content]
    if fiction:
        issues.append(f"❌ 虚构人物: {fiction}")
    else:
        issues.append(f"✅ 虚构人物: 无")
    
    # 10. 中文数字金额
    cn_amount = re.findall(r'[一二三四五六七八九十百千万亿]+(?:万|亿|千|百|十)?元', content)
    if cn_amount:
        issues.append(f"❌ 中文数字金额: {cn_amount}")
    else:
        issues.append(f"✅ 中文数字金额: 无")
    
    # 11. 长度
    if ratio < 0.8:
        issues.append(f"❌ 长度不足: {ratio:.0%} (要求≥80%)")
    else:
        issues.append(f"✅ 长度: {ratio:.0%} ({cn_chars}/{original_chars}字)")
    
    # 12. 教材顺序检查（手动标记）
    issues.append("⚠️ 教材顺序: 需人工检查是否打破原文顺序(Why→What→How)")
    
    return fname, issues, ratio

if __name__ == '__main__':
    files = {
        'output/会计/043_会计-第1章-第5节-财务报告及其编制.md': 505,
        'output/会计/044_会计-第1章-第5节-财务报告的构成.md': 418,
        'output/会计/050_会计-第1章-第5节.md': 138,
    }
    
    all_pass = True
    for path, orig in files.items():
        fname, issues, ratio = check_file(path, orig)
        print(f"\n{'='*60}")
        print(f"【{fname}】原文{orig}字 | 比例{ratio:.0%}")
        print('='*60)
        for issue in issues:
            print(f"  {issue}")
            if issue.startswith('❌'):
                all_pass = False
    
    print(f"\n{'='*60}")
    if all_pass:
        print("✅ 全部通过机械检查（仍需人工确认教材顺序和具象化质量）")
    else:
        print("❌ 存在违规项，需修复")
    print('='*60)
