document.addEventListener('DOMContentLoaded', () => {
  const root = document.querySelector('[data-home-editor]');
  if (!root) return;
  const form = root.querySelector('form');
  const list = root.querySelector('[data-component-list]');
  const status = root.querySelector('[data-editor-status]');
  const frame = root.querySelector('iframe');
  const stage = frame.parentElement;
  let components = JSON.parse(document.getElementById('home-components-data').textContent);
  let width = 1366, timer, controller, version = 0, dirty = false;
  const labels = {text: 'Texto', community: 'Comunidade / guildas', banner: 'Banner dividido', callout: 'Chamada centralizada', links: 'Atalhos'};
  function fit() {
    const scale = Math.min(1, stage.clientWidth / width);
    frame.style.width = `${width}px`;
    frame.style.height = `${width === 390 ? 844 : 900}px`;
    frame.style.transform = `scale(${scale}) translateX(-50%)`;
    stage.style.height = `${(width === 390 ? 844 : 900) * scale}px`;
  }
  new ResizeObserver(fit).observe(stage);
  root.querySelectorAll('[data-preview-width]').forEach(button => button.addEventListener('click', () => {
    width = Number(button.dataset.previewWidth);
    root.querySelectorAll('[data-preview-width]').forEach(item => {
      const selected = item === button;
      item.setAttribute('aria-pressed', String(selected));
      item.classList.toggle('btn-primary', selected);
      item.classList.toggle('btn-outline', !selected);
    });
    fit();
  }));
  function sync() { form.elements.components_json.value = JSON.stringify(components); }
  async function readJson(response) {
    if (response.redirected || response.status === 401) throw new Error('Sua sessão expirou. Entre novamente antes de salvar.');
    if (!(response.headers.get('content-type') || '').includes('application/json')) {
      if (response.status === 403) throw new Error('Atualize a página para renovar a sessão de segurança e tente novamente.');
      throw new Error(`O servidor retornou uma resposta inesperada (HTTP ${response.status}). As alterações não foram confirmadas.`);
    }
    return response.json();
  }
  async function preview() {
    sync();
    const current = ++version;
    if (controller) controller.abort();
    controller = new AbortController();
    status.textContent = 'Atualizando prévia…';
    try {
      const response = await fetch(form.dataset.previewUrl, {method:'POST', body:new FormData(form), signal:controller.signal});
      if (!response.ok) {
        const data = await readJson(response);
        throw new Error(data.error || 'Não foi possível atualizar a prévia.');
      }
      if (response.redirected) throw new Error('Sua sessão expirou. Entre novamente para continuar.');
      const html = await response.text();
      if (current !== version) return;
      frame.srcdoc = html;
      status.textContent = dirty ? 'Prévia atualizada. Alterações ainda não publicadas.' : 'Prévia da configuração publicada.';
    } catch (error) {
      if (error.name !== 'AbortError' && current === version) status.textContent = error.message;
    }
  }
  function changed() {
    dirty = true;
    sync();
    clearTimeout(timer);
    ++version;
    if (controller) controller.abort();
    status.textContent = 'Alterações não publicadas.';
    timer = setTimeout(preview, 350);
  }
  function draw() {
    list.replaceChildren();
    components.forEach((component, index) => {
      const card = document.createElement('details');
      card.className = 'home-editor-card';
      card.open = true;
      const summary = document.createElement('summary');
      summary.textContent = `${index + 1}. ${labels[component.kind]}`;
      card.append(summary);
      const controls = document.createElement('div');
      controls.className = 'flex flex-wrap gap-2 mt-3';
      [['↑', -1], ['↓', 1], ['Remover', 0]].forEach(([text, direction]) => {
        const button = document.createElement('button');
        button.type = 'button'; button.className = 'btn btn-outline btn-sm'; button.textContent = text;
        button.setAttribute('aria-label', `${direction < 0 ? 'Mover acima' : direction > 0 ? 'Mover abaixo' : 'Remover'}: ${component.title}`);
        button.disabled = direction < 0 && index === 0 || direction > 0 && index === components.length - 1;
        button.addEventListener('click', () => {
          if (!direction) components.splice(index, 1);
          else [components[index], components[index + direction]] = [components[index + direction], components[index]];
          draw(); changed();
        });
        controls.append(button);
      });
      card.append(controls);
      const fields = [['is_visible','Mostrar na home'], ['eyebrow','Texto acima do título'], ['title','Título'], ['content','Descrição / conteúdo']];
      if (['banner','callout'].includes(component.kind)) fields.push(
        ['button_label','Texto do botão principal'],['button_url','Destino principal (ex.: /personagens/)'],
        ['secondary_label','Texto do botão secundário'],['secondary_url','Destino secundário (ex.: /wiki/)']
      );
      if (component.kind === 'banner') {
        const picker = document.createElement('button');
        picker.type='button'; picker.className='btn btn-outline mt-3'; picker.textContent='Escolher imagem / URL e enquadrar';
        picker.addEventListener('click',()=>window.CodexImagePicker.open({ratio:16/9,initial:component.image_asset_info || {source:component.image_url},onSelect:asset=>{
          component.image_asset_id=asset.id; component.image_asset_info=asset; component.image_url=''; changed();
        }}));
        card.append(picker);
      }
      fields.forEach(([key, caption]) => {
        const label = document.createElement('label'); label.textContent = caption;
        const input = document.createElement(key === 'content' ? 'textarea' : 'input');
        if (key === 'is_visible') {input.type='checkbox'; input.checked=component[key]; input.className='checkbox';}
        else {
          input.value = component[key] || '';
          input.className = key === 'content' ? 'textarea textarea-bordered' : 'input input-bordered';
          if (key !== 'content') input.type = key === 'image_url' ? 'url' : 'text';
          if (key === 'title') {input.required=true; input.maxLength=140;}
          if (key === 'eyebrow') input.maxLength=80;
          if (key.endsWith('_label')) input.maxLength=60;
          if (key.endsWith('_url')) input.maxLength=500;
          if (key === 'image_url') input.maxLength=200;
          if (key === 'content') {input.rows=4; input.maxLength=20000;}
        }
        input.addEventListener('input', () => {component[key] = key === 'is_visible' ? input.checked : input.value; changed();});
        label.append(input); card.append(label);
      });
      list.append(card);
    });
    if (!components.length) list.textContent = 'Nenhum componente. Adicione um bloco para começar.';
  }
  root.querySelector('[data-add-component]').addEventListener('click', () => {
    const kind = root.querySelector('[data-component-kind]').value;
    components.push({kind, title: labels[kind], content:'', eyebrow:'', image_url:'', is_visible:true});
    draw(); changed();
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    sync();
    const payload = form.elements.components_json.value;
    const button = form.querySelector('[type=submit]');
    button.disabled = true;
    status.textContent = 'Publicando…';
    try {
      const response = await fetch(form.dataset.saveUrl, {method:'POST', body:new FormData(form), credentials:'same-origin', headers:{'X-Requested-With':'XMLHttpRequest','Accept':'application/json'}});
      const result = await readJson(response);
      if (!response.ok || !result.saved) throw new Error(result.error || 'Não foi possível publicar.');
      dirty = JSON.stringify(components) !== payload;
      status.textContent = dirty ? 'Publicado. Há novas alterações ainda não salvas.' : 'Home publicada com sucesso.';
    } catch (error) {status.textContent = error.message;}
    finally {button.disabled = false;}
  });
  window.addEventListener('beforeunload', event => {if (dirty) {event.preventDefault(); event.returnValue='';}});
  frame.addEventListener('load', () => {
    // Keep navigation in the preview from replacing the draft with another page.
    const doc = frame.contentDocument;
    if (doc) doc.addEventListener('click', event => {if (event.target.closest('a')) event.preventDefault();});
    fit();
  });
  draw(); preview();
});
