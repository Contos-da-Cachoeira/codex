(() => {
  const dashboard = document.querySelector('[data-admin-dashboard]');
  if (!dashboard) return;
  const baseUrl = dashboard.dataset.adminBaseUrl;
  const storageKey = `codex-admin:${dashboard.dataset.adminUserId}`;
  const tabIds = new Set([...dashboard.querySelectorAll('[data-admin-tab]')].map(tab => tab.dataset.adminTab));
  const legacyTabs = {open_users_modal: 'user_roles_modal', open_personagens_modal: 'character_modal',
    open_larps_modal: 'larp_modal', open_home_components_modal: 'home_components_modal', open_theme_modal: 'theme_modal', open_social_modal: 'social_modal'};
  let saved = {};
  try { saved = JSON.parse(sessionStorage.getItem(storageKey) || '{}') || {}; } catch (_) {}
  const params = new URLSearchParams(location.search);
  const legacyTab = Object.keys(legacyTabs).find(key => params.get(key) === '1');
  const hashTab = location.hash.slice(1);
  const state = {tab: tabIds.has(hashTab) ? hashTab : legacyTab ? legacyTabs[legacyTab] : dashboard.dataset.adminInitialTab || saved.tab || 'overview',
    records: {...saved.records}, wiki: {...saved.wiki}};
  for (const [kind, parameter] of Object.entries({users: 'selected_user', characters: 'selected_character', larps: 'selected_larp'})) {
    if (params.has(parameter)) state.records[kind] = params.get(parameter);
  }
  if (params.get('new_larp') === '1') state.records.larps = 'new';
  if (params.has('wiki_action') || params.has('wiki_selected')) {
    state.wiki = {mode: params.get('wiki_action') || '', selected: params.get('wiki_id') || params.get('wiki_selected') || '', category: params.get('wiki_category') || ''};
  }
  const controllers = new Map(), versions = new Map(), submitting = new WeakSet();

  function persist() {
    try { sessionStorage.setItem(storageKey, JSON.stringify({tab: state.tab, records: state.records, wiki: {selected: state.wiki.selected || ''}})); } catch (_) {}
  }
  function cleanUrl() { if (location.pathname === baseUrl && (location.search || location.hash)) history.replaceState(null, '', baseUrl); }
  function notice(text, error = false) {
    const feedback = dashboard.querySelector('[data-admin-feedback]');
    feedback.textContent = text;
    feedback.className = `alert ${error ? 'alert-error' : 'alert-success'}`;
    feedback.hidden = !text;
  }
  function applyTheme(theme) {
    for (const [key, value] of Object.entries(theme || {})) {
      const variable = key === 'site_muted_text_color' ? '--site-muted' : key.startsWith('site_') ? '--' + key.replace(/_color$/, '').replaceAll('_', '-') : '--color-' + key.replace(/_color$/, '').replaceAll('_', '-');
      document.documentElement.style.setProperty(variable, value);
    }
  }
  async function requestPanel(tab, url, options = {}) {
    const version = (versions.get(tab) || 0) + 1;
    versions.set(tab, version);
    const requestedState = JSON.stringify(state);
    let response;
    try {
      response = await fetch(url, {credentials: 'same-origin', ...options.fetch,
        headers: {'X-Admin-Panel': tab, 'Accept': 'application/json', ...options.fetch?.headers}});
    } catch (_) { throw new Error('Não foi possível comunicar com o servidor. Seus campos foram mantidos; tente salvar novamente.'); }
    if (!(response.headers.get('Content-Type') || '').includes('application/json')) throw new Error('Não foi possível atualizar o painel. Seus campos foram mantidos; confira se sua sessão continua ativa.');
    const payload = await response.json();
    if (!response.ok || payload.error) throw new Error(payload.error || 'Não foi possível salvar. Seus campos foram mantidos.');
    if (payload.panel !== tab || typeof payload.html !== 'string') throw new Error('O servidor não retornou o painel solicitado. Seus campos foram mantidos.');
    if (versions.get(tab) !== version) return;
    const panel = document.getElementById(tab);
    const content = document.createElement('template');
    content.innerHTML = payload.html;
    content.content.querySelectorAll('script').forEach(script => script.remove());
    const controller = controllers.get(tab);
    const handled = controller?.update?.(content.content, payload, options);
    if (!handled) {
      // Keep a newly chosen wiki item if a save finishes after the user switched items.
      if (tab === 'wiki_panel' && options.operation !== 'filter' && requestedState !== JSON.stringify(state) && state.wiki.mode === '') {
        payload.state = {...state.wiki};
      }
      panel.replaceChildren(content.content);
      if (tab === 'wiki_panel') state.wiki = payload.state;
      document.dispatchEvent(new CustomEvent('admin:panelupdated', {detail: {tab, payload}}));
    }
    applyTheme(payload.theme);
    persist(); cleanUrl();
    if (payload.messages?.length) notice(payload.messages.map(message => message.text).join(' '), payload.messages.some(message => message.tags.includes('error')));
    else if (payload.invalid) notice('Confira os campos indicados no formulário.', true);
    else if (options.operation === 'save') notice('Alterações salvas.');
  }

  window.CodexAdmin = {
    state, baseUrl, register: (tab, controller) => controllers.set(tab, controller),
    setTab(tab) { state.tab = tabIds.has(tab) ? tab : 'overview'; persist(); cleanUrl(); },
    setRecord(kind, id) { state.records[kind] = id; persist(); },
    setWiki(next) { state.wiki = next; persist(); },
    async load(tab, url, operation = 'navigate') {
      try { await requestPanel(tab, url, {operation}); } catch (error) { notice(error.message, true); }
    },
  };
  persist(); cleanUrl();
  document.addEventListener('DOMContentLoaded', () => {
    dashboard.addEventListener('submit', async event => {
      if (event.defaultPrevented) return;
      const form = event.target;
      const panel = form.closest('[data-admin-panel]');
      if (!panel || panel.id === 'home_components_modal') return;
      event.preventDefault();
      if (submitting.has(form)) return;
      submitting.add(form);
      const button = event.submitter || form.querySelector('[type="submit"]');
      const originalText = button?.textContent;
      const get = (form.getAttribute('method') || 'get').toLowerCase() === 'get';
      if (button) { button.disabled = true; button.textContent = get ? 'Filtrando…' : 'Salvando…'; }
      try {
        const body = new FormData(form);
        if (event.submitter?.name) body.append(event.submitter.name, event.submitter.value);
        // A hidden input named "action" shadows HTMLFormElement.action.
        const url = new URL(form.getAttribute('action') || baseUrl, location.origin);
        url.hash = '';
        if (get) url.search = new URLSearchParams(body).toString();
        await requestPanel(panel.id, url, {operation: get ? 'filter' : 'save', submitted: body,
          fetch: get ? {} : {method: 'POST', body}});
      } catch (error) { notice(error.message, true); }
      finally {
        submitting.delete(form);
        if (button) { button.disabled = false; button.textContent = originalText; }
      }
    });
  });
})();
