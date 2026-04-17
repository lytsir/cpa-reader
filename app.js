/* ===== CPA大白话 - 三栏阅读器 ===== */

const state = {
  subject: '会计',
  tocData: null,
  sidebarOpen: window.innerWidth > 768,
  sidebarPinned: false,
  resizerDragging: false,
  translatePanelWidth: 0.38,
  translateData: {},
  journalData: {},
  currentAnchor: null,
  anchorElements: [],
  inJournalView: false,
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
  journalBack: document.getElementById('journal-back'),
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
  if (els.journalBack) els.journalBack.addEventListener('click', () => {
    state.inJournalView = false;
    loadSubject(state.subject);
  });
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
  if (els.journalBack) els.journalBack.style.display = 'none';
  state.inJournalView = false;

  // 预加载分录索引（renderTOC需要）
  if (!state.journalData[subject]) {
    try {
      const jrRes = await fetch(`metadata/${encodeURIComponent(subject + '_分录索引.json')}?v=${Date.now()}`);
      state.journalData[subject] = await jrRes.json();
    } catch (e) {
      state.journalData[subject] = {};
    }
  }

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

  // 获取锚点并绑定滚动监听和点击跳转
  state.anchorElements = Array.from(els.originalContent.querySelectorAll('.section-anchor'));
  state.currentAnchor = null;
  els.originalContent.removeEventListener('scroll', onOriginalScroll);
  els.originalContent.addEventListener('scroll', onOriginalScroll);
  els.originalContent.removeEventListener('click', onOriginalClick);
  els.originalContent.addEventListener('click', onOriginalClick);

  // 默认滚动到第一章（等待大HTML渲染稳定）
  requestAnimationFrame(() => {
    setTimeout(() => {
      scrollToAnchor(`${subject}-第1章`);
    }, 300);
  });
}

/* ===== 大白话加载 ===== */
function loadTranslate(anchorId, scrollTop) {
  const data = state.translateData[state.subject] || {};
  const content = data[anchorId];
  if (content) {
    els.translateContent.innerHTML = `<div class="translate-section">${escapeHtml(content).replace(/\n/g, '<br>')}</div>`;
  } else {
    els.translateContent.innerHTML = `<div class="placeholder">暂无大白话解读，敬请期待</div>`;
  }
  if (scrollTop) {
    els.translateContent.scrollTop = 0;
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/* ===== 滚动监听 ===== */
const onOriginalScroll = throttle(updateActiveAnchor, 120);

/* ===== 点击跳转 ===== */
function onOriginalClick(e) {
  const container = els.originalContent;
  const rect = container.getBoundingClientRect();
  const clickY = e.clientY - rect.top + container.scrollTop;

  let bestAnchor = state.anchorElements[0];
  for (let i = 0; i < state.anchorElements.length; i++) {
    const el = state.anchorElements[i];
    const nextEl = state.anchorElements[i + 1];
    const top = el.offsetTop - container.offsetTop;
    const nextTop = nextEl ? nextEl.offsetTop - container.offsetTop : Infinity;
    if (clickY >= top && clickY < nextTop) {
      bestAnchor = el;
      break;
    }
  }

  if (bestAnchor.id !== state.currentAnchor) {
    state.currentAnchor = bestAnchor.id;
    loadTranslate(bestAnchor.id, true);
    syncTOCHighlight(bestAnchor.id);
    highlightAnchorBlock(bestAnchor.id);
  }
}

/* ===== 高亮当前锚点区块 ===== */
function highlightAnchorBlock(anchorId) {
  els.originalContent.querySelectorAll('.active-anchor').forEach(el => el.classList.remove('active-anchor'));
  const anchor = document.getElementById(anchorId);
  if (!anchor) return;
  anchor.classList.add('active-anchor');
  let sibling = anchor.nextElementSibling;
  while (sibling && !sibling.classList.contains('section-anchor')) {
    sibling.classList.add('active-anchor');
    sibling = sibling.nextElementSibling;
  }
}

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
    highlightAnchorBlock(bestAnchor.id);
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

/* ===== 渲染目录（章→节两级 + 分录链接） ===== */
function renderTOC(subject) {
  els.tocTree.innerHTML = '';
  const data = state.tocData && state.tocData[subject];
  if (!data || !data.chapters) {
    els.tocTree.innerHTML = '<div class="toc-item">暂无目录</div>';
    return;
  }

  const journalMap = state.journalData[subject] || {};

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

    // 如果本章有分录，添加分录链接
    if (journalMap[ch.anchor]) {
      const jrItem = document.createElement('div');
      jrItem.className = 'toc-item journal-link';
      jrItem.textContent = '📋 本章会计分录';
      jrItem.dataset.journal = ch.anchor;
      jrItem.addEventListener('click', () => {
        showJournalEntries(ch.anchor);
        highlightTOC(jrItem);
        if (isMobile()) closeSidebar();
      });
      els.tocTree.appendChild(jrItem);
    }
  });
}

