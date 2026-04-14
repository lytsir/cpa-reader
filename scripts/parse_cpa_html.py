#!/usr/bin/env python3
"""
CPA教材HTML语义单元切分脚本 - v1.0
核心原则：纯代码切分，不调用LLM；原文零改动，仅插入不可见锚点
"""

import re
import json
import html
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString


def classify_heading(text):
    """
    基于文本特征对标题进行分级。
    返回: (level, type)
    level: 1=章, 2=节, 3=小节, 4=细项, 5=知识点, 99=可疑, 0=非标题
    """
    text = text.strip()
    
    # ===== 强过滤：这些绝对不是标题 =====
    # 会计分录（借/贷开头）
    if re.match(r'^(借|贷)[：:]', text):
        return 0, 'paragraph'
    # 纯金额/数字（如 "65000" "10 000 000"）
    if re.match(r'^\d[\d\s,\.]*$', text):
        return 0, 'paragraph'
    # 表格标题
    if re.match(r'^表[\d\-]+', text):
        return 0, 'paragraph'
    # 表格列头（常见于例题中的子表格）
    if text in ['第一组', '第二组', '第三组', '第四组', '第五组', '单位：元', '单位：万元']:
        return 0, 'paragraph'
    # 日期/时间标记（例题中常见）
    if re.match(r'^\d+×\d+年|\d{4}年\d+月\d+日|2×\d+年', text):
        return 0, 'paragraph'
    # 公式/等式（包含 == = 计算式）
    if '==' in text or re.match(r'^[\w\-\u4e00-\u9fa5]+\s*=\s*\d', text):
        return 0, 'paragraph'
    # 会计科目+金额（如 "银行存款 50000" "累计折旧 19200000"）
    if re.match(r'^[\u4e00-\u9fa5——\-]+\s+\d[\d\s,\.]*$', text):
        return 0, 'paragraph'
    # 表格说明行（"单位：" "资产账面价值与公允价值" 且字数<20）- 这里放宽
    if re.match(r'^单位[：:]', text) or text == '资产账面价值与公允价值':
        return 0, 'paragraph'
    # 明显是完整句子（有句号且字数>20）
    if '。' in text and len(text) > 20:
        return 0, 'paragraph'
    # 包含"应当""可以"等法规用语且较长
    if len(text) > 30 and any(w in text for w in ['应当', '可以', '不得', '必须']):
        return 0, 'paragraph'
    # 过长且无标点（可能是公式或分录被截断）
    if len(text) > 40 and not any(c in text for c in ['，', '。', '；', '、']):
        return 0, 'paragraph'
    
    # ===== 真正的标题规则 =====
    # 层级1：章
    if re.match(r'^第[一二三四五六七八九十百千零]+章', text):
        return 1, 'chapter'
    
    # 层级2：节
    if re.match(r'^第[一二三四五六七八九十百千零]+节', text):
        return 2, 'section'
    
    # 层级3：小节（一级标题）
    if re.match(r'^[一二三四五六七八九十百千零]+[、．.．]', text):
        return 3, 'subsection'
    
    # 层级4：细项（二级标题）
    if re.match(r'^[(（][一二三四五六七八九十百千零]+[)）]', text):
        return 4, 'item'
    
    # 层级5：知识点（三级标题）- 带括号的阿拉伯数字
    if re.match(r'^[(（][1234567890]+[)）]', text):
        return 5, 'point'
    
    # 层级5：带点的阿拉伯数字（如 "1. 资产的定义"）
    if re.match(r'^[1234567890]+[、．.．]', text):
        return 5, 'point'
    
    # 特殊：案例/例子标记
    if re.match(r'^\[例[\d\-]+\]|^\【例[\d\-]+\】|^案例[\d\.\-]*', text):
        return 3, 'subsection'
    
    # 异常：短文本但不像段落
    if len(text) < 50 and not text.endswith(('。', '；', '：', '!', '？', '?')):
        return 99, 'suspicious'
    
    return 0, 'paragraph'


def generate_anchor_id(subject, chapter, section, subsection):
    """生成锚点ID"""
    parts = [subject]
    if chapter:
        parts.append(chapter)
    if section:
        parts.append(section)
    if subsection:
        parts.append(subsection)
    
    anchor = '-'.join(parts)
    # 清理非法字符
    anchor = re.sub(r'[^\w\-]', '', anchor)
    anchor = re.sub(r'-+', '-', anchor)
    return anchor.strip('-')


