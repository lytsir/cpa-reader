/* ===== CPA大白话 - 三栏阅读器 ===== */

const state = {
  subject: '会计',
  tocData: null,
  sidebarOpen: window.innerWidth > 768, // 桌面端默认展开
  sidebarPinned: false,
  resizerDragging: false,
  translatePanelWidth: 0.38, // 右栏占比（桌面端）
};

const els = {
  subjectSelect: document.getElementById('subject-select'),
  menuToggle: document.getElementById('menu-toggle'),
  sidebar: document.getElementById('sidebar'),
  sidebarOverlay: document.getElementById('sidebar-overlay'),
  pinToggle: document.getElementById('pin-toggle'),
  tocTree: document.getElementById('toc-tree'),
  originalContent: document.getElementById('original-content'),
  resizer: document.getElementById('resizer'),
  translatePanel: document.getElementById('translate-panel'),
  translateContent: document.getElementById('translate-content'),
  translateToggle: document.getElementById('translate-toggle'),
  translateClose: document.getElementById('translate-close'),
};

/* ===== 初始化 ===== */
async function init() {
  // 读取URL参数或localStorage的科目
  const urlParams = new URLSearchParams(window.location.search);
  const urlSubject = urlParams.get('subject');
  const savedSubject = localStorage.getItem('cpa-subject');
  if (urlSubject) state.subject = urlSubject;
  else if (savedSubject) state.subject = savedSubject;

  els.subjectSelect.value = state.subject;

  // 事件绑定
  els.subjectSelect.addEventListener('change', onSubjectChange);
  els.menuToggle.addEventListener('click', toggleSidebar);
  els.sidebarOverlay.addEventListener('click', closeSidebar);
  els.pinToggle.addEventListener('click', togglePin);
  if (els.translateToggle) els.translateToggle.addEventListener('click', openTranslatePanel);
  if (els.translateClose) els.translateClose.addEventListener('click', closeTranslatePanel);
  setupResizer();
  updateSidebarUI();

  // 加载数据
  await loadTOCData();
  await loadSubject(state.subject);
}

/* ===== 加载章节树 ===== */
async function loadTOCData() {
  try {
    const res = await fetch('metadata/六科_章节树.json?v=' + Date.now());
    state.tocData = await res.json();
  } catch (e) {
    console.error('加载章节树失败', e);
    els.tocTree.innerHTML = '<div class="toc-item">加载目录失败，请刷新</div>';
  }
}

/* ===== 切换科目 ===== */
function onSubjectChange() {
  state.subject = els.subjectSelect.value;
  localStorage.setItem('cpa-subject', state.subject);
  // 更新URL
  const url = new URL(window.location);
  url.searchParams.set('subject', state.subject);
  window.history.replaceState({}, '', url);
  loadSubject(state.subject);
}

/* ===== 加载指定科目 ===== */
async function loadSubject(subject) {
  // 清空中栏
  els.originalContent.innerHTML = '<div class="placeholder">正在加载教材...</div>';
  els.translateContent.innerHTML = '<div class="placeholder">请先选择目录开始学习</div>';

  // 渲染目录
  renderTOC(subject);

  // 加载完整HTML（提取body内容）
  try {
    const res = await fetch(`metadata/${subject}_带锚点.html?v=${Date.now()}`);
    const htmlText = await res.text();
    // 提取body内容（完整HTML文档不能直接innerHTML）
    const bodyMatch = htmlText.match(/<body[^>]*>([\s\S]*)<\/body>/i);
    const content = bodyMatch ? bodyMatch[1] : htmlText;
    els.originalContent.innerHTML = content;
  } catch (e) {
    console.error('加载原文失败', e);
    els.originalContent.innerHTML = '<div class="placeholder">加载原文失败，请检查网络后刷新</div>';
    return;
  }

  // 默认滚动到第一章
  setTimeout(() => {
    scrollToAnchor(`${subject}-第1章`);
  }, 50);
}

