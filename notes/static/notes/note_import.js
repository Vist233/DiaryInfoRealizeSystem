/* Import from URL with optional summarize */
(function () {
  const form = document.getElementById('import-form');
  const input = document.getElementById('import-url');
  const summarize = document.getElementById('import-summarize');
  if (!form || !input) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = (input.value || '').trim();
    if (!/^https?:\/\//i.test(url)) { alert('Please enter a valid URL starting with http(s)://'); input.focus(); return; }
    try {
      const res = await fetch('/api/notes/import_url/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, summarize: !!summarize?.checked })
      });
      if (!res.ok) { const t = await res.text(); alert('Import failed: ' + t); return; }
      const data = await res.json();
      if (data.id) location.href = '/' + data.id + '/'; else location.reload();
    } catch (e) {
      alert('Network error.');
    }
  });
})();

