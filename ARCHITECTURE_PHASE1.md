# CPA大白话 三栏阅读器 - Phase 1 架构总结与复用指南

## 一、核心目标
构建一个**零改动原文**、**章-节两级导航**、**跨端响应式**的三栏阅读器（目录 / 原文 / 大白话），为后续六科大白话批量生成提供统一载体。

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│  左栏: 目录树 (TOC)          中栏: 原文 (Original)          右栏: 大白话 (Translate)  │
│  ───────────────              ────────────────              ─────────────────────  │
│  章 → 节 两级导航              完整教材 HTML                   占位 / 后续动态加载     │
│  点击跳转锚点                  仅插入不可见锚点                 当前为 placeholder     │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 文件结构
```
repo-root/
├── index.html              # 入口，三栏布局 + 科目选择器
├── app.js                  # 核心逻辑: 加载 / 渲染 / 跳转 / 响应式
├── style.css               # 三栏 Flexbox + 移动端侧滑
├── metadata/
│   ├── 六科_章节树.json     # 六科章-节结构，前端渲染目录
│   ├── 会计_带锚点.html     # 完整教材（~3.6MB，30章）
│   ├── 审计_带锚点.html
│   ├── 财管_带锚点.html
│   ├── 战略_带锚点.html
│   ├── 经济法_带锚点.html
│   └── 税法_带锚点.html
```

**关键约束**：GitHub Pages 要求 `index.html` 必须在仓库根目录，不能放在 `frontend/` 子目录。

---

## 三、Phase 1 具体做了什么

### 3.1 原文处理：全本 HTML +  invisible anchors
- **输入**：六科合并后的原始教材 HTML（从 EPUB/PDF/Word 合并得到）
- **处理**：Python 脚本遍历 `<h1>` / `<h2>` 标题，在章节/节位置插入不可见锚点
  ```html
  <div id="会计-第1章" class="section-anchor"></div>
  <h1>第一章 总 论</h1>
  <div id="会计-第1章-第1节" class="section-anchor"></div>
  <h2>第一节 会计概述</h2>
  ```
- **输出**：`metadata/{subject}_带锚点.html`
- **原则**：**原文零改动**，只插入无样式的 `<div id="...">` 锚点

### 3.2 目录树提取：结构化 JSON
- 同时解析原始 HTML 的标题层级，生成 `metadata/六科_章节树.json`
- 深度只到**章 → 节**两级（子节不显示，保证目录清爽）
- 每个节点带 `title` 和 `anchor`（与 HTML 中的 `id` 一一对应）

### 3.3 前端渲染逻辑 (`app.js`)
| 功能 | 实现方式 |
|------|----------|
| **科目切换** | `<select>` 触发 `loadSubject(subject)`，URL 参数同步 |
| **加载原文** | `fetch(metadata/${subject}_带锚点.html)`，**正则提取 `<body>` 内容**后 `innerHTML` |
| **渲染目录** | 读取 `六科_章节树.json` → `renderTOC()` 生成可点击列表 |
| **锚点跳转** | `document.getElementById(anchor)` → 计算 `offsetTop` → `container.scrollTo({top, behavior:'smooth'})` |
| **桌面端分栏** | Flexbox：`sidebar (280px)` + `original-panel (flex:1)` + `resizer (8px)` + `translate-panel (38%)` |
| **拖拽调整** | `mousedown`/`touchstart` 监听 resizer，动态计算右栏 `width` |
| **移动端适配** | ≤768px 时：左栏/右栏变为 `position: absolute` 侧滑面板；☰ 和 💬 按钮分别控制 |

### 3.4 响应式设计 (`style.css`)
- **桌面端 (>768px)**：三栏并排，sidebar 可收起（`☰` 按钮控制 `width: 0` 过渡动画）
- **平板端 (768px~1024px)**：三栏保持，宽度自适应
- **手机端 (≤768px)**：默认只显示原文；左栏从左侧滑入，右栏从右侧滑入

---

