/* Quick create via API and simple UX touches */
(function () {
  const form = document.getElementById('qc-form');
  const input = document.getElementById('qc-title');
  if (!form || !input) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = (input.value || '').trim();
    if (!title) { input.focus(); return; }
    try {
      const res = await fetch('/api/notes/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title })
      });
      if (!res.ok) {
        const t = await res.text();
        alert('Create failed: ' + t);
        return;
      }
      // reload to show the new note at top
      location.href = '/';
    } catch (e) {
      alert('Network error.');
    }
  });
})();

