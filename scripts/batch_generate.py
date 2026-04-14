#!/usr/bin/env python3
"""
大白话批量生成脚本 - v1.0
按科目和章节批量生成大白话，自动质检，自动记录
"""

import os
import sys
import json
import csv
import time
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

# 读取Prompt
PROMPT_PATH = Path("/Volumes/lyq/CPA三栏阅读器_工作区/prompts/golden_prompt_v1.md")


def load_prompt():
    return PROMPT_PATH.read_text(encoding='utf-8')


def extract_segment(soup, anchor_id, next_anchor_id=None):
    """提取两个锚点之间的完整HTML片段"""
    anchor = soup.find(id=anchor_id)
    if not anchor:
        return None
    
    parts = [str(anchor)]
    current = anchor.next_sibling
    while current:
        if hasattr(current, 'get') and current.get('class') == ['section-anchor']:
            if next_anchor_id and current.get('id') == next_anchor_id:
                break
            elif not next_anchor_id:
                break
        if hasattr(current, 'name') and current.name:
            parts.append(str(current))
        current = current.next_sibling
    
    return '\n'.join(parts)


def call_llm(prompt):
    """调用LLM生成大白话。这里使用当前session的模型接口"""
    # 实际运行时通过 hermes 工具调用
    # 但为了脚本可独立运行，我们使用环境变量或stdin/stdout模式
    # 简化版：打印prompt到stdout，由外部收集结果
    # 更好的方式：直接import并使用当前AI的能力
    
    # 由于这个脚本在独立Python进程中运行，没有直接访问hermes LLM的通道
    # 方案：将请求写入文件，由主进程读取后调用LLM，再写回文件
    raise NotImplementedError(
        "batch_generate.py 需要在Hermes session中由AI代理直接执行，\n"
        "或者通过环境变量配置外部API（如OPENAI_API_KEY）。\n"
        "在当前架构下，建议由Hermes直接逐条调用生成工具。"
    )


def quality_check(original_text, translation):
    """内嵌质量检查（简化版）"""
    from difflib import SequenceMatcher
    
    similarity = SequenceMatcher(None, original_text, translation).ratio() * 100
    if similarity > 75:
        return False, f"相似度{similarity:.1f}%"
    
    if len(translation) < len(original_text) * 0.5:
        return False, f"过度压缩{len(translation)/len(original_text):.1%}"
    
    markers = ["比如", "例如", "换句话说", "意思是", "相当于", "就好比", "举个例"]
    if not any(m in translation for m in markers):
        return False, "缺乏具象化"
    
    return True, f"通过（相似度{similarity:.1f}%）"


def update_tracking(subject, anchor, title, char_count, status, note=""):
    """更新任务跟踪表"""
    tracking_path = Path("/Volumes/lyq/CPA三栏阅读器_工作区/TASK_TRACKING.csv")
    rows = []
    found = False
    
    if tracking_path.exists():
        with open(tracking_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    
    for row in rows:
        if row['科目'] == subject and row['单元标题'] == title:
            row['状态'] = status
            row['生成时间'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            row['备注'] = note
            found = True
            break
    
    if not found:
        # 解析chapter/section从anchor
        parts = anchor.split('-')
        chapter = parts[2] if len(parts) > 2 else ''
        section = parts[3] if len(parts) > 3 else ''
        rows.append({
            '科目': subject,
            '章': chapter,
            '节': section,
            '单元标题': title,
            '字数': str(char_count),
            '状态': status,
            '生成时间': datetime.now().strftime('%Y-%m-%d %H:%M'),
            '质量抽查': '',
            '备注': note
        })
    
    with open(tracking_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['科目','章','节','单元标题','字数','状态','生成时间','质量抽查','备注'])
        writer.writeheader()
        writer.writerows(rows)


def main():
    """
    由于batch_generate.py需要调用LLM，而独立Python进程无法直接访问Hermes的模型接口，
    这个脚本目前主要提供工具函数。实际的批量生成由Hermes AI代理直接执行。
    """
    print("📘 batch_generate.py 提供以下功能：")
    print("  - extract_segment(): 从带锚点的HTML中提取原文片段")
    print("  - quality_check(): 大白话质量快速检查")
    print("  - update_tracking(): 更新TASK_TRACKING.csv")
    print("")
    print("💡 实际批量生成请通过Hermes会话直接调用")


if __name__ == "__main__":
    main()
