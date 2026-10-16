const root = document.querySelector('[data-pdf-reader]');
if (root) {
  const status = root.querySelector('[data-pdf-status]');
  const page = root.querySelector('[data-pdf-page]');
  const previous = root.querySelector('[data-pdf-previous]');
  const next = root.querySelector('[data-pdf-next]');
  const zoom = root.querySelector('[data-pdf-zoom]');
  const fullscreen = root.querySelector('[data-pdf-fullscreen]');
  const search = root.querySelector('[data-pdf-search]');
  const searchCount = root.querySelector('[data-pdf-find-count]');
  const container = root.querySelector('[data-pdf-container]');
  const base = new URL('../vendor/pdfjs/6.4.299/', import.meta.url);
  let loadingTask;
  fullscreen.hidden = !document.fullscreenEnabled;
  fullscreen.addEventListener('click', async () => {
    try {
      if (document.fullscreenElement === root) await document.exitFullscreen();
      else await root.requestFullscreen();
    } catch { status.textContent = 'Não foi possível abrir em tela cheia. Você pode continuar lendo aqui.'; }
  });
  document.addEventListener('fullscreenchange', () => fullscreen.setAttribute('aria-label', document.fullscreenElement === root ? 'Sair da tela cheia' : 'Tela cheia'));
  try {
    const pdfjs = await import(new URL('build/pdf.min.js', base));
    const {PDFViewer, EventBus, PDFLinkService, PDFFindController} = await import(new URL('web/pdf_viewer.js', base));
    pdfjs.GlobalWorkerOptions.workerSrc = new URL('build/pdf.worker.min.js', base).href;
    const eventBus = new EventBus();
    const linkService = new PDFLinkService({eventBus, externalLinkTarget: 2, externalLinkRel: 'noopener noreferrer'});
    const findController = new PDFFindController({eventBus, linkService});
    const viewer = new PDFViewer({container, viewer: root.querySelector('[data-pdf-viewer]'), eventBus, linkService,
      findController, enableScripting: false, imageResourcesPath: new URL('web/images/', base).href});
    linkService.setViewer(viewer);
    let total = 0;
    const updatePage = () => {
      page.value = viewer.currentPageNumber;
      previous.disabled = viewer.currentPageNumber <= 1;
      next.disabled = viewer.currentPageNumber >= total;
    };
    eventBus.on('pagechanging', updatePage);
    eventBus.on('pagesinit', () => { viewer.currentScaleValue = 'page-width'; updatePage(); });
    eventBus.on('pagerendered', event => {
      if (event.error) { status.textContent = 'Não foi possível exibir esta página. Tente outra página ou baixe o PDF.'; status.classList.add('is-error'); }
      else { status.textContent = ''; root.dataset.pdfReady = 'true'; }
    });
    loadingTask = pdfjs.getDocument({url: root.dataset.pdfUrl, cMapUrl: new URL('cmaps/', base).href, cMapPacked: true,
      standardFontDataUrl: new URL('standard_fonts/', base).href, wasmUrl: new URL('wasm/', base).href,
      disableStream: true, disableAutoFetch: true, rangeChunkSize: 128 * 1024, isEvalSupported: false});
    const pdf = await loadingTask.promise;
    total = pdf.numPages;
    root.querySelector('[data-pdf-total]').textContent = total;
    page.max = total;
    viewer.setDocument(pdf);
    linkService.setDocument(pdf, null);
    root.querySelectorAll('[data-pdf-control]').forEach(control => control.disabled = false);
    updatePage();
    previous.addEventListener('click', () => viewer.currentPageNumber = Math.max(1, viewer.currentPageNumber - 1));
    next.addEventListener('click', () => viewer.currentPageNumber = Math.min(total, viewer.currentPageNumber + 1));
    const goToPage = () => {
      const value = Number(page.value);
      if (Number.isInteger(value) && value >= 1 && value <= total) viewer.currentPageNumber = value;
      else page.value = viewer.currentPageNumber;
    };
    page.addEventListener('change', goToPage);
    page.addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); goToPage(); } });
    zoom.addEventListener('change', () => viewer.currentScaleValue = zoom.value);
    let searchTimer;
    function find(again = false) {
      const query = search.value.trim();
      searchCount.textContent = query ? 'Buscando…' : '';
      eventBus.dispatch('find', {source: root, type: again ? 'again' : '', query,
        caseSensitive: false, entireWord: false, highlightAll: true, findPrevious: false, matchDiacritics: false});
    }
    search.addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => find(), 250); });
    root.querySelector('[data-pdf-find]').addEventListener('submit', event => { event.preventDefault(); clearTimeout(searchTimer); find(true); });
    eventBus.on('updatefindmatchescount', ({matchesCount}) => {
      searchCount.textContent = search.value.trim() ? `${matchesCount.current || 0} de ${matchesCount.total} resultados` : '';
    });
    eventBus.on('updatefindcontrolstate', ({state}) => { if (state === 1) searchCount.textContent = 'Nenhum resultado'; });
    let resizeFrame, dimensions = '';
    new ResizeObserver(() => {
      const current = `${container.clientWidth}:${container.clientHeight}`;
      if (current === dimensions) return;
      dimensions = current;
      cancelAnimationFrame(resizeFrame);
      resizeFrame = requestAnimationFrame(() => {
        if (['page-width', 'page-fit'].includes(zoom.value)) viewer.currentScaleValue = zoom.value;
        viewer.update();
      });
    }).observe(root.querySelector('.wd-reader-frame'));
    window.addEventListener('pagehide', () => loadingTask.destroy(), {once: true});
  } catch (error) {
    console.error('Falha ao iniciar o leitor de PDF:', error);
    loadingTask?.destroy();
    status.textContent = 'Não foi possível carregar o leitor. Tente atualizar a página ou use Baixar PDF / Abrir PDF em outra aba.';
    status.classList.add('is-error');
    status.setAttribute('role', 'alert');
    root.dataset.pdfError = 'true';
    root.querySelectorAll('[data-pdf-control]').forEach(control => control.disabled = true);
  }
}
