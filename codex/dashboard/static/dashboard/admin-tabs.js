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
  const tabs = [...dashboard.querySelectorAll('[data-admin-tab]')];
  const panels = [...dashboard.querySelectorAll('[data-admin-panel]')];
  function activate(id, focus = false) {
    const selected = tabs.find(tab => tab.dataset.adminTab === id) || tabs[0];
    tabs.forEach(tab => {
      tab.setAttribute('aria-selected', String(tab === selected));
      tab.tabIndex = tab === selected ? 0 : -1;
    });
    panels.forEach(panel => { panel.hidden = panel.id !== selected.dataset.adminTab; });
    if (focus) selected.focus();
    window.CodexAdmin.setTab(selected.dataset.adminTab);
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

  activate(window.CodexAdmin.state.tab);
  window.addEventListener('hashchange', () => {
    const tab = window.location.hash.slice(1);
    if (tabs.some(item => item.dataset.adminTab === tab)) activate(tab);
  });

});
