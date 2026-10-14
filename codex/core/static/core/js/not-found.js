(() => {
  const backLink = document.querySelector('[data-not-found-back]');
  if (!backLink || !document.referrer) return;

  try {
    const previous = new URL(document.referrer);
    if (previous.origin !== window.location.origin || previous.href === window.location.href) return;

    // A real link also works when this page was opened in a new tab.
    backLink.href = previous.href;
  } catch {
    // The home link remains available when the referrer isn't a valid URL.
  }
})();
