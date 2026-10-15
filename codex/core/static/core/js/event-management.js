(() => {
  const root = document.querySelector('[data-event-manager]');
  if (!root) return;
  const feedback = root.querySelector('[data-event-feedback]');
  let editorDirty = false, editorBusy = false;
  const notify = (message, error = false) => {
    feedback.textContent = message;
    feedback.hidden = false;
    feedback.classList.toggle('is-error', error);
    feedback.setAttribute('role', error ? 'alert' : 'status');
  };
  async function send(form, data) {
    let response;
    try {
      response = await fetch(form.getAttribute('action') || window.location.href, {method: 'POST', body: data, credentials: 'same-origin',
        headers: {'X-Event-Management': '1', 'X-CSRFToken': data.get('csrfmiddlewaretoken')}});
    } catch {
      throw new Error('Não foi possível comunicar com o servidor. As edições foram mantidas; tente novamente.');
    }
    if (response.status === 413) throw new Error('A capa excede o tamanho permitido pelo servidor. Escolha uma imagem menor; as outras edições foram mantidas.');
    if (response.redirected) {
      throw new Error('Não foi possível salvar. Sua sessão pode ter expirado; entre novamente em outra aba. As edições foram mantidas.');
    }
    if (!response.headers.get('Content-Type')?.includes('application/json')) throw new Error('Não foi possível salvar no momento. As edições foram mantidas; tente novamente.');
    return response.json();
  }
  const editorSignature = form => JSON.stringify([...new FormData(form)].filter(([name]) => name !== 'csrfmiddlewaretoken').map(([name, value]) => [name, value instanceof File ? (value.name ? `${value.name}:${value.size}:${value.lastModified}` : '') : value]));
  let editorBaseline = '';
  const clearEditorErrors = form => {
    form.querySelectorAll('.em-field-error, [data-event-form-errors]').forEach(element => element.textContent = '');
    form.querySelectorAll('[aria-invalid]').forEach(element => element.removeAttribute('aria-invalid'));
  };
  let previewUrl;
  function releasePreview() { if (previewUrl) URL.revokeObjectURL(previewUrl); previewUrl = null; }
  function bindEditor(form) {
    if (!form) return;
    editorBaseline = editorSignature(form);
    form.addEventListener('input', () => { editorDirty = editorSignature(form) !== editorBaseline; });
    form.addEventListener('change', event => {
      editorDirty = editorSignature(form) !== editorBaseline;
      if (event.target.name !== 'capa') return;
      const preview = form.querySelector('[data-event-cover-preview]');
      releasePreview();
      const file = event.target.files[0];
      if (file && file.type.startsWith('image/')) {
        previewUrl = URL.createObjectURL(file);
        preview.querySelector('img').src = previewUrl;
        preview.hidden = false;
        const clear = form.querySelector('[name="capa-clear"]');
        if (clear) clear.checked = false;
      } else preview.hidden = true;
    });
    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (editorBusy) return;
      const data = new FormData(form), controls = [...form.querySelectorAll('input,select,textarea,button')];
      const previous = controls.map(control => control.disabled);
      const button = form.querySelector('[type=submit]'), buttonText = button.textContent;
      editorBusy = true;
      form.setAttribute('aria-busy', 'true');
      controls.forEach(control => control.disabled = true);
      button.textContent = 'Salvando…';
      clearEditorErrors(form);
      try {
        const result = await send(form, data);
        if (!result.ok) {
          Object.entries(result.errors || {}).forEach(([name, errors]) => {
            const field = form.elements.namedItem(name);
            const target = name === '__all__' ? form.querySelector('[data-event-form-errors]') : field?.closest('.em-editor-field')?.querySelector('.em-field-error');
            if (target) target.textContent = errors.join(' ');
            field?.setAttribute?.('aria-invalid', 'true');
          });
          notify(result.message, true);
          return;
        }
        releasePreview();
        root.querySelector('[data-event-summary]').outerHTML = result.summary;
        const host = root.querySelector('[data-event-editor-host]');
        host.innerHTML = result.editor;
        root.querySelectorAll('[data-event-title]').forEach(element => element.textContent = result.title);
        document.title = `Gerenciar ${result.title} | Codex`;
        editorDirty = false;
        bindEditor(host.querySelector('form'));
        root.querySelector('#editar-evento').open = false;
        notify(result.message);
      } catch (error) {
        notify(error.message || 'Não foi possível comunicar com o servidor. As edições foram mantidas; tente novamente.', true);
      } finally {
        editorBusy = false;
        controls.forEach((control, index) => control.disabled = previous[index]);
        form.removeAttribute('aria-busy');
        button.textContent = buttonText;
      }
    });
  }
  bindEditor(root.querySelector('[data-event-editor]'));
  root.addEventListener('click', async event => {
    if (event.target.closest('[data-open-event-edit]')) {
      event.preventDefault();
      const section = root.querySelector('#editar-evento');
      section.open = true;
      section.scrollIntoView({block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
    }
    if (event.target.closest('[data-cancel-event-edit]')) {
      const form = root.querySelector('[data-event-editor]');
      form.reset();
      releasePreview();
      form.querySelector('[data-event-cover-preview]').hidden = true;
      clearEditorErrors(form);
      editorDirty = false;
      root.querySelector('#editar-evento').open = false;
    }
    if (event.target.closest('[data-event-delete]')) root.querySelector('#delete-event-dialog').showModal();
    if (event.target.closest('[data-close-event-dialog]')) event.target.closest('dialog').close();
    const copy = event.target.closest('[data-event-copy]');
    if (copy) {
      try { await navigator.clipboard.writeText(copy.dataset.eventCopy); notify('Link de inscrição copiado.'); }
      catch { root.querySelector('#event-signup-link')?.select(); notify('Selecione e copie o link de inscrição.'); }
    }
  });
  root.querySelectorAll('dialog').forEach(dialog => dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); }));
  const participants = root.querySelector('[data-event-participants]');
  if (!participants) {
    window.addEventListener('beforeunload', event => { if (editorDirty || editorBusy) { event.preventDefault(); event.returnValue = ''; } });
    return;
  }
  const form = participants.querySelector('[data-participant-form]');
  const rows = [...form.querySelectorAll('[data-participant-row]')];
  const search = participants.querySelector('[data-participant-search]');
  const filters = [...participants.querySelectorAll('[data-participant-filter]')];
  const desktop = matchMedia('(min-width: 1201px)');
  const detail = participants.querySelector('[data-participant-detail]');
  const dialog = participants.querySelector('[data-participant-dialog]');
  const dialogContent = participants.querySelector('[data-participant-dialog-content]');
  const save = form.querySelector('[data-participant-save]'), reset = form.querySelector('[data-participant-reset]');
  let selected = null, busy = false, conflicts = [];
  const fields = row => [...row.querySelectorAll('[data-event-field]')];
  const normalized = text => text.toLowerCase().normalize('NFD').replace(/\p{Diacritic}/gu, '');
  function isChanged(input) {
    if (input.type === 'checkbox') return Number(input.checked) !== Number(input.dataset.initial);
    if (input.value.trim() === '') return true;
    return Number(input.value.replace(',', '.')) !== Number(input.dataset.initial);
  }
  const changes = row => fields(row).filter(isChanged).map(input => input.dataset.eventField);
  const dirtyRows = () => rows.filter(row => changes(row).length);
  function updateStateLabels(row) {
    ['taxa_paga', 'presenca'].forEach(name => {
      const input = row.querySelector(`[data-event-field="${name}"]`);
      row.querySelector(`[data-state-text="${name}"]`).textContent = name === 'taxa_paga' ? (input.checked ? 'Pago' : 'Pendente') : (input.checked ? 'Confirmada' : 'Não confirmada');
    });
    if (selected === row) updateDetailStatus();
  }
  function updateDetailStatus() {
    if (!selected) return;
    for (const host of [detail, dialogContent]) {
      const paid = selected.querySelector('[data-event-field="taxa_paga"]').checked;
      const present = selected.querySelector('[data-event-field="presenca"]').checked;
      const paidBadge = host.querySelector('[data-detail-paid]'), presenceBadge = host.querySelector('[data-detail-presence]');
      if (paidBadge) { paidBadge.textContent = paid ? 'Taxa paga' : 'Taxa pendente'; paidBadge.classList.toggle('is-green', paid); }
      if (presenceBadge) { presenceBadge.textContent = present ? 'Presença confirmada' : 'Presença não confirmada'; presenceBadge.classList.toggle('is-green', present); }
    }
  }
  function select(row, open = false) {
    selected = row;
    for (const item of rows) {
      item.classList.toggle('is-selected', item === row);
      item.querySelector('[data-open-participant]').setAttribute('aria-pressed', String(item === row));
    }
    if (row) {
      const template = participants.querySelector(`[data-participant-template="${row.dataset.participantRow}"]`);
      detail.replaceChildren(template.content.cloneNode(true));
      dialogContent.replaceChildren(template.content.cloneNode(true));
      updateDetailStatus();
      if (open && !desktop.matches && !dialog.open) dialog.showModal();
    } else {
      const empty = document.createElement('p'); empty.className = 'em-muted'; empty.textContent = 'Nenhum participante corresponde aos filtros.';
      detail.replaceChildren(empty);
    }
  }
  function updateDirty() {
    const dirty = dirtyRows(), hidden = dirty.filter(row => row.hidden).length;
    rows.forEach(row => row.classList.toggle('is-dirty', changes(row).length > 0));
    if (save) {
      save.disabled = busy || !dirty.length;
      reset.disabled = busy || !dirty.length;
      form.querySelector('[data-participant-dirty]').textContent = busy ? 'Salvando alterações…' : dirty.length ? `${dirty.length} participante${dirty.length === 1 ? '' : 's'} com alterações${hidden ? ` (${hidden} fora do filtro)` : ''}` : 'Todas as alterações estão salvas';
      form.querySelector('[data-participant-save-hint]').textContent = dirty.length ? 'Revise os valores antes de salvar. Use Tab para avançar.' : 'XP pertence ao jogador; ouro pertence ao personagem.';
    }
  }
  function applyFilters() {
    const term = normalized(search.value.trim());
    const values = Object.fromEntries(filters.map(input => [input.dataset.participantFilter, input.value]));
    rows.forEach(row => {
      row.hidden = !normalized(row.dataset.participantSearchText).includes(term)
        || (values.payment === 'paid' && row.dataset.savedPaid !== '1')
        || (values.payment === 'pending' && row.dataset.savedPaid !== '0')
        || (values.presence === 'present' && row.dataset.savedPresence !== '1')
        || (values.presence === 'absent' && row.dataset.savedPresence !== '0')
        || (values.guild !== 'all' && row.dataset.guild !== values.guild);
    });
    const visible = rows.filter(row => !row.hidden);
    participants.querySelector('[data-participant-count]').textContent = `Exibindo ${visible.length} de ${rows.length} participantes`;
    participants.querySelector('[data-participant-no-results]').hidden = visible.length > 0 || !rows.length;
    participants.querySelector('[data-clear-participant-filters]').hidden = !term && filters.every(input => input.value === 'all');
    if (!selected || selected.hidden) select(visible[0] || null);
    updateDirty();
  }
  function clearFilters() { search.value = ''; filters.forEach(input => input.value = 'all'); applyFilters(); }
  function updateSavedRow(row, data) {
    for (const input of fields(row)) {
      const value = data[input.dataset.eventField];
      if (input.type === 'checkbox') input.checked = Boolean(value);
      else input.value = value;
      input.dataset.initial = typeof value === 'boolean' ? String(Number(value)) : String(value);
      input.removeAttribute('aria-invalid');
    }
    const previous = {xp_anterior: data.xp, ouro_anterior: data.ouro, taxa_anterior: Number(data.taxa_paga), presenca_anterior: Number(data.presenca)};
    Object.entries(previous).forEach(([name, value]) => row.querySelector(`[name$="-${name}"]`).value = value);
    row.dataset.savedPaid = String(Number(data.taxa_paga));
    row.dataset.savedPresence = String(Number(data.presenca));
    row.querySelectorAll('[data-error-for]').forEach(element => element.textContent = '');
    updateStateLabels(row);
  }
  participants.querySelector('[data-event-filters]').hidden = false;
  search.addEventListener('input', applyFilters);
  filters.forEach(input => input.addEventListener('change', applyFilters));
  participants.querySelector('[data-clear-participant-filters]').addEventListener('click', clearFilters);
  participants.addEventListener('click', event => {
    const button = event.target.closest('[data-open-participant]'), row = event.target.closest('[data-participant-row]');
    if (button) select(row, true);
    else if (row && desktop.matches && !event.target.closest('input,label,a,select')) select(row);
  });
  form.addEventListener('input', event => {
    const row = event.target.closest('[data-participant-row]');
    if (!row) return;
    const name = event.target.dataset.eventField;
    if (name) { row.querySelector(`[data-error-for="${name}"]`).textContent = ''; event.target.removeAttribute('aria-invalid'); }
    updateStateLabels(row); updateDirty();
  });
  form.addEventListener('reset', event => {
    event.preventDefault();
    if (busy) return;
    rows.forEach(row => {
      const data = Object.fromEntries(fields(row).map(input => [input.dataset.eventField, input.type === 'checkbox' ? Boolean(Number(input.dataset.initial)) : input.dataset.initial]));
      updateSavedRow(row, data);
    });
    applyFilters();
    notify('As alterações não salvas foram desfeitas.');
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const dirty = dirtyRows();
    if (busy || !dirty.length) return;
    const data = new FormData(form), ids = new Set(dirty.map(row => row.dataset.participantRow));
    rows.forEach(row => {
      if (!ids.has(row.dataset.participantRow)) row.querySelectorAll('[name]').forEach(input => data.delete(input.name));
      else { data.append('registration_ids', row.dataset.participantRow); changes(row).forEach(name => data.append(`changed_fields_${row.dataset.participantRow}`, name)); }
    });
    busy = true;
    form.setAttribute('aria-busy', 'true');
    form.querySelector('[data-participant-fieldset]').disabled = true;
    updateDirty();
    try {
      const result = await send(form, data);
      if (!result.ok) {
        notify(result.message, true);
        conflicts = result.conflicts || [];
        form.querySelector('[data-refresh-participant-conflicts]').hidden = !conflicts.length;
        Object.entries(result.errors || {}).forEach(([id, errors]) => {
          const row = rows.find(row => row.dataset.participantRow === id);
          if (!row) return;
          Object.entries(errors).forEach(([name, messages]) => {
            const target = row.querySelector(`[data-error-for="${name}"]`);
            if (target) target.textContent = messages.join(' ');
            row.querySelector(`[data-event-field="${name}"]`)?.setAttribute('aria-invalid', 'true');
          });
        });
        return;
      }
      result.rows.forEach(data => { const row = rows.find(row => row.dataset.participantRow === String(data.id)); if (row) updateSavedRow(row, data); });
      root.querySelectorAll('[data-event-metric]').forEach(element => element.textContent = result.metrics[element.dataset.eventMetric]);
      conflicts = [];
      form.querySelector('[data-refresh-participant-conflicts]').hidden = true;
      notify(result.message);
      applyFilters();
    } catch (error) {
      notify(error.message || 'Não foi possível comunicar com o servidor. As edições foram mantidas; tente novamente.', true);
    } finally {
      busy = false;
      form.querySelector('[data-participant-fieldset]').disabled = false;
      form.removeAttribute('aria-busy');
      updateDirty();
    }
  });
  form.querySelector('[data-refresh-participant-conflicts]').addEventListener('click', () => {
    conflicts.forEach(data => { const row = rows.find(row => row.dataset.participantRow === String(data.id)); if (row) updateSavedRow(row, data); });
    conflicts = [];
    form.querySelector('[data-refresh-participant-conflicts]').hidden = true;
    applyFilters(); notify('Os participantes em conflito foram recarregados. As outras edições continuam disponíveis.');
  });
  desktop.addEventListener('change', () => { if (desktop.matches && dialog.open) dialog.close(); });
  rows.forEach(updateStateLabels);
  applyFilters();
  window.addEventListener('beforeunload', event => { if (busy || dirtyRows().length) { event.preventDefault(); event.returnValue = ''; } });
})();
