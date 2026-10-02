(() => {
  const input = document.querySelector('[data-wiki-search]');
  if (!input) return;
  const cards = [...document.querySelectorAll('[data-wiki-item]')];
  const count = document.querySelector('[data-wiki-count]');
  const empty = document.querySelector('[data-wiki-empty]');
  const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR');
  const filter = () => {
    const query = normalize(input.value.trim());
    let visible = 0;
    cards.forEach(card => {
      card.hidden = !normalize(card.dataset.wikiItem).includes(query);
      if (!card.hidden) visible += 1;
    });
    count.textContent = `${visible} ${visible === 1 ? 'item encontrado' : 'itens encontrados'}`;
    empty.hidden = visible !== 0;
  };
  input.addEventListener('input', filter);
  filter();
})();
