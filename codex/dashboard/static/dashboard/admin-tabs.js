document.addEventListener('DOMContentLoaded', () => {
  const dashboard = document.querySelector('[data-admin-dashboard]');
  if (!dashboard) return;
  const componentsEditor = dashboard.querySelector('.home-components-editor');
  if (componentsEditor) {
    componentsEditor.addEventListener('invalid', event => {
      const component = event.target.closest('details');
      if (component) component.open = true;
    }, true);
  }
  const eventFormToggle = dashboard.querySelector('[data-toggle-event-form]');
  const eventForm = dashboard.querySelector('#larp-create-form');
  if (eventFormToggle && eventForm) {
    eventFormToggle.addEventListener('click', () => {
      eventForm.hidden = !eventForm.hidden;
      eventFormToggle.setAttribute('aria-expanded', String(!eventForm.hidden));
      eventFormToggle.textContent = eventForm.hidden ? 'Criar novo evento' : 'Minimizar formulário';
      eventFormToggle.classList.toggle('btn-primary', eventForm.hidden);
      eventFormToggle.classList.toggle('btn-outline', !eventForm.hidden);
    });
  }
  const tabs = [...dashboard.querySelectorAll('[data-admin-tab]')];
  const panels = [...dashboard.querySelectorAll('[data-admin-panel]')];
  const legacyTabs = {
    open_users_modal: 'user_roles_modal',
    open_personagens_modal: 'character_modal',
    open_larps_modal: 'larp_modal',
    open_home_components_modal: 'home_components_modal',
    open_theme_modal: 'theme_modal',
    open_social_modal: 'social_modal',
  };

  function activate(id, focus = false, updateUrl = true) {
    const selected = tabs.find(tab => tab.dataset.adminTab === id) || tabs[0];
    tabs.forEach(tab => {
      tab.setAttribute('aria-selected', String(tab === selected));
      tab.tabIndex = tab === selected ? 0 : -1;
    });
    panels.forEach(panel => { panel.hidden = panel.id !== selected.dataset.adminTab; });
    if (focus) selected.focus();
    if (updateUrl) {
      const url = new URL(window.location.href);
      Object.keys(legacyTabs).forEach(key => url.searchParams.delete(key));
      url.hash = selected.dataset.adminTab;
      window.history.replaceState(null, '', url);
    }
  }

  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => activate(tab.dataset.adminTab));
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next === undefined) return;
      event.preventDefault();
      activate(tabs[next].dataset.adminTab, true);
    });
  });
  dashboard.querySelectorAll('[data-admin-target]').forEach(button => {
    button.addEventListener('click', () => activate(button.dataset.adminTarget, true));
  });

  const params = new URLSearchParams(window.location.search);
  const requested = Object.keys(legacyTabs).find(key => params.get(key) === '1');
  activate(requested ? legacyTabs[requested] : window.location.hash.slice(1));
  window.addEventListener('hashchange', () => activate(window.location.hash.slice(1), false, false));

  dashboard.querySelectorAll('[data-copy-link]').forEach(button => {
    button.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(button.dataset.copyLink);
        button.textContent = 'Copiado';
      } catch {
        button.textContent = 'Copie pelo link';
      }
      window.setTimeout(() => { button.textContent = 'Copiar link'; }, 1500);
    });
  });
});
