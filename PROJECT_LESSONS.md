# CPA三栏阅读器 - 项目经验总结与优化建议

## 一、已踩的坑

### 1. 大白话锚点ID不匹配 → 用户看不到白话
**现象**：第8-12章点击目录显示"暂无大白话解读"
**根因**：大白话索引的锚点ID格式与HTML实际锚点ID不一致
- 大白话：`会计-第8章-短期借款`（缺少"第X节"）
- HTML：`会计-第8章-第1节-短期借款`
**修复**：
- 批量映射：从HTML中提取主题→节的对应关系，重写33个锚点ID
- 防御代码：`loadTranslate()`增加子锚点回退，精确匹配失败时自动合并子主题白话

### 2. 分录数据混入LaTeX/描述文本 → 显示乱码
**现象**：分录中出现 `④④2×232\times`、`1080001 0 8 \enspace 000`
**根因**：PDF转HTML后表格结构被破坏
- MathML公式（`2\times 18`）混入了纯文本提取
- 表格金额被拆成多段落（`75000`→`750007 5 \enspace 000`）
- 描述性文本（日期、编号）被误当成分录行
**修复**：
- 清理正则：`\\times`、`\\enspace`、重复编号`③③`→`③`
- 手动修复第10章核心分录金额（96000/108000/75000等）
- 删除描述性文本混入的科目行

### 3. 分录索引缓存 → 修复后不生效
**现象**：GitHub已推送修复，浏览器仍显示旧乱码
**根因**：`loadSubject()`中`if (!state.journalData[subject])`只加载一次，后续永不更新
**修复**：去掉缓存判断，每次加载科目都重新fetch分录索引

### 4. 大文件加载超时 → 页面卡在"加载中"
**现象**：3.6MB的`会计_带锚点.html`在GitHub Pages上fetch超时
**根因**：单文件太大，浏览器fetch 30秒超时
**修复**：
- 按章节拆分为22个小文件（20-200KB）
- `loadSubject()`只加载第1章
- 点击其他章节时按需`loadChapter()`

---

## 二、待优化的架构问题

### 1. 锚点ID生成必须统一
**现状**：不同阶段的脚本生成不同格式的锚点ID
**建议**：
- 建立一个`锚点规范文档`，所有生成脚本必须遵守
- 格式：`{科目}-第{X}章-第{Y}节-[主题]`
- 生成后立即运行`验证脚本`检查与HTML的匹配率

### 2. 分录提取需要更健壮
**现状**：依赖段落文本特征提取，PDF转HTML质量差时崩溃
**建议**：
- 提取前先做`HTML结构检查`：统计`<p>`标签中借/贷关键字的分布
- 异常检测：如果出现`\`字符或纯数字段落，标记为可疑
- 金额合并逻辑：遇到`\enspace`或断行时，尝试前后合并为完整数字

### 3. 数据缓存策略
**现状**：为了省流量而缓存，但更新后用户看不到新内容
**建议**：
- 大白话索引、分录索引：`fetch时始终加?v=Date.now()`，但允许浏览器HTTP缓存（GitHub Pages支持）
- 或者：设置一个`数据版本号`（如`data-v2`），每次批量更新时递增，URL中携带版本号

### 4. 加载体验
**现状**：首次加载仍显示"正在加载教材..."较长时间
**建议**：
- 增加加载进度条（`fetch`支持`ReadableStream`获取下载进度）
- 第1章加载完成后立即显示，后台预加载第2章
- 增加骨架屏（skeleton screen）而非纯文字placeholder

### 5. 数据验证流水线
**现状**：修复靠用户反馈，事后补救
**建议**：每次构建后自动运行：
```
1. 检查所有目录锚点是否有对应大白话（匹配率>90%）
2. 检查分录中是否包含LaTeX残留（\\times、\\enspace等）
3. 检查金额字段是否为空或异常（纯数字作为科目）
4. 输出报告，不匹配时构建失败
```

---

## 三、关键代码模式（应固化为skill）

### 按需加载章节
```javascript
// state.loadedChapters = new Set()
async function loadChapter(chapterNum) {
  const chKey = `${state.subject}-第${chapterNum}章`;
  if (state.loadedChapters.has(chKey)) return;
  // fetch章节HTML → insertAdjacentHTML → 修复表格/公式
}
```

### 大白话子锚点回退
```javascript
function loadTranslate(anchorId) {
  let content = data[anchorId];
  if (!content) {
    const childKeys = Object.keys(data).filter(k => k.startsWith(anchorId + '-'));
    if (childKeys.length > 0) {
      content = childKeys.map(k => data[k]).join('\n\n');
    }
  }
}
```

---

## 四、已推送的修复汇总

| 文件 | 修改内容 |
|------|----------|
| `metadata/会计_分录索引.json` | 补充第8-12章71条分录 + 修复金额/LaTeX乱码 |
| `metadata/会计_大白话索引.json` | 修复33个锚点ID，补充节级信息 |
| `metadata/会计_分章/` | 新增22个章节拆分文件 |
| `app.js` | 按需加载 + 子锚点回退 + 取消分录缓存 |
| `index.html` | 版本号更新 |
