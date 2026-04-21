#!/usr/bin/env python3
"""
CPA大白话v3硬校验脚本（Gatekeeper）
每篇生成后必须通过此脚本校验，不通过则拒绝保存。
用法：python3 gatekeeper.py <待校验.md文件路径>
返回码：0=通过，1=不通过（stderr输出具体问题）
"""
import sys
import re

def fail(msg):
    print(f"\u274c {msg}", file=sys.stderr)
    return False

def check(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    passed = True

    # 1. 四步结构完整性
    has_step1 = re.search(r'^##\s*这段到底在讲什么？', content, re.M)
    has_step2 = re.search(r'^##\s*你可能会卡在这里', content, re.M)
    has_step3 = re.search(r'^##\s*逐一破解', content, re.M)

    if not has_step1:
        passed &= fail("缺少步骤1：##这段到底在讲什么？")
    if not has_step2:
        passed &= fail("缺少步骤2：##你可能会卡在这里")
    if not has_step3:
        passed &= fail("缺少步骤3：##逐一破解")

    # 2. 步骤2必须用"- "列表
    if has_step2:
        m = re.search(r'^##\s*你可能会卡在这里\s*\n(.*?)(?=^##|\Z)', content, re.DOTALL | re.M)
        if m:
            section = m.group(1)
            if section.strip() and '- ' not in section:
                passed &= fail("步骤2未用'- '列表")

    # 3. 步骤3格式：必须用"卡点X："分块，禁###子标题，禁中文数字
    if has_step3:
        m = re.search(r'^##\s*逐一破解\s*\n(.*?)(?=^##|\Z)', content, re.DOTALL | re.M)
        if m:
            section = m.group(1)
            if section.strip():
                if not re.search(r'卡点\d+：', section):
                    passed &= fail("步骤3未用'卡点X：'分块")
                if re.search(r'\n###\s', section):
                    passed &= fail("步骤3含###子标题")
                if re.search(r'卡点[一二三四五六七八九十]', section):
                    passed &= fail("步骤3含中文数字'卡点一'")
                if re.search(r'\*\*例[0-9-]+|\*\*分录[0-9-]+', section):
                    passed &= fail("例题/分录未从逐一破解剥离")

    # 4. 禁止Markdown表格（排除代码块）
    in_code = False
    for line in content.split('\n'):
        if line.strip().startswith('```'):
            in_code = not in_code
            continue
        if not in_code and '|' in line:
            parts = line.split('|')
            if len(parts) >= 3 and any(p.strip() for p in parts[1:-1]):
                passed &= fail(f"含Markdown表格: {line.strip()[:60]}")
                break

    # 5. 禁用词黑名单
    forbidden = ['讲真', '说白了', '你要知道', '简单说', '上述', '计算得出', '如表所示', '根据相关规定']
    for word in forbidden:
        if word in content:
            passed &= fail(f"禁用词: '{word}'")

    # 6. 分录科目不加引号
    if re.search(r'[借贷][：:][^\n]*"[^"]*"', content):
        passed &= fail("分录科目含引号")

    # 7. 金额阻断空格（分录行中）
    for line in content.split('\n'):
        if ('借' in line or '贷' in line) and re.search(r'\d\s+\d', line):
            passed &= fail(f"金额含空格: {line.strip()[:60]}")
            break

    # 8. 第四步标题规范（如有）
    step4_match = re.search(r'^##\s*(例题|表|分录)', content, re.M)
    if step4_match:
        if not re.search(r'^##例题[0-9-]+深度解析|^##表[0-9-]+深度解析', content, re.M):
            passed &= fail("第四步标题不规范（应为'例题X-X深度解析'或'表X-X深度解析'）")

    return passed

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 gatekeeper.py <filepath>", file=sys.stderr)
        sys.exit(1)

    if check(sys.argv[1]):
        print("✅ Gatekeeper 通过")
        sys.exit(0)
    else:
        sys.exit(1)
