(() => {
  document.querySelectorAll('[data-admin-dashboard] table, #planilha-participantes table').forEach(table => {
    const headings = [...table.querySelectorAll('thead th')].map(th => th.textContent.trim());
    table.querySelectorAll('tbody tr').forEach(row => {
      [...row.cells].forEach((cell, index) => {
        if (cell.colSpan === 1 && headings[index]) cell.dataset.label = headings[index];
      });
    });
    table.classList.add('mobile-records');
  });
  const fallback = document.body.dataset.imageFallback;
  const recoverImage = img => {
    if (!(img instanceof HTMLImageElement) || img.closest('dialog') || !img.getAttribute('src') || img.dataset.imageFailed) return;
    img.dataset.imageFailed = 'true';
    img.classList.add('image-unavailable');
    img.title = 'Imagem indisponível';
    if (img.alt) img.alt = `Imagem indisponível: ${img.alt}`;
    img.src = fallback;
  };
  document.addEventListener('error', event => recoverImage(event.target), true);
  document.querySelectorAll('img').forEach(img => {
    if (img.complete && !img.naturalWidth) recoverImage(img);
  });
})();
