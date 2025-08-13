/* Missing links and inline editing with server-rendered preview + mode toggle */
(function () {
  const missingBox = document.getElementById('missing-links-detail');
  const contentEl = document.getElementById('note-content-raw');
  const viewBox = document.getElementById('note-content');
  const titleEl = document.getElementById('note-title');
  const editorBox = document.getElementById('inline-editor');
  const existingTitles = (window.EXISTING_TITLES || []).map((s) => (s || '').trim()).filter(Boolean);

  function extractTitles(md) {
    const set = new Set();
    (md.match(/\[\[([^\[\]]+)\]\]/g) || []).forEach((w) => {
      const t = w.slice(2, -2).trim();
      if (t) set.add(t);
    });
    return Array.from(set.values());
  }

  if (missingBox && contentEl) {
    const titles = extractTitles(contentEl.textContent || '');
    const missing = titles.filter((t) => !existingTitles.includes(t));
    missingBox.innerHTML = missing.length ? missing.map((t) => `<a href="/create/?title=${encodeURIComponent(t)}">Create "${t}"</a>`).join(' · ') : '<span class="muted">No missing links</span>';
  }

  function debounce(fn, wait) { let t; return function (...args) { clearTimeout(t); t = setTimeout(() => fn.apply(this, args), wait); }; }
  async function renderServer(md) {
    try {
      const res = await fetch('/api/notes/preview/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: md || '' }) });
      if (!res.ok) return '';
      const data = await res.json();
      return data.html || '';
    } catch { return ''; }
  }

  function startEdit() {
    if (!contentEl || !viewBox || !editorBox) return;
    const currentTitle = (titleEl?.textContent || '').trim();
    const currentContent = contentEl.textContent || '';

    editorBox.innerHTML = `
      <div>
        <div style="display:flex; align-items:center; justify-content: space-between; gap:.5rem;">
          <div>
            <label class="muted" for="ie-title">Title</label>
            <input id="ie-title" type="text" value="${currentTitle.replace(/\"/g, '&quot;')}">
          </div>
          <div class="toggle" role="tablist" aria-label="Editor mode">
            <button id="mode-rendered" class="active" type="button">Rendered</button>
            <button id="mode-markdown" type="button">Markdown</button>
          </div>
        </div>
        <div id="edit-rendered" class="preview content" contenteditable="true" style="margin-top:.5rem;"></div>
        <textarea id="edit-markdown" style="display:none; width:100%; min-height:260px; margin-top:.5rem;"></textarea>
        <div style="margin-top:.5rem; display:flex; gap:.5rem;">
          <button id="ie-save" class="btn btn-primary">Save</button>
          <button id="ie-cancel" class="btn btn-ghost">Cancel</button>
        </div>
        <div class="muted" style="margin-top:.5rem;">Missing links: <span id="ie-missing"></span></div>
      </div>
    `;

    const tInput = editorBox.querySelector('#ie-title');
    const wys = editorBox.querySelector('#edit-rendered');
    const ta = editorBox.querySelector('#edit-markdown');
    const miss = editorBox.querySelector('#ie-missing');
    const btnSave = editorBox.querySelector('#ie-save');
    const btnCancel = editorBox.querySelector('#ie-cancel');
    const btnRendered = editorBox.querySelector('#mode-rendered');
    const btnMarkdown = editorBox.querySelector('#mode-markdown');

    let mdText = currentContent;

    async function setRenderedFromMd() { wys.innerHTML = await renderServer(mdText); }
    function stripTags(x) { return (x || '').replace(/<[^>]+>/g, ''); }
    function htmlToMd(html) {
      let s = html;
      s = s.replace(/<a[^>]*data-wikilink=\"([^\"]+)\"[^>]*>[^<]*<\/a>/gi, (_, t) => `[[${t}]]`);
      s = s.replace(/<h1[^>]*>([\s\S]*?)<\/h1>/gi, (_, t) => `# ${stripTags(t)}`);
      s = s.replace(/<h2[^>]*>([\s\S]*?)<\/h2>/gi, (_, t) => `## ${stripTags(t)}`);
      s = s.replace(/<h3[^>]*>([\s\S]*?)<\/h3>/gi, (_, t) => `### ${stripTags(t)}`);
      s = s.replace(/<strong[^>]*>([\s\S]*?)<\/strong>/gi, (_, t) => `**${stripTags(t)}**`);
      s = s.replace(/<em[^>]*>([\s\S]*?)<\/em>/gi, (_, t) => `*${stripTags(t)}*`);
      s = s.replace(/<code[^>]*>([\s\S]*?)<\/code>/gi, (_, t) => `\`${stripTags(t)}\``);
      s = s.replace(/<a[^>]*href=\"([^\"]+)\"[^>]*>([\s\S]*?)<\/a>/gi, (_, href, t) => `${stripTags(t)}`);
      s = s.replace(/<br\s*\/?>/gi, '\n');
      s = s.replace(/<p[^>]*>([\s\S]*?)<\/p>/gi, (_, t) => `${stripTags(t)}\n\n`);
      s = stripTags(s);
      s = s.replace(/\n{3,}/g, '\n\n');
      return s.trim();
    }

    const updateMissingFromMd = function () {
      const titles = extractTitles(mdText || '');
      const missing = titles.filter((tt) => !existingTitles.includes(tt) && tt !== (tInput.value || ''));
      miss.innerHTML = missing.length ? missing.map((tt) => `<a href="/create/?title=${encodeURIComponent(tt)}">Create \"${tt}\"</a>`).join(' · ') : '<span class="muted">No missing links</span>';
    };

    async function switchToRendered() {
      btnRendered.classList.add('active');
      btnMarkdown.classList.remove('active');
      ta.style.display = 'none';
      wys.style.display = '';
      await setRenderedFromMd();
      updateMissingFromMd();
      wys.focus();
    }
    function switchToMarkdown() {
      btnMarkdown.classList.add('active');
      btnRendered.classList.remove('active');
      wys.style.display = 'none';
      ta.style.display = '';
      ta.value = mdText;
      updateMissingFromMd();
      ta.focus();
    }

    function stopEdit() { editorBox.style.display = 'none'; viewBox.style.display = ''; if (titleEl) titleEl.style.display = ''; }
    async function save() {
      const noteId = window.NOTE_ID; if (!noteId) return; btnSave.disabled = true;
      try {
        const res = await fetch(`/api/notes/${noteId}/`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: tInput.value || '', content: mdText || '' }) });
        if (!res.ok) throw new Error('Save failed'); location.reload();
      } catch (e) { alert('Failed to save. Please try again.'); btnSave.disabled = false; }
    }

    wys.addEventListener('input', () => { mdText = htmlToMd(wys.innerHTML); updateMissingFromMd(); });
    ta.addEventListener('input', () => { mdText = ta.value || ''; updateMissingFromMd(); });
    tInput.addEventListener('input', updateMissingFromMd);
    btnCancel.addEventListener('click', (e) => { e.preventDefault(); stopEdit(); });
    btnSave.addEventListener('click', (e) => { e.preventDefault(); save(); });
    ta.addEventListener('keydown', (e) => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') { e.preventDefault(); save(); } if (e.key === 'Escape') { e.preventDefault(); stopEdit(); } });
    wys.addEventListener('keydown', (e) => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') { e.preventDefault(); save(); } if (e.key === 'Escape') { e.preventDefault(); stopEdit(); } });
    btnRendered.addEventListener('click', switchToRendered);
    btnMarkdown.addEventListener('click', switchToMarkdown);

    viewBox.style.display = 'none'; if (titleEl) titleEl.style.display = 'none'; editorBox.style.display = '';
    switchToRendered();
  }

  if (viewBox) viewBox.addEventListener('click', startEdit);
  if (titleEl) titleEl.addEventListener('click', startEdit);
})();
