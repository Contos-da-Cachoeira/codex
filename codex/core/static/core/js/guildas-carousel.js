(function () {
  document.querySelectorAll('[data-guildas-carousel]').forEach(function (carousel) {
    if (carousel.dataset.initialized) return;
    carousel.dataset.initialized = 'true';
    const track = carousel.querySelector('[data-carousel-track]');
    const previous = carousel.querySelector('[data-carousel-prev]');
    const next = carousel.querySelector('[data-carousel-next]');
    if (!track || !previous || !next) return;

    const originalCards = Array.from(track.querySelectorAll('.guilda-showcase-card'));
    const originalCount = originalCards.length;
    if (originalCount < 2) return;

    const cloneCards = (cards) => cards.map((card) => {
      const clone = card.cloneNode(true);
      clone.setAttribute('aria-hidden', 'true');
      clone.setAttribute('tabindex', '-1');
      return clone;
    });

    track.prepend(...cloneCards(originalCards));
    track.append(...cloneCards(originalCards));

    let currentIndex = originalCount;
    let resetTimer;

    const getStep = () => {
      const card = track.querySelector('.guilda-showcase-card');
      const styles = getComputedStyle(track);
      const gap = Number.parseFloat(styles.columnGap || styles.gap) || 0;
      return (card ? card.getBoundingClientRect().width : 0) + gap;
    };

    const goToCurrent = (behavior) => {
      track.scrollTo({
        left: currentIndex * getStep(),
        behavior: behavior || 'smooth',
      });
    };

    const resetToMiddle = () => {
      window.clearTimeout(resetTimer);
      if (currentIndex >= originalCount * 2) {
        currentIndex -= originalCount;
      } else if (currentIndex < originalCount) {
        currentIndex += originalCount;
      }
      goToCurrent('auto');
    };

    const move = (direction) => {
      currentIndex += direction;
      goToCurrent('smooth');
      resetTimer = window.setTimeout(resetToMiddle, 480);
    };

    previous.addEventListener('click', () => move(-1));
    next.addEventListener('click', () => move(1));
    window.addEventListener('resize', () => goToCurrent('instant'));
    window.requestAnimationFrame(() => goToCurrent('auto'));
    window.setInterval(() => move(1), 3000);
  });
})();
