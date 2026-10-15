document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('#personagem-form');
  if (!form) return;
  const read = id => JSON.parse(document.getElementById(id).textContent);
  const spells = read('magias-por-classe-data');
  const initial = read('magias-selecionadas-data');
  const rules = read('class-rules-data');
  const select = document.querySelector('#classe-select');
  const panels = [...form.querySelectorAll('[data-character-panel]')];
  const tabs = [...form.querySelectorAll('[data-character-tab]')];
  const counts = {'2': 3, '4': 3, '8': 4};
  let firstRender = true;
  function show(name) {
    panels.forEach(panel => panel.hidden = panel.dataset.characterPanel !== name);
    tabs.forEach(tab => tab.setAttribute('aria-selected', String(tab.dataset.characterTab === name)));
  }
  function spellValidity() {
    const inputs = [...form.querySelectorAll('.magia-checkbox')];
    const count = inputs.filter(input => input.checked).length;
    const required = counts[select.value] || 0;
    document.querySelector('#spell-count').textContent = required ? `${count} de ${required} magias escolhidas` : '';
    inputs.forEach(input => input.setCustomValidity(''));
    if (inputs.length && count !== required) inputs[0].setCustomValidity(`Escolha exatamente ${required} magias.`);
  }
  function render() {
    const id = select.value, data = rules[id];
    const options = document.querySelector('#magias-opcoes');
    options.replaceChildren();
    document.querySelector('#magias-wrapper').classList.toggle('hidden', !(spells[id] || []).length);
    const fixed = ['5', '9'].includes(id);
    document.querySelector('#magias-fixas-info').classList.toggle('hidden', !fixed);
    for (const spell of spells[id] || []) {
      const label = document.createElement('label');
      label.className = 'flex items-center gap-3 border border-base-300 rounded-lg px-3 py-2';
      const input = document.createElement('input');
      input.type = 'checkbox'; input.name = 'magias_pretendidas'; input.value = spell;
      input.className = 'checkbox checkbox-sm magia-checkbox';
      input.checked = fixed || (firstRender && initial.includes(spell));
      input.disabled = fixed;
      input.addEventListener('change', spellValidity);
      label.append(input, document.createTextNode(spell)); options.append(label);
    }
    for (const [field, ids] of Object.entries({feitico_antigo:['8'], divindade:['4','9'], afinidade:['5']})) {
      const box = form.querySelector(`[data-special-field="${field}"]`);
      const input = box.querySelector('input,select');
      box.hidden = !ids.includes(id); input.disabled = box.hidden; input.required = !box.hidden;
    }
    const info = document.querySelector('#class-rules'); info.replaceChildren();
    if (data) {
      for (const [key, title] of Object.entries({descricao:'Descrição', sabe_usar:'Sabe usar', defesas:'Defesas', item_inicial:'Item inicial', foco:'Focos de magia', habilidade_especial:'Habilidade especial'})) {
        const p = document.createElement('p'), strong = document.createElement('strong');
        strong.textContent = title + ': '; p.append(strong, document.createTextNode(data[key] || '')); info.append(p);
      }
      for (const detail of data.habilidade_detalhes || []) {
        const p = document.createElement('p'); p.textContent = detail; info.append(p);
      }
      if (['1','2','3'].includes(id)) {
        const p = document.createElement('p'); p.textContent = 'Escolha o efeito no momento do uso. Os efeitos compartilham o uso único da habilidade.'; info.append(p);
      }
    }
    firstRender = false;
    spellValidity();
    const image = document.querySelector(`.character-class-card input[value="${id}"]`)?.closest('label').querySelector('img');
    const preview = document.querySelector('[data-class-preview]');
    if (image) { preview.src = image.src; preview.alt = image.alt; } else { preview.removeAttribute('src'); }
  }
  function validate(panel) {
    spellValidity();
    const invalid = panel.querySelector(':invalid');
    if (invalid) { show(panel.dataset.characterPanel); invalid.reportValidity(); return false; }
    return true;
  }
  tabs.forEach(tab => tab.addEventListener('click', () => show(tab.dataset.characterTab)));
  form.querySelectorAll('[data-character-next]').forEach(button => button.addEventListener('click', () => {
    if (validate(button.closest('[data-character-panel]'))) show(button.dataset.characterNext);
  }));
  form.querySelectorAll('[data-character-prev]').forEach(button => button.addEventListener('click', () => show(button.dataset.characterPrev)));
  form.addEventListener('submit', event => {
    for (const panel of panels) if (!validate(panel)) { event.preventDefault(); break; }
  });
  select.addEventListener('change', render); render();
  show(panels.find(panel => panel.querySelector('.errorlist,.text-error,.alert-error'))?.dataset.characterPanel || 'identity');
  if (new URLSearchParams(location.search).has('created') && parent !== window) parent.postMessage({type:'personagem-criado'}, location.origin);
});
