document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-record-manager]').forEach(manager => {
    let catalog = manager.querySelector('[data-record-scroll]');
    const detail = manager.querySelector('[data-record-detail]');
    let templates = new Map([...manager.querySelectorAll('[data-record-preview]')].map(template => [template.dataset.recordPreview, template.content]));
    const drafts = new Map();
    let firstId = manager.querySelector('[data-record-select]')?.dataset.recordSelect || 'empty';
    const initialId = detail.querySelector('[data-record-id]')?.dataset.recordId || 'empty';
    let activeId = initialId;

    function highlight(id) {
      manager.querySelectorAll('[data-record-select]').forEach(row => {
        const selected = row.dataset.recordSelect === id;
        row.classList.toggle('is-selected', selected);
        if (selected) { row.setAttribute('aria-current', 'true'); row.closest('details').open = true; }
        else row.removeAttribute('aria-current');
      });
    }

    function show(id, scroll = false) {
      if (id === activeId || (!templates.has(id) && !drafts.has(id))) return;
      const previous = document.createDocumentFragment();
      while (detail.firstChild) previous.appendChild(detail.firstChild);
      drafts.set(activeId, previous);
      const content = drafts.get(id) || templates.get(id).cloneNode(true);
      detail.replaceChildren(content);
      activeId = id;
      window.CodexAdmin.setRecord(manager.dataset.recordManager, id);
      detail.scrollTop = 0;
      highlight(id);
      const title = detail.querySelector('h3')?.textContent;
      manager.querySelector('[data-record-announcement]').textContent = title ? `${title} selecionado.` : '';
      if (scroll && matchMedia('(max-width: 800px)').matches) detail.scrollIntoView({block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
    }

    manager.addEventListener('click', async event => {
      const target = event.target.closest('a, button');
      if (!target) return;
      if (target.matches('[data-record-select], [data-record-new]') && event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) {
        event.preventDefault();
        const id = target.matches('[data-record-new]') ? 'new' : target.dataset.recordSelect;
        show(id, true);
      } else if (target.matches('.admin-records-filters a') && event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) {
        event.preventDefault();
        window.CodexAdmin.load(manager.dataset.recordTab, target.href, 'filter');
      } else if (target.matches('[data-record-edit], [data-record-cancel]')) {
        if (activeId === 'new') { detail.querySelector('form')?.reset(); show(firstId); return; }
        const editing = target.matches('[data-record-edit]');
        const fields = detail.querySelector('[data-record-edit-fields]');
        if (!fields) return;
        if (!editing) fields.querySelector('form')?.reset();
        fields.hidden = !editing;
        detail.querySelector('[data-record-read-fields]').hidden = editing;
        detail.querySelector('[data-record-edit]').disabled = editing;
        detail.scrollTop = 0;
      } else if (target.matches('[data-record-copy]')) {
        try {
          await navigator.clipboard.writeText(target.dataset.recordCopy);
          target.textContent = 'Link copiado';
          setTimeout(() => { target.textContent = 'Copiar link'; }, 1800);
        } catch (_) { target.textContent = 'Selecione e copie o link acima'; }
      }
    });

    window.CodexAdmin.register(manager.dataset.recordTab, {
      update(fragment, payload, options) {
        const fresh = fragment.querySelector('[data-record-manager]');
        if (!fresh) return false;
        const openGroups = [...catalog.querySelectorAll('details[open] summary h3')].map(element => element.textContent);
        const scrollTop = catalog.scrollTop;
        const submittedId = options.submitted?.get('selected_record') || options.submitted?.get('event_id') || activeId;
        const selected = options.operation === 'filter' || activeId === submittedId ? payload.state.selected : activeId;
        const previous = document.createDocumentFragment();
        while (detail.firstChild) previous.appendChild(detail.firstChild);
        drafts.set(activeId, previous);
        if (options.operation === 'save') drafts.delete(submittedId);
        const freshCatalog = fresh.querySelector('.admin-records-catalog');
        manager.querySelector('.admin-records-catalog').replaceChildren(...freshCatalog.childNodes);
        catalog = manager.querySelector('[data-record-scroll]');
        firstId = manager.querySelector('[data-record-select]')?.dataset.recordSelect || 'empty';
        catalog.querySelectorAll('details').forEach(group => {
          if (openGroups.includes(group.querySelector('h3').textContent)) group.open = true;
        });
        manager.querySelectorAll('[data-record-preview]').forEach(template => template.remove());
        manager.append(...fresh.querySelectorAll('[data-record-preview]'));
        templates = new Map([...manager.querySelectorAll('[data-record-preview]')].map(template => [template.dataset.recordPreview, template.content]));
        activeId = null;
        show(templates.has(selected) || drafts.has(selected) ? selected : payload.state.selected);
        catalog.scrollTop = scrollTop;
        return true;
      },
    });

    const restored = window.CodexAdmin.state.records[manager.dataset.recordManager];
    if (restored && templates.has(restored)) show(restored);
    window.CodexAdmin.setRecord(manager.dataset.recordManager, activeId);
    requestAnimationFrame(() => {
      const selected = catalog.querySelector('[aria-current="true"]');
      if (selected && !manager.closest('[hidden]')) {
        const row = selected.getBoundingClientRect(), box = catalog.getBoundingClientRect();
        if (row.bottom > box.bottom) catalog.scrollTop += row.bottom - box.bottom;
      }
    });
  });
});
