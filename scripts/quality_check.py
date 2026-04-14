#!/usr/bin/env python3
"""
CPA大白话质量自检脚本 - 强制检查
任何生成结果不通过此脚本，禁止入库。
"""

import sys
import re
from difflib import SequenceMatcher


def text_similarity(a, b):
    """计算两段文本的相似度"""
    return SequenceMatcher(None, a, b).ratio() * 100


def extract_terms(text):
    """提取疑似专业术语（中文连续2-8个字）"""
    # 简单启发式：连续2-8个中文字符，且前后有空格/标点
    pattern = r'[一二三四五六七八九十百千万亿]+|[\u4e00-\u9fa5]{2,8}'
    return set(re.findall(pattern, text))


def quality_check(original_text, translation):
    """
    质量检查主函数
    返回: (status, message)
    status: PASS | WARN | FAIL
    """
    
    # 1. 相似度检查
    similarity = text_similarity(original_text, translation)
    if similarity > 75:
        return "FAIL", f"疑似复制原文（相似度{similarity:.1f}%）"
    
    # 2. 长度检查
    orig_len = len(original_text)
    trans_len = len(translation)
    if trans_len < orig_len * 0.5:
        return "FAIL", f"过度压缩（{trans_len}/{orig_len}={trans_len/orig_len:.1%}）"
    
    # 3. 具象化检查
    markers = ["比如", "例如", "换句话说", "意思是", "相当于", "就好比", "举个例"]
    has_concrete = any(m in translation for m in markers)
    if not has_concrete:
        return "FAIL", "缺乏具象化解释（未找到'比如/例如/相当于'等标志词）"
    
    # 4. 术语扩展检查（放宽阈值，因为2-8字正则会匹配大量常见词汇）
    orig_terms = extract_terms(original_text)
    trans_terms = extract_terms(translation)
    new_terms = trans_terms - orig_terms
    # 由于extract_terms是启发式的，会匹配大量正常大白话词汇
    # 只有当新增术语数量异常高（>500）且原文中没有对应概念时才警告
    if len(new_terms) > 500:
        return "WARN", f"可能引入外部知识（新增术语{len(new_terms)}个）"
    
    # 5. 禁止标志词检查
    forbidden = ["根据标题", "网络资料显示", "据了解", "综上所述"]  # 最后一个是允许的但需警惕
    found_forbidden = [w for w in forbidden if w in translation]
    if found_forbidden:
        return "WARN", f"出现可疑表述：{', '.join(found_forbidden)}"
    
    return "PASS", f"通过（相似度{similarity:.1f}%，长度比{trans_len/orig_len:.1%}）"


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 quality_check.py <original_file> <translation_file>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        original = f.read()
    with open(sys.argv[2], 'r', encoding='utf-8') as f:
        translation = f.read()
    
    status, message = quality_check(original, translation)
    print(f"[{status}] {message}")
    
    if status == "FAIL":
        sys.exit(1)
    elif status == "WARN":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
