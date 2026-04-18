#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/Volumes/lyq/CPA三栏阅读器_工作区/scripts')
from hard_check_dabaihua import check

base = "/Volumes/lyq/CPA三栏阅读器_工作区/temp_ch4_sec345"

files = [
    ("会计-第4章-第3节", "会计-第4章-第3节_dabaihua.txt", "会计-第4章-第3节.txt"),
    ("会计-第4章-第3节-无形资产后续计量的原则", "会计-第4章-第3节-无形资产后续计量的原则_dabaihua.txt", "会计-第4章-第3节-无形资产后续计量的原则.txt"),
    ("会计-第4章-第3节-估计无形资产的使用寿命", "会计-第4章-第3节-估计无形资产的使用寿命_dabaihua.txt", "会计-第4章-第3节-估计无形资产的使用寿命.txt"),
    ("会计-第4章-第3节-无形资产使用寿命的确定", "会计-第4章-第3节-无形资产使用寿命的确定_dabaihua.txt", "会计-第4章-第3节-无形资产使用寿命的确定.txt"),
    ("会计-第4章-第3节-无形资产使用寿命的复核", "会计-第4章-第3节-无形资产使用寿命的复核_dabaihua.txt", "会计-第4章-第3节-无形资产使用寿命的复核.txt"),
    ("会计-第4章-第3节-使用寿命有限的无形资产", "会计-第4章-第3节-使用寿命有限的无形资产_dabaihua.txt", "会计-第4章-第3节-使用寿命有限的无形资产.txt"),
    ("会计-第4章-第3节-摊销期和摊销方法", "会计-第4章-第3节-摊销期和摊销方法_dabaihua.txt", "会计-第4章-第3节-摊销期和摊销方法.txt"),
    ("会计-第4章-第3节-残值的确定", "会计-第4章-第3节-残值的确定_dabaihua.txt", "会计-第4章-第3节-残值的确定.txt"),
    ("会计-第4章-第3节-使用寿命有限的无形资产摊销的账务处理", "会计-第4章-第3节-使用寿命有限的无形资产摊销的账务处理_dabaihua.txt", "会计-第4章-第3节-使用寿命有限的无形资产摊销的账务处理.txt"),
    ("会计-第4章-第3节-使用寿命不确定的无形资产", "会计-第4章-第3节-使用寿命不确定的无形资产_dabaihua.txt", "会计-第4章-第3节-使用寿命不确定的无形资产.txt"),
    ("会计-第4章-第3节-无形资产的减值", "会计-第4章-第3节-无形资产的减值_dabaihua.txt", "会计-第4章-第3节-无形资产的减值.txt"),
    ("会计-第4章-第4节", "会计-第4章-第4节_dabaihua.txt", "会计-第4章-第4节.txt"),
    ("会计-第4章-第4节-无形资产的出售", "会计-第4章-第4节-无形资产的出售_dabaihua.txt", "会计-第4章-第4节-无形资产的出售.txt"),
    ("会计-第4章-第4节-无形资产的报废", "会计-第4章-第4节-无形资产的报废_dabaihua.txt", "会计-第4章-第4节-无形资产的报废.txt"),
    ("会计-第4章-第5节", "会计-第4章-第5节_dabaihua.txt", "会计-第4章-第5节.txt"),
    ("会计-第4章-第5节-无形资产的列示", "会计-第4章-第5节-无形资产的列示_dabaihua.txt", "会计-第4章-第5节-无形资产的列示.txt"),
    ("会计-第4章-第5节-无形资产的披露", "会计-第4章-第5节-无形资产的披露_dabaihua.txt", "会计-第4章-第5节-无形资产的披露.txt"),
    ("会计-第4章-第5节-关于知识产权的其他披露要求", "会计-第4章-第5节-关于知识产权的其他披露要求_dabaihua.txt", "会计-第4章-第5节-关于知识产权的其他披露要求.txt"),
    ("会计-第4章-第5节-关于确认为无形资产的数据资源的披露要求", "会计-第4章-第5节-关于确认为无形资产的数据资源的披露要求_dabaihua.txt", "会计-第4章-第5节-关于确认为无形资产的数据资源的披露要求.txt"),
]

passed = 0
failed = 0
for anchor, dabai_file, orig_file in files:
    dabai_path = os.path.join(base, dabai_file)
    orig_path = os.path.join(base, orig_file)
    with open(dabai_path, 'r') as f:
        dabai = f.read()
    with open(orig_path, 'r') as f:
        orig = f.read()
    errors = check(dabai, orig, anchor)
    if errors:
        print(f"❌ {anchor}")
        for e in errors:
            print(f"   {e}")
        failed += 1
    else:
        print(f"✅ {anchor}")
        passed += 1

print(f"\n总计: {passed} 通过, {failed} 失败")
