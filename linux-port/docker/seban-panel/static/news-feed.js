(() => {
  const list = document.getElementById('news-feed');
  if (!list) return;
  const storageKey = 'seban-panel-news-seen';
  let seen;
  try { seen = new Set(JSON.parse(sessionStorage.getItem(storageKey) || '[]')); } catch (_) { seen = new Set(); }
  const escape = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  async function refresh() {
    try {
      const data = await fetch('/api/news-feed', {cache: 'no-store'}).then(response => response.json());
      if (!data.ok) return;
      const fresh = data.events.filter(event => !seen.has(event.key));
      if (!fresh.length) return;
      fresh.forEach(event => seen.add(event.key));
      const capped = [...seen].slice(-500);
      sessionStorage.setItem(storageKey, JSON.stringify(capped));
      list.innerHTML = fresh.slice(-8).map(event => `<li><time>${escape(event.time)}</time><span>${escape(event.message)}</span></li>`).join('');
    } catch (_) {
      list.innerHTML = '<li class="muted">Feed wydarzeń jest chwilowo niedostępny.</li>';
    }
  }
  refresh();
  setInterval(refresh, 30000);
})();
