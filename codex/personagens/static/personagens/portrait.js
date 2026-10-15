document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('[data-portrait-options]')?.closest('form');
  if (!form) return;
  function update() {
    const name = form.querySelector('[name=nome]').value.trim() || 'Seu personagem';
    form.querySelector('[data-name-preview]').textContent = name.slice(0, 1).toUpperCase();
    form.querySelectorAll('[data-character-name]').forEach(box => box.textContent = name);
    const photo = form.querySelector('[name=image_asset]');
    const mode = form.querySelector('[name=portrait_mode]:checked');
    form.querySelector('[name=portrait_mode][value=photo]').setCustomValidity(mode?.value === 'photo' && !photo.value ? 'Escolha uma foto ou outra opção de identificação.' : '');
  }
  form.addEventListener('input', update);
  form.addEventListener('change', update);
  form.addEventListener('character-photo-change', () => {
    const hasPhoto = Boolean(form.querySelector('[name=image_asset]').value);
    form.querySelector(`[name=portrait_mode][value="${hasPhoto ? 'photo' : 'name'}"]`).checked = true;
    update();
  });
  update();
});