## 四、关键坑与修复记录

| 问题 | 现象 | 根因 | 修复 |
|------|------|------|------|
| **中间栏空白** | 页面加载后原文区域只有"正在加载教材..." | 直接 `innerHTML = 完整HTML文档` 导致浏览器丢弃 `<body>` | JS 中正则提取 `<body>(...)</body>` 内容再插入 |
| **404 on GitHub Pages** | 部署后页面空白 | 文件放在 `frontend/` 子目录，GitHub Pages 只服务根目录 | 全部文件移到仓库根目录 |
| **目录点击无跳转** | 点击章节目录无反应 | 页面仍缓存旧版 `app.js?v=1`，新逻辑未生效 | 每次更新 `index.html` 中的 `?v=N` cache-buster |
| **桌面端 sidebar 无法隐藏** | 点击 ☰ 没有反应 | `updateSidebarUI()` 被 `sidebarPinned` 状态覆盖，且 CSS 没写 `.sidebar:not(.open)` 的桌面隐藏样式 | JS 解耦 pinned 与 open 状态；CSS 增加桌面端 `width:0` 过渡 |
| **手机端看不到大白话** | 右栏默认隐藏且无入口 | 移动端 CSS 把 `translate-panel` 设为侧滑，但没有打开按钮 | 顶部栏新增 💬 按钮，右栏 header 新增 ✕ 关闭按钮 |

---

## 五、复用指南：如何为其他教材/文档制作同款三栏阅读器

### 5.1 数据准备（可复用脚本）
你需要两份产物：

**A. 带锚点的完整原文 HTML**
```python
# 核心逻辑伪代码
import re
html = open("source/合并.html").read()
chapters = extract_headings(html)  # 根据 h1/h2 提取章-节
for ch in chapters:
    anchor = f"{subject}-{ch.id}"
    html = insert_before(html, ch.position, f'<div id="{anchor}" class="section-anchor"></div>')
open(f"metadata/{subject}_带锚点.html", "w").write(html)
```

**B. 章节树 JSON**
```json
{
  "会计": {
    "chapters": [
      {
        "title": "第一章 总 论",
        "anchor": "会计-第1章",
        "sections": [
          {"title": "第一节 会计概述", "anchor": "会计-第1章-第1节"}
        ]
      }
    ]
  }
}
```

### 5.2 前端复用（零改动即可用）
`index.html` + `app.js` + `style.css` 这套前端是**通用**的，只需修改：
1. **科目列表**：`index.html` 中 `<select id="subject-select">` 的 `<option>`
2. **fetch 路径**：`app.js` 中 `fetch(`metadata/${subject}_带锚点.html`)` 的路径前缀
3. **JSON 文件名**：`app.js` 中 `fetch('metadata/六科_章节树.json')` 的文件名

### 5.3 部署 checklist
- [ ] `index.html` 必须在仓库根目录（GitHub Pages 要求）
- [ ] 每次更新 `app.js` / `style.css` 时，同步修改 `index.html` 里的 `?v=N` 防止 CDN 缓存
- [ ] 大文件 HTML 直接放 Git（<100MB 无需 LFS）
- [ ] 推送后等待 1~2 分钟让 GitHub Pages 生效

### 5.4 扩展方向
| Phase | 扩展内容 | 依赖 |
|-------|----------|------|
| **Phase 2** | 锚点精细化（小节、例题、公式级锚点） | 需要更细粒度的 HTML 解析 |
| **Phase 3** | 右栏填充大白话 | 按 anchor 生成对应 `.md` 或 `.json`，前端 `fetch` 后渲染 |
| **Phase 4** | 搜索 / 高亮 / 笔记同步 | 增加 indexedDB 或后端 API |

---

## 六、一句话总结

> **把任何长篇教材变成三栏阅读器，只需要做三件事：原始 HTML 插锚点 → 提取章-节 JSON → 通用前端加载。**

这套模式完全可复制到法考、建造师、医学教材等任何"需要对照原文做白话解读"的场景。
