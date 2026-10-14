(() => {
  const initialized = new WeakSet();
  function initialize() {
    const manager = document.querySelector('[data-wiki-manager]');
    if (!manager || initialized.has(manager)) return;
    initialized.add(manager);
    const admin = window.CodexAdmin;
    const catalog = manager.querySelector('[data-wiki-catalog-scroll]');
    const detail = manager.querySelector('[data-wiki-detail]');
    const key = 'codex-wiki-catalog';
    const previews = new Map([...manager.querySelectorAll('[data-wiki-detail-template]')]
      .map(template => [template.dataset.wikiDetailTemplate, template.content]));
    const initialItem = detail.querySelector('[data-wiki-item]')?.dataset.wikiItem;
    if (initialItem && !previews.has(initialItem)) previews.set(initialItem, detail.cloneNode(true));

    function filterIdentity() {
      return {filter: manager.querySelector('[name="wiki_section"]')?.value || '', query: manager.querySelector('[name="wiki_q"]')?.value || ''};
    }
    function rememberCatalog() {
      try {
        sessionStorage.setItem(key, JSON.stringify({...filterIdentity(), scroll: catalog.scrollTop,
          open: [...manager.querySelectorAll('[data-wiki-group][open]')].map(group => group.dataset.wikiGroup)}));
      } catch (_) {}
    }
    function show(id) {
      if (!previews.has(id)) return false;
      const content = previews.get(id);
      detail.replaceChildren(...[...content.childNodes].map(node => node.cloneNode(true)));
      detail.scrollTop = 0;
      catalog.querySelectorAll('[data-wiki-select]').forEach(row => {
        const selected = row.dataset.wikiSelect === id;
        row.classList.toggle('is-selected', selected);
        if (selected) { row.setAttribute('aria-current', 'true'); row.closest('details').open = true; }
        else row.removeAttribute('aria-current');
      });
      const name = detail.querySelector('.wiki-manager-item-title h3')?.textContent;
      manager.querySelector('[data-wiki-selection-status]').textContent = name ? `${name} selecionado.` : '';
      admin.setWiki({mode: '', selected: id, category: ''});
      return true;
    }

    manager.addEventListener('submit', rememberCatalog);
    manager.addEventListener('click', event => {
      const link = event.target.closest('a');
      if (!link || event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      rememberCatalog();
      const id = link.dataset.wikiSelect;
      if (id && previews.has(id)) {
        event.preventDefault();
        if (detail.querySelector('[data-wiki-item]')?.dataset.wikiItem !== id) show(id);
        if (matchMedia('(max-width: 800px)').matches) detail.scrollIntoView({block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
        return;
      }
      const url = new URL(link.href);
      if (url.origin === location.origin && url.pathname === admin.baseUrl) {
        event.preventDefault();
        admin.setWiki({mode: url.searchParams.get('wiki_action') || '', selected: url.searchParams.get('wiki_id') || url.searchParams.get('wiki_selected') || '', category: url.searchParams.get('wiki_category') || ''});
        admin.load('wiki_panel', url);
      }
    });

    if (!admin.state.wiki.mode && admin.state.wiki.selected) show(admin.state.wiki.selected);
    if (!admin.state.wiki.mode) admin.setWiki({mode: '', selected: detail.querySelector('[data-wiki-item]')?.dataset.wikiItem || '', category: ''});
    requestAnimationFrame(() => {
      try {
        const saved = JSON.parse(sessionStorage.getItem(key) || 'null');
        const filters = filterIdentity();
        if (saved && saved.filter === filters.filter && saved.query === filters.query) {
          manager.querySelectorAll('[data-wiki-group]').forEach(group => { if (saved.open.includes(group.dataset.wikiGroup)) group.open = true; });
          catalog.scrollTop = saved.scroll;
        }
      } catch (_) {}
    });
  }
  document.addEventListener('DOMContentLoaded', initialize);
  document.addEventListener('admin:panelupdated', event => { if (event.detail.tab === 'wiki_panel') initialize(); });
})();