/* ===== 渲染目录（章→节两级） ===== */
function renderTOC(subject) {
  els.tocTree.innerHTML = '';
  const data = state.tocData && state.tocData[subject];
  if (!data || !data.chapters) {
    els.tocTree.innerHTML = '<div class="toc-item">暂无目录</div>';
    return;
  }

  data.chapters.forEach((ch, chIdx) => {
    // 章
    const chItem = document.createElement('div');
    chItem.className = 'toc-item chapter';
    chItem.textContent = ch.title;
    chItem.dataset.anchor = ch.anchor;
    chItem.addEventListener('click', () => {
      scrollToAnchor(ch.anchor);
      highlightTOC(chItem);
      if (isMobile()) closeSidebar();
    });
    els.tocTree.appendChild(chItem);

    // 节
    ch.sections.forEach((sec) => {
      const secItem = document.createElement('div');
      secItem.className = 'toc-item section';
      secItem.textContent = sec.title;
      secItem.dataset.anchor = sec.anchor;
      secItem.addEventListener('click', () => {
        scrollToAnchor(sec.anchor);
        highlightTOC(secItem);
        if (isMobile()) closeSidebar();
      });
      els.tocTree.appendChild(secItem);
    });
  });
}

/* ===== 跳转到锚点 ===== */
function scrollToAnchor(anchor) {
  const el = document.getElementById(anchor);
  if (!el) return;
  const container = els.originalContent;
  const top = el.offsetTop - container.offsetTop - 12;
  container.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
}

/* ===== 高亮目录项 ===== */
function highlightTOC(activeItem) {
  document.querySelectorAll('.toc-item').forEach(i => i.classList.remove('active'));
  activeItem.classList.add('active');
}

/* ===== 侧边栏控制 ===== */
function toggleSidebar() {
  state.sidebarOpen = !state.sidebarOpen;
  updateSidebarUI();
}
function closeSidebar() {
  state.sidebarOpen = false;
  updateSidebarUI();
}
function togglePin() {
  state.sidebarPinned = !state.sidebarPinned;
  els.pinToggle.textContent = state.sidebarPinned ? '📍' : '📌';
  updateSidebarUI();
}
function updateSidebarUI() {
  els.sidebar.classList.toggle('open', state.sidebarOpen);
  els.sidebarOverlay.classList.toggle('open', state.sidebarOpen && isMobile());
}

function isMobile() {
  return window.innerWidth <= 768;
}

/* ===== 大白话面板控制 ===== */
function openTranslatePanel() {
  if (!isMobile()) return;
  els.translatePanel.classList.add('open');
}
function closeTranslatePanel() {
  els.translatePanel.classList.remove('open');
}

/* ===== 分隔线拖动 ===== */
function setupResizer() {
  if (!els.resizer || !els.translatePanel) return;

  els.resizer.addEventListener('mousedown', startDrag);
  els.resizer.addEventListener('touchstart', startDrag, { passive: false });

  function startDrag(e) {
    if (isMobile()) return;
    state.resizerDragging = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    document.addEventListener('mousemove', onDrag);
    document.addEventListener('mouseup', stopDrag);
    document.addEventListener('touchmove', onDrag, { passive: false });
    document.addEventListener('touchend', stopDrag);
  }

  function onDrag(e) {
    if (!state.resizerDragging) return;
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const containerWidth = document.querySelector('.main-container').clientWidth;
    const sidebarWidth = els.sidebar.clientWidth;
    const availableWidth = containerWidth - sidebarWidth - 8; // 减去分隔线
    let newWidth = containerWidth - clientX;
    // 限制范围
    newWidth = Math.max(200, Math.min(newWidth, availableWidth * 0.65));
    els.translatePanel.style.width = newWidth + 'px';
    els.translatePanel.style.flex = 'none';
  }

  function stopDrag() {
    state.resizerDragging = false;
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    document.removeEventListener('mousemove', onDrag);
    document.removeEventListener('mouseup', stopDrag);
    document.removeEventListener('touchmove', onDrag);
    document.removeEventListener('touchend', stopDrag);
  }
}

/* ===== 窗口大小变化 ===== */
window.addEventListener('resize', () => {
  updateSidebarUI();
  if (!isMobile() && els.translatePanel) {
    // 桌面端：重置样式，关闭大白话面板
    els.translatePanel.style.width = '';
    els.translatePanel.style.flex = '';
    els.translatePanel.classList.remove('open');
  }
});

/* ===== 启动 ===== */
init();
