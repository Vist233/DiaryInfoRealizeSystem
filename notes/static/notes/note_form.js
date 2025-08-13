/* Server-rendered preview with wikilink suggestions */
(function () {
  const textarea = document.querySelector('textarea#id_content');
  const preview = document.getElementById('preview');
  const missingBox = document.getElementById('missing-links');
  const existingTitles = (window.EXISTING_TITLES || []).map((s) => (s || '').trim()).filter(Boolean);

  function debounce(fn, wait) { let t; return function (...args) { clearTimeout(t); t = setTimeout(() => fn.apply(this, args), wait); }; }

  async function renderServer(md) {
    try {
      const res = await fetch('/api/notes/preview/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: md || '' })
      });
      if (!res.ok) return '';
      const data = await res.json();
      return data.html || '';
    } catch { return ''; }
  }

  const update = debounce(async function () {
    if (preview) preview.innerHTML = await renderServer(textarea.value || '');
    updateMissing();
  }, 250);

  function extractTitles(md) {
    const set = new Set();
    (md.match(/\[\[([^\[\]]+)\]\]/g) || []).forEach((w) => {
      const t = w.slice(2, -2).trim();
      if (t) set.add(t);
    });
    return Array.from(set.values());
  }

  function updateMissing() {
    if (!missingBox) return;
    const titles = extractTitles(textarea.value || '');
    const missing = titles.filter((t) => !existingTitles.includes(t) && (document.querySelector('#id_title')?.value || '') !== t);
    if (!missing.length) { missingBox.innerHTML = '<span class="muted">No missing links</span>'; return; }
    missingBox.innerHTML = missing.map((t) => `<a href="/create/?title=${encodeURIComponent(t)}">Create "${t}"</a>`).join(' · ');
  }

  if (textarea) {
    textarea.addEventListener('input', update);
    update();
  }
})();