/* ===== 跳转到锚点 ===== */
function scrollToAnchor(anchor) {
  // 如果当前在分录视图，先切回原文视图
  if (state.inJournalView) {
    state.inJournalView = false;
    loadSubject(state.subject);
    return;
  }
  const el = document.getElementById(anchor);
  if (!el) return;
  const container = els.originalContent;
  const top = el.offsetTop - container.offsetTop - 12;
  container.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
  loadTranslate(anchor);
  syncTOCHighlight(anchor);
}

/* ===== 显示分录表格 ===== */
function showJournalEntries(chapterAnchor) {
  state.inJournalView = true;
  if (els.journalBack) els.journalBack.style.display = 'flex';
  const data = state.journalData[state.subject] || {};
  const chapter = data[chapterAnchor];
  if (!chapter) return;

  let html = `<div class="journal-view"><h2>${escapeHtml(chapter.title)}</h2>`;

  chapter.entries.forEach((cat) => {
    html += `<div class="journal-category"><h3>${escapeHtml(cat.category)}</h3>`;
    cat.items.forEach((item, idx) => {
      const entryId = `${chapterAnchor}-jr-${idx}`;
      html += renderJournalEntry(item, entryId);
    });
    html += `</div>`;
  });

  html += `</div>`;
  els.originalContent.innerHTML = html;

  // 绑定点击事件
  els.originalContent.querySelectorAll('.journal-entry').forEach((el) => {
    el.addEventListener('click', () => {
      const entryId = el.dataset.entryId;
      showJournalTranslate(entryId);
      els.originalContent.querySelectorAll('.journal-entry.active').forEach((a) => a.classList.remove('active'));
      el.classList.add('active');
    });
  });

  // 右栏显示提示
  els.translateContent.innerHTML = '<div class="placeholder">👆 点击左侧分录查看大白话解释</div>';
}

/* ===== 渲染单个分录条目 ===== */
function renderJournalEntry(item, entryId) {
  let debitRows = item.debit.map((d) =>
    `<tr class="debit"><td class="jr-dir">借</td><td class="jr-account">${escapeHtml(d.科目)}</td><td class="jr-amount">${escapeHtml(d.金额)}</td></tr>`
  ).join('');
  let creditRows = item.credit.map((c) =>
    `<tr class="credit"><td class="jr-dir">　贷</td><td class="jr-account">${escapeHtml(c.科目)}</td><td class="jr-amount">${escapeHtml(c.金额)}</td></tr>`
  ).join('');

  return `
    <div class="journal-entry" data-entry-id="${entryId}">
      <div class="journal-entry-title">${escapeHtml(item.title)}</div>
      <table class="journal-entry-table">
        <tbody>${debitRows}${creditRows}</tbody>
      </table>
    </div>
  `;
}

/* ===== 显示分录大白话 ===== */
function showJournalTranslate(entryId) {
  const [chapterAnchor, , idxStr] = entryId.split('-');
  const data = state.journalData[state.subject] || {};
  const chapter = data[chapterAnchor];
  if (!chapter) return;

  // 找到对应的分录条目
  let flatIdx = 0;
  for (const cat of chapter.entries) {
    for (const item of cat.items) {
      if (flatIdx == idxStr) {
        els.translateContent.innerHTML = `
          <div class="journal-translate">
            <h4>${escapeHtml(item.title)}</h4>
            <p>${escapeHtml(item.大白话).replace(/\n/g, '<br>')}</p>
          </div>
        `;
        return;
      }
      flatIdx++;
    }
  }
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
    e.stopPropagation();
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
