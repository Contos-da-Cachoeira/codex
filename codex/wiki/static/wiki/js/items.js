(() => {
  const input = document.querySelector('[data-wiki-search]');
  if (!input) return;
  const cards = [...document.querySelectorAll('[data-wiki-item]')];
  const count = document.querySelector('[data-wiki-count]');
  const empty = document.querySelector('[data-wiki-empty]');
  const filters = [...document.querySelectorAll('[data-wiki-filter]')];
  const more = document.querySelector('[data-wiki-more]');
  const results = document.getElementById(input.getAttribute('aria-controls'));
  const pageSize = Number(results?.dataset.wikiPageSize) || cards.length;
  const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR');
  const searchable = cards.map(card => ({card, text: normalize(card.dataset.wikiItem)}));
  let category = 'all';
  let limit = pageSize;

  const filter = (resetLimit = true) => {
    if (resetLimit) limit = pageSize;
    const terms = normalize(input.value.trim()).split(/\s+/).filter(Boolean);
    const matches = searchable.filter(({card, text}) =>
      (category === 'all' || card.dataset.wikiCategory === category) && terms.every(term => text.includes(term))
    );
    cards.forEach(card => { card.hidden = true; });
    matches.slice(0, limit).forEach(({card}) => { card.hidden = false; });
    const shown = Math.min(limit, matches.length);
    if (count) {
      count.textContent = more && matches.length > shown
        ? `Exibindo ${shown} de ${matches.length} conteúdos`
        : `${matches.length} ${matches.length === 1 ? 'resultado encontrado' : 'resultados encontrados'}`;
    }
    if (empty) empty.hidden = matches.length !== 0 || cards.length === 0;
    if (more) more.hidden = shown >= matches.length;
    filters.forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.wikiFilter === category));
    });
  };

  document.querySelector('[data-wiki-controls]')?.removeAttribute('hidden');
  input.addEventListener('input', () => filter());
  filters.forEach(button => button.addEventListener('click', () => {
    category = button.dataset.wikiFilter;
    filter();
  }));
  more?.addEventListener('click', () => {
    const previousLimit = limit;
    limit += pageSize;
    filter(false);
    // Keep keyboard navigation at the newly revealed contents.
    cards.filter(card => !card.hidden)[previousLimit]?.focus({preventScroll: true});
  });
  document.querySelector('[data-wiki-reset]')?.addEventListener('click', () => {
    input.value = '';
    category = 'all';
    filter();
    input.focus({preventScroll: true});
  });
  filter();
})();