def build_tree(elements):
    """
    基于元素列表构建章节树
    返回: (tree, flat_list, anomalies)
    """
    tree = []
    flat_list = []
    anomalies = {
        'suspicious_h1': [],
        'oversized_units': [],
        'undersized_units': [],
        'orphan_units': []
    }
    
    # 第一步：给所有元素打标签
    tagged = []
    for i, elem in enumerate(elements):
        text = elem.get_text(strip=True)
        level, tag_type = classify_heading(text)
        tagged.append({
            'index': i,
            'text': text,
            'level': level,
            'type': tag_type,
            'html': str(elem),
            'elem': elem
        })
    
    # 收集所有标题位置
    headings = [t for t in tagged if t['level'] > 0]
    
    # 构建层级上下文
    current_chapter = ""
    current_section = ""
    
    for h in headings:
        if h['level'] == 1:
            current_chapter = h['text']
            current_section = ""
        elif h['level'] == 2:
            current_section = h['text']
        
        h['chapter'] = current_chapter
        h['section'] = current_section
    
    # 第二步：按层级3（小节）作为单元起点进行聚合
    units = []
    current_unit = None
    
    for i, item in enumerate(tagged):
        if item['level'] == 1:  # 章
            # 结束当前单元
            if current_unit and current_unit['char_count'] > 0:
                units.append(current_unit)
            current_unit = {
                'start_index': i,
                'anchor': '',
                'title': item['text'],
                'level': 1,
                'chapter': item['text'],
                'section': '',
                'subsection': '',
                'content_indices': [i],
                'char_count': len(item['text']),
                'headings': [item]
            }
        elif item['level'] == 2:  # 节
            # 如果当前单元已经有足够内容，结束它
            if current_unit and current_unit['char_count'] > 800:
                units.append(current_unit)
            elif current_unit and current_unit['char_count'] > 0:
                # 内容不够，累积（把节标题加入当前单元）
                current_unit['content_indices'].append(i)
                current_unit['char_count'] += len(item['text'])
                current_unit['headings'].append(item)
                if current_unit['char_count'] > 800:
                    units.append(current_unit)
                    current_unit = None
                continue
            
            current_unit = {
                'start_index': i,
                'anchor': '',
                'title': item['text'],
                'level': 2,
                'chapter': item.get('chapter', ''),
                'section': item['text'],
                'subsection': '',
                'content_indices': [i],
                'char_count': len(item['text']),
                'headings': [item]
            }
        elif item['level'] >= 3:  # 小节及以下
            # 如果当前单元够大，结束它并开始新单元
            if current_unit and current_unit['char_count'] >= 800:
                units.append(current_unit)
                current_unit = None
            
            if current_unit is None:
                current_unit = {
                    'start_index': i,
                    'anchor': '',
                    'title': item['text'],
                    'level': item['level'],
                    'chapter': item.get('chapter', ''),
                    'section': item.get('section', ''),
                    'subsection': item['text'] if item['level'] >= 3 else '',
                    'content_indices': [i],
                    'char_count': len(item['text']),
                    'headings': [item]
                }
            else:
                current_unit['content_indices'].append(i)
                current_unit['char_count'] += len(item['text'])
                current_unit['headings'].append(item)
                # 更新主标题为最后一个小节
                current_unit['title'] = item['text']
                current_unit['subsection'] = item['text']
        else:
            # 普通内容
            if current_unit is None:
                # 孤儿内容（通常不应该出现）
                current_unit = {
                    'start_index': i,
                    'anchor': '',
                    'title': f'前文-{i}',
                    'level': 0,
                    'chapter': '',
                    'section': '',
                    'subsection': '',
                    'content_indices': [i],
                    'char_count': len(item['text']),
                    'headings': []
                }
            else:
                current_unit['content_indices'].append(i)
                current_unit['char_count'] += len(item['text'])
    
    # 收尾最后一个单元
    if current_unit and current_unit['char_count'] > 0:
        units.append(current_unit)
    
    # 后处理：合并过短单元
    merged_units = []
    for i, unit in enumerate(units):
        if unit['char_count'] < 800:
            if merged_units:
                # 并入前一个单元
                merged_units[-1]['content_indices'].extend(unit['content_indices'])
                merged_units[-1]['char_count'] += unit['char_count']
                merged_units[-1]['title'] = f"{merged_units[-1]['title']} + {unit['title']}"
            else:
                merged_units.append(unit)
        else:
            merged_units.append(unit)
    
    # 生成anchor和最终数据结构
    for unit in merged_units:
        unit['anchor'] = generate_anchor_id(
            '会计',  # 由调用方传入
            unit['chapter'],
            unit['section'],
            unit['subsection'] or unit['title']
        )
        
        # 确保anchor唯一性
        counter = 1
        base_anchor = unit['anchor']
        while any(u['anchor'] == unit['anchor'] and u is not unit for u in merged_units):
            unit['anchor'] = f"{base_anchor}-{counter}"
            counter += 1
        
        flat_list.append({
            'anchor': unit['anchor'],
            'title': unit['title'],
            'level': unit['level'],
            'char_count': unit['char_count'],
            'chapter': unit['chapter'],
            'section': unit['section'],
            'subsection': unit['subsection']
        })
        
        # 异常检测
        if unit['char_count'] > 8000:
            anomalies['oversized_units'].append({
                'anchor': unit['anchor'],
                'title': unit['title'],
                'char_count': unit['char_count']
            })
        elif unit['char_count'] < 800 and unit['level'] >= 3:
            anomalies['undersized_units'].append({
                'anchor': unit['anchor'],
                'title': unit['title'],
                'char_count': unit['char_count']
            })
    
    # 收集可疑h1
    for t in tagged:
        if t['level'] == 99:
            anomalies['suspicious_h1'].append({
                'index': t['index'],
                'text': t['text'][:80]
            })
    
    # 构建树
    tree = []
    current_chapter_node = None
    current_section_node = None
    
    for unit in merged_units:
        if unit['level'] == 1:
            current_chapter_node = {
                'title': unit['chapter'],
                'anchor': unit['anchor'],
                'children': []
            }
            tree.append(current_chapter_node)
            current_section_node = None
        elif unit['level'] == 2:
            current_section_node = {
                'title': unit['section'],
                'anchor': unit['anchor'],
                'children': []
            }
            if current_chapter_node:
                current_chapter_node['children'].append(current_section_node)
            else:
                tree.append(current_section_node)
        else:
            node = {
                'title': unit['title'],
                'anchor': unit['anchor'],
                'char_count': unit['char_count']
            }
            if current_section_node:
                current_section_node['children'].append(node)
            elif current_chapter_node:
                current_chapter_node['children'].append(node)
            else:
                tree.append(node)
    
    return tree, flat_list, anomalies, merged_units, tagged


