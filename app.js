/* ===== CPA大白话 - 三栏阅读器 ===== */

const state = {
  subject: '会计',
  tocData: null,
  sidebarOpen: window.innerWidth > 768,
  sidebarPinned: false,
  resizerDragging: false,
  translatePanelWidth: 0.38,
  translateData: {},
  currentAnchor: null,
  anchorElements: [],
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
  const urlParams = new URLSearchParams(window.location.search);
  const urlSubject = urlParams.get('subject');
  const savedSubject = localStorage.getItem('cpa-subject');
  if (urlSubject) state.subject = urlSubject;
  else if (savedSubject) state.subject = savedSubject;
  els.subjectSelect.value = state.subject;

  els.subjectSelect.addEventListener('change', onSubjectChange);
  els.menuToggle.addEventListener('click', toggleSidebar);
  els.sidebarOverlay.addEventListener('click', closeSidebar);
  els.pinToggle.addEventListener('click', togglePin);
  if (els.translateToggle) els.translateToggle.addEventListener('click', openTranslatePanel);
  if (els.translateClose) els.translateClose.addEventListener('click', closeTranslatePanel);
  setupResizer();
  updateSidebarUI();

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
  const url = new URL(window.location);
  url.searchParams.set('subject', state.subject);
  window.history.replaceState({}, '', url);
  loadSubject(state.subject);
}

/* ===== 加载指定科目 ===== */
async function loadSubject(subject) {
  els.originalContent.innerHTML = '<div class="placeholder">正在加载教材...</div>';
  els.translateContent.innerHTML = '<div class="placeholder">请先选择目录开始学习</div>';

  renderTOC(subject);

  // 加载原文
  try {
    const res = await fetch(`metadata/${subject}_带锚点.html?v=${Date.now()}`);
    const htmlText = await res.text();
    const bodyMatch = htmlText.match(/<body[^>]*>([\s\S]*)<\/body>/i);
    const content = bodyMatch ? bodyMatch[1] : htmlText;
    els.originalContent.innerHTML = content;
  } catch (e) {
    console.error('加载原文失败', e);
    els.originalContent.innerHTML = '<div class="placeholder">加载原文失败，请检查网络后刷新</div>';
    return;
  }

  // 加载大白话索引
  try {
    const transRes = await fetch(`metadata/${subject}_大白话索引.json?v=${Date.now()}`);
    state.translateData[subject] = await transRes.json();
  } catch (e) {
    state.translateData[subject] = {};
  }

  // 获取锚点并绑定滚动监听
  state.anchorElements = Array.from(els.originalContent.querySelectorAll('.section-anchor'));
  state.currentAnchor = null;
  els.originalContent.removeEventListener('scroll', onOriginalScroll);
  els.originalContent.addEventListener('scroll', onOriginalScroll);

  // 默认滚动到第一章（等待大HTML渲染稳定）
  requestAnimationFrame(() => {
    setTimeout(() => {
      scrollToAnchor(`${subject}-第1章`);
    }, 300);
  });
}

/* ===== 大白话加载 ===== */
function loadTranslate(anchorId) {
  const data = state.translateData[state.subject] || {};
  const content = data[anchorId];
  if (content) {
    els.translateContent.innerHTML = `<div class="translate-section">${escapeHtml(content).replace(/\n/g, '<br>')}</div>`;
  } else {
    els.translateContent.innerHTML = `<div class="placeholder">暂无大白话解读，敬请期待</div>`;
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/* ===== 滚动监听 ===== */
const onOriginalScroll = throttle(updateActiveAnchor, 120);

function updateActiveAnchor() {
  if (!state.anchorElements.length) return;
  const container = els.originalContent;
  const scrollTop = container.scrollTop;

  let bestAnchor = state.anchorElements[0];
  for (const el of state.anchorElements) {
    const top = el.offsetTop - container.offsetTop;
    if (top <= scrollTop + 24) {
      bestAnchor = el;
    } else {
      break;
    }
  }

  if (bestAnchor.id !== state.currentAnchor) {
    state.currentAnchor = bestAnchor.id;
    loadTranslate(bestAnchor.id);
    syncTOCHighlight(bestAnchor.id);
  }
}

function throttle(fn, wait) {
  let lastTime = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastTime >= wait) {
      lastTime = now;
      fn.apply(this, args);
    }
  };
}

/* ===== 目录高亮同步 ===== */
function syncTOCHighlight(anchorId) {
  let bestItem = null;
  let bestScore = -1;

  document.querySelectorAll('.toc-item').forEach(item => {
    item.classList.remove('active');
    const itemAnchor = item.dataset.anchor || '';
    if (anchorId === itemAnchor) {
      bestItem = item;
      bestScore = 1000;
    } else if (anchorId.startsWith(itemAnchor + '-')) {
      const score = itemAnchor.length;
      if (score > bestScore) {
        bestScore = score;
        bestItem = item;
      }
    }
  });

  if (bestItem) bestItem.classList.add('active');
}

/* ===== 渲染目录（章→节两级） ===== */
function renderTOC(subject) {
  els.tocTree.innerHTML = '';
  const data = state.tocData && state.tocData[subject];
  if (!data || !data.chapters) {
    els.tocTree.innerHTML = '<div class="toc-item">暂无目录</div>';
    return;
  }

  data.chapters.forEach((ch) => {
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
  loadTranslate(anchor);
  syncTOCHighlight(anchor);
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
    e.preventDefault();
    state.resizerDragging = true;
    document.body.classList.add('resizer-dragging');

    document.addEventListener('mousemove', onDrag);
    document.addEventListener('mouseup', stopDrag);
    document.addEventListener('touchmove', onDrag, { passive: false });
    document.addEventListener('touchend', stopDrag);
  }

  function onDrag(e) {
    if (!state.resizerDragging) return;
    e.preventDefault();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const containerRect = document.querySelector('.main-container').getBoundingClientRect();
    const sidebarWidth = els.sidebar.clientWidth;
    const newWidth = containerRect.right - clientX;
    const minWidth = 200;
    const maxWidth = containerRect.width - sidebarWidth - 120;
    const clampedWidth = Math.max(minWidth, Math.min(newWidth, maxWidth));
    els.translatePanel.style.width = clampedWidth + 'px';
    els.translatePanel.style.flex = 'none';
  }

  function stopDrag() {
    state.resizerDragging = false;
    document.body.classList.remove('resizer-dragging');
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
    els.translatePanel.style.width = '';
    els.translatePanel.style.flex = '';
    els.translatePanel.classList.remove('open');
  }
});

/* ===== 启动 ===== */
init();
