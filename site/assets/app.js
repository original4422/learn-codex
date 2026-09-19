'use strict';
(() => {
  const lang = document.body.dataset.lang;
  const zh = lang === 'zh';
  const get = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } };
  const put = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* reading works without storage */ } };
  const theme = get('learn-codex-theme', 'light');
  document.documentElement.dataset.theme = theme;
  document.querySelector('#theme').addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next; put('learn-codex-theme', next);
  });
  const menu = document.querySelector('#menu');
  menu.addEventListener('click', () => { const open = document.querySelector('#sidebar').classList.toggle('open'); menu.setAttribute('aria-expanded', String(open)); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape') { document.querySelector('#sidebar').classList.remove('open'); menu.setAttribute('aria-expanded', 'false'); } });
  document.querySelectorAll('.copy-code').forEach(button => {
    button.textContent = zh ? '复制' : 'Copy';
    button.setAttribute('aria-label', zh ? '复制代码' : 'Copy code');
    button.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(button.closest('.code-block').querySelector('code').textContent); button.textContent = zh ? '已复制' : 'Copied'; }
      catch { button.textContent = zh ? '请手动选中复制' : 'Select and copy manually'; }
      setTimeout(() => { button.textContent = zh ? '复制' : 'Copy'; }, 1800);
    });
  });
  const savedProgress = get('learn-codex-completed', []);
  const completed = new Set(Array.isArray(savedProgress) ? savedProgress.filter(value => /^\d{2}-/.test(value)) : []);
  const done = document.querySelector('#mark-done');
  const updateProgress = () => {
    document.querySelector('#progress-count').textContent = `${completed.size} / 11`;
    document.querySelector('#progress-fill').style.width = `${completed.size / 11 * 100}%`;
    if (done) { const learned = completed.has(document.body.dataset.page); done.textContent = learned ? `✓ ${done.dataset.undone}` : done.dataset.done; done.setAttribute('aria-pressed', String(learned)); }
  };
  if (done) done.addEventListener('click', () => { const page = document.body.dataset.page; if (completed.has(page)) completed.delete(page); else completed.add(page); put('learn-codex-completed', [...completed]); updateProgress(); });
  updateProgress();
  const dialog = document.querySelector('#search-dialog');
  const input = document.querySelector('#search-input');
  const results = document.querySelector('#search-results');
  let index = [];
  const search = () => {
    const query = input.value.trim().toLocaleLowerCase();
    const words = query.split(/\s+/).filter(Boolean);
    const matches = index.map(page => ({page, score: words.reduce((n, word) => n + (page.title.toLocaleLowerCase().includes(word) ? 4 : 0), 0)})).filter(({page}) => words.every(word => (page.title + ' ' + page.text).toLocaleLowerCase().includes(word))).sort((a,b) => b.score - a.score).slice(0, 15);
    results.replaceChildren();
    for (const {page} of matches) {
      const link = document.createElement('a'); link.href = page.url; link.textContent = page.title;
      const snippet = document.createElement('small'); const offset = query ? Math.max(0, page.text.toLocaleLowerCase().indexOf(words[0]) - 25) : 0; snippet.textContent = page.text.slice(offset, offset + 115).replace(/\n/g, ' ') + '…'; link.append(snippet); results.append(link);
    }
    if (!matches.length) { const text = document.createElement('p'); text.textContent = results.dataset.empty; results.append(text); }
  };
  const openSearch = async () => {
    dialog.showModal(); input.focus();
    if (!index.length) {
      try { const response = await fetch(`/${lang}/search.json`); if (!response.ok) throw new Error('Search unavailable'); index = await response.json(); }
      catch { results.textContent = zh ? '请通过本地预览服务器打开网站。搜索索引暂不可用。' : 'Open this site through the preview server. Search index is unavailable.'; return; }
    }
    search();
  };
  document.querySelector('#search-open').addEventListener('click', openSearch);
  document.querySelector('#search-close').addEventListener('click', () => dialog.close());
  input.addEventListener('input', search);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && dialog.open) { event.preventDefault(); dialog.close(); return; }
    if (event.key === '/' && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) && !dialog.open) { event.preventDefault(); openSearch(); }
  }, true);
  dialog.addEventListener('click', event => { if (event.target === dialog) { const rect = dialog.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close(); } });
  const step = document.querySelector('#step');
  if (step) {
    let cursor = 0;
    const scenarios = {
      success: zh ? ['request: 列出尚未完成的任务。', 'decision: 调用 list_tasks(status="open")。', 'tool.result: [{id: 2, title: "补充过滤测试"}]', 'verify: 返回 1 项；输出依据工具结果，结束。'] : ['request: List unfinished tasks.', 'decision: Call list_tasks(status="open").', 'tool.result: [{id: 2, title: "Add filter tests"}]', 'verify: 1 item; answer grounded in the tool result. Done.'],
      failure: zh ? ['request: 列出尚未完成的任务。', 'decision: 调用 list_tasks(status="open")。', 'tool.error: 存储文件损坏，不能当作空清单。', 'verify: 报告阻碍；保留原始文件，停止。'] : ['request: List unfinished tasks.', 'decision: Call list_tasks(status="open").', 'tool.error: Corrupt store; this is not an empty list.', 'verify: Report the blocker. Preserve the file. Stop.'],
      budget: zh ? ['request: 持续搜索，直到找到更多任务。', 'decision: 请求再次读取，但工具调用预算为 0。', 'budget.exhausted: 未运行工具。', 'verify: 明确任务未完成；请求调整范围或预算。'] : ['request: Keep searching for more tasks.', 'decision: Request another read; tool budget is 0.', 'budget.exhausted: No tool was executed.', 'verify: Task incomplete. Revise the scope or budget.']
    };
    const log = document.querySelector('#sim-log');
    const reset = () => { cursor = 0; log.textContent = zh ? '等待开始。点击「下一步」观察事件。' : 'Ready. Click “Next step” to observe events.'; step.disabled = false; document.querySelectorAll('[data-stage]').forEach(node => node.classList.remove('current')); };
    step.addEventListener('click', () => { if (cursor === 0) log.textContent = ''; log.textContent += scenarios[document.querySelector('#scenario').value][cursor] + '\n'; document.querySelectorAll('[data-stage]').forEach(node => node.classList.toggle('current', Number(node.dataset.stage) === cursor)); cursor += 1; step.disabled = cursor === 4; });
    document.querySelector('#reset').addEventListener('click', reset); document.querySelector('#scenario').addEventListener('change', reset); reset();
    const policy = () => { const inside = document.querySelector('#inside').checked; const approved = document.querySelector('#approved').checked; document.querySelector('#policy-result').textContent = !inside ? (zh ? 'DENY · 路径越界。批准不等于获得文件系统权限。' : 'DENY · Out of bounds. Approval is not filesystem permission.') : !approved ? (zh ? 'ASK · 路径允许，但仍缺少所需批准。' : 'ASK · Path allowed; required approval is missing.') : (zh ? 'ALLOW · 两项检查通过。实际执行仍可能失败。' : 'ALLOW · Both checks pass. Execution may still fail.'); };
    document.querySelector('#inside').addEventListener('change', policy); document.querySelector('#approved').addEventListener('change', policy); policy();
  }
})();