def insert_anchors(soup, units, tagged):
    """
    在原文中插入不可见锚点标记，不改动任何原有内容
    """
    for unit in units:
        start_idx = unit['start_index']
        # 找到起始元素
        if start_idx < len(tagged):
            start_elem = tagged[start_idx]['elem']
            # 在该元素之前插入锚点
            anchor = soup.new_tag('div', **{
                'id': unit['anchor'],
                'class': 'section-anchor',
                'style': 'height:0; margin:0; padding:0; border:0;'
            })
            start_elem.insert_before(anchor)
    
    return soup


def save_results(subject, soup, tree, flat_list, anomalies, units, output_dir):
    """保存所有结果文件"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 保存带锚点的HTML
    anchored_html = str(soup)
    (output_dir / f"{subject}_带锚点.html").write_text(anchored_html, encoding='utf-8')
    
    # 2. 保存章节树JSON
    (output_dir / f"{subject}_章节树.json").write_text(
        json.dumps(tree, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    
    # 3. 保存锚点映射JSON
    (output_dir / f"{subject}_锚点映射.json").write_text(
        json.dumps(flat_list, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    
    # 4. 保存异常报告
    report_lines = [f"# {subject} 切分异常报告\n"]
    
    if anomalies['suspicious_h1']:
        report_lines.append("\n## 可疑h1标题（不符合任何标题规则但标记为h1）")
        for item in anomalies['suspicious_h1']:
            report_lines.append(f"- 行号:{item['index']} | 文本:{item['text']}")
    else:
        report_lines.append("\n## 可疑h1标题: 无")
    
    if anomalies['oversized_units']:
        report_lines.append("\n## 超长单元（>8000字）")
        for item in anomalies['oversized_units']:
            report_lines.append(f"- {item['anchor']}: {item['title'][:40]} ({item['char_count']}字)")
    else:
        report_lines.append("\n## 超长单元: 无")
    
    if anomalies['undersized_units']:
        report_lines.append("\n## 孤立短单元（<800字且无法合并）")
        for item in anomalies['undersized_units']:
            report_lines.append(f"- {item['anchor']}: {item['title'][:40]} ({item['char_count']}字)")
    else:
        report_lines.append("\n## 孤立短单元: 无")
    
    report_lines.append(f"\n## 统计\n- 总单元数: {len(units)}\n")
    
    (output_dir / f"{subject}_异常报告.md").write_text(
        '\n'.join(report_lines),
        encoding='utf-8'
    )


def main():
    import sys
    if len(sys.argv) != 3:
        print("Usage: python3 parse_cpa_html.py <subject> <html_path>")
        print("Example: python3 parse_cpa_html.py 会计 /Volumes/lyq/CPA三栏阅读器_工作区/source/会计_合并.html")
        sys.exit(1)
    
    subject = sys.argv[1]
    html_path = sys.argv[2]
    output_dir = f"/Volumes/lyq/CPA三栏阅读器_工作区/metadata"
    
    print(f"🔄 开始处理 {subject}...")
    
    # 读取并解析HTML
    html_text = Path(html_path).read_text(encoding='utf-8')
    soup = BeautifulSoup(html_text, 'html.parser')
    body = soup.find('body')
    
    # 获取所有直接子元素（我们只关心body内的顶级元素）
    elements = [elem for elem in body.children if hasattr(elem, 'name') and elem.name]
    print(f"📄 总元素数: {len(elements)}")
    
    # 构建树和单元
    tree, flat_list, anomalies, units, tagged = build_tree(elements)
    
    # 插入锚点
    soup = insert_anchors(soup, units, tagged)
    
    # 保存结果
    save_results(subject, soup, tree, flat_list, anomalies, units, output_dir)
    
    print(f"✅ 处理完成")
    print(f"   单元总数: {len(units)}")
    print(f"   可疑h1: {len(anomalies['suspicious_h1'])}")
    print(f"   超长单元: {len(anomalies['oversized_units'])}")
    print(f"   孤立短单元: {len(anomalies['undersized_units'])}")
    print(f"   输出目录: {output_dir}")


if __name__ == "__main__":
    main()
