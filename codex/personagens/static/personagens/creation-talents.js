document.addEventListener('DOMContentLoaded', () => {
  const box = document.querySelector('[data-creation-talents]');
  if (!box) return;
  const form = box.closest('form');
  const hidden = form.querySelector('[name=talent_requests]');
  const catalog = JSON.parse(document.getElementById('creation-talents-data').textContent);
  const byKey = Object.fromEntries(catalog.map(item => [item.key, item]));
  const spells = JSON.parse(document.getElementById('creation-talent-spells').textContent);
  const ancient = JSON.parse(document.getElementById('creation-talent-ancient').textContent);
  const classSpells = JSON.parse(document.getElementById('magias-por-classe-data').textContent);
  const choice = box.querySelector('[data-talent-choice]');
  const list = box.querySelector('[data-selected-creation-talents]');
  const feedback = box.querySelector('[data-talent-feedback]');
  const balance = Number(box.dataset.playerXp);
  let selected;
  try { selected = JSON.parse(hidden.value || '[]'); } catch { selected = []; }
  if (!Array.isArray(selected)) selected = [];
  const total = () => selected.reduce((sum, item) => sum + (byKey[item.talento]?.custo_xp || 0), 0);
  const value = name => box.querySelector(`[data-talent-value="${name}"]`);
  function edit() {
    const item = byKey[choice.value];
    box.querySelector('[data-talent-editor]').hidden = !item;
    feedback.textContent = '';
    if (!item) return;
    box.querySelector('[data-talent-description]').textContent = item.descricao;
    box.querySelector('[data-talent-requirement]').textContent = [item.requisito, item.restricao, item.stackavel ? 'Permite compras repetidas.' : ''].filter(Boolean).join(' · ');
    const conditional = {magia:['MAGIA_EXTRA_CLASSE','MAGIA_OUTRA_CLASSE','CONJURAR','FEITICO_ANTIGO'], foco:['CONJURAR'], detalhes:['FORMA_SELVAGEM']};
    for (const [field, keys] of Object.entries(conditional)) box.querySelector(`[data-talent-choice-field="${field}"]`).hidden = !keys.includes(choice.value);
    const own = classSpells[form.querySelector('[name=classe]').value] || [];
    const known = [...form.querySelectorAll('.magia-checkbox:checked')].map(input => input.value);
    const queued = selected.map(item => item.magia);
    let available = spells;
    if (choice.value === 'FEITICO_ANTIGO') available = ancient.filter(spell => spell !== form.querySelector('[name=feitico_antigo]').value);
    if (choice.value === 'MAGIA_EXTRA_CLASSE') available = own;
    if (choice.value === 'MAGIA_OUTRA_CLASSE') available = spells.filter(spell => !own.includes(spell));
    value('magia').replaceChildren();
    const placeholder = document.createElement('option'); placeholder.value = ''; placeholder.textContent = 'Selecione a magia'; value('magia').append(placeholder);
    available.filter(spell => !known.includes(spell) && !queued.includes(spell)).forEach(spell => {
      const option = document.createElement('option'); option.value = spell; option.textContent = spell; value('magia').append(option);
    });
  }
  function render() {
    hidden.value = JSON.stringify(selected);
    box.querySelector('[data-talent-summary]').textContent = `${selected.length} de 5 compras · ${total()} XP`;
    list.replaceChildren();
    if (!selected.length) { const p = document.createElement('p'); p.textContent = 'Nenhum talento selecionado. Você pode adquirir talentos depois na ficha.'; list.append(p); }
    selected.forEach((request, index) => {
      const item = byKey[request.talento];
      const row = document.createElement('div'); row.className = 'character-question';
      const title = document.createElement('strong'); title.textContent = `${item?.nome || request.talento} — ${item?.custo_xp || 0} XP`;
      const details = document.createElement('p'); details.textContent = [request.magia, request.foco, request.detalhes, request.justificativa].filter(Boolean).join(' · ');
      const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'btn btn-ghost btn-sm'; remove.textContent = 'Remover';
      remove.setAttribute('aria-label', `Remover ${item?.nome || 'talento'} ${index + 1}`);
      remove.addEventListener('click', () => { selected.splice(index,1); render(); edit(); });
      row.append(title, details, remove); list.append(row);
    });
  }
  choice.addEventListener('change', edit);
  form.querySelector('[name=classe]').addEventListener('change', edit);
  form.addEventListener('change', event => { if (event.target.name === 'magias_pretendidas' || event.target.name === 'feitico_antigo') edit(); });
  box.querySelector('[data-add-creation-talent]').addEventListener('click', () => {
    const item = byKey[choice.value];
    if (!item) return;
    const fail = message => { feedback.textContent = message; };
    if (selected.length >= 5) return fail('Você já selecionou cinco compras. Remova uma para trocar.');
    if (total() + item.custo_xp > balance) return fail('Saldo de XP insuficiente para adicionar este talento. Você pode continuar sem talentos.');
    const repeatable = item.stackavel;
    if (!repeatable && selected.some(request => request.talento === item.key)) return fail('Este talento não permite compras repetidas.');
    const request = {talento:item.key, justificativa:value('justificativa').value.trim()};
    if (!request.justificativa) { value('justificativa').focus(); return fail('Conte como seu personagem aprendeu este talento.'); }
    for (const field of ['magia','foco','detalhes']) {
      if (box.querySelector(`[data-talent-choice-field="${field}"]`).hidden) continue;
      request[field] = value(field).value.trim();
      if (!request[field]) { value(field).focus(); return fail('Complete a escolha necessária para este talento.'); }
    }
    selected.push(request); render(); edit();
    feedback.textContent = 'Talento adicionado à solicitação. Será enviado junto com a ficha.';
  });
  render(); edit();
});
