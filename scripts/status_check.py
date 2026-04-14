#!/usr/bin/env python3
"""
项目状态检查脚本 - 每次session开始时运行
"""

import os
import glob
from pathlib import Path

BASE_DIR = Path("/Volumes/lyq/CPA三栏阅读器_工作区")


def count_output_files(subject):
    pattern = BASE_DIR / "output" / subject / "*.md"
    return len(glob.glob(str(pattern)))


def check_source_files():
    source_dir = BASE_DIR / "source"
    files = {
        "会计_合并.html": source_dir / "会计_合并.html",
        "审计_合并.html": source_dir / "审计_合并.html",
        "税法_合并.html": source_dir / "税法_合并.html",
        "财管.html": source_dir / "财管.html",
        "经济法.html": source_dir / "经济法.html",
        "战略.html": source_dir / "战略.html",
    }
    result = {}
    for name, path in files.items():
        if path.exists():
            size_mb = path.stat().st_size / 1024 / 1024
            result[name] = f"✅ {size_mb:.1f}MB"
        else:
            result[name] = "❌ 缺失"
    return result


def main():
    print("=" * 60)
    print("📊 CPA三栏阅读器 项目状态检查")
    print("=" * 60)
    
    # 1. 检查项目宪法
    constitution = BASE_DIR / "PROJECT_CONSTITUTION.md"
    if constitution.exists():
        print("\n✅ 项目宪法: 已建立")
    else:
        print("\n❌ 项目宪法: 缺失")
    
    # 2. 检查源文件
    print("\n📚 源文件状态:")
    for name, status in check_source_files().items():
        print(f"  {name}: {status}")
    
    # 3. 检查输出进度
    print("\n📝 大白话生成进度:")
    subjects = ["会计", "审计", "税法", "财管", "经济法", "战略"]
    for subject in subjects:
        count = count_output_files(subject)
        print(f"  {subject}: {count} 个单元")
    
    # 4. 检查前端框架
    frontend = BASE_DIR / "frontend" / "index.html"
    if frontend.exists():
        print("\n✅ 前端框架: 已创建")
    else:
        print("\n⏳ 前端框架: 待创建")
    
    # 5. 检查迭代日志
    log = BASE_DIR / "ITERATION_LOG.md"
    if log.exists():
        with open(log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        entries = [l for l in lines if l.startswith('## ')]
        print(f"\n🔄 迭代日志: {len(entries)} 条记录")
    else:
        print("\n⏳ 迭代日志: 待创建")
    
    # 6. 检查Prompt版本
    prompts = list((BASE_DIR / "prompts").glob("golden_prompt_v*.md"))
    if prompts:
        latest = sorted(prompts)[-1].name
        print(f"\n🎯 黄金Prompt: {latest}")
    else:
        print("\n⏳ 黄金Prompt: 待确认")
    
    print("\n" + "=" * 60)
    print("💡 提示: 如需开始工作，请先确认项目宪法中的核心铁律")
    print("=" * 60)


if __name__ == "__main__":
    main()
