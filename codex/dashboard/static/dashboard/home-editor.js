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
  let activePreview, componentTimer, componentController, componentVersion = 0;
  async function previewComponent() {
    if (!activePreview) return;
    const target = activePreview;
    const current = ++componentVersion;
    if (componentController) componentController.abort();
    componentController = new AbortController();
    target.status.textContent = 'Atualizando prévia do componente…';
    const body = new FormData(form);
    // Hidden components remain visible in the editor without changing the draft.
    body.set('components_json', JSON.stringify([{...target.component, is_visible: true}]));
    try {
      const response = await fetch(form.dataset.previewUrl, {method: 'POST', body, signal: componentController.signal});
      if (response.redirected) throw new Error('Sua sessão expirou. Entre novamente para continuar.');
      if (!response.ok) {
        const result = await readJson(response);
        throw new Error(result.error || 'Não foi possível atualizar a prévia.');
      }
      const html = await response.text();
      if (current !== componentVersion || activePreview !== target) return;
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const componentHome = doc.querySelector('.codex-home');
      if (!componentHome) throw new Error('Não foi possível carregar o componente.');
      doc.body.replaceChildren(componentHome);
      const style = doc.createElement('style');
      style.textContent = 'body { margin:0 !important; padding:16px !important; min-height:0 !important; }';
      doc.head.append(style);
      target.frame.srcdoc = '<!doctype html>' + doc.documentElement.outerHTML;
      target.status.textContent = target.component.is_visible ? 'Prévia do componente.' : 'Componente oculto na home; exibido aqui para edição.';
    } catch (error) {
      if (error.name !== 'AbortError' && current === componentVersion && activePreview === target) target.status.textContent = error.message;
    }
  }
  const labels = {text: 'Texto', community: 'Comunidade / guildas', banner: 'Banner dividido', callout: 'Chamada centralizada', links: 'Atalhos', event: 'Evento'};
  function fitPreview(previewFrame, previewStage, previewWidth) {
    const scale = Math.min(1, previewStage.clientWidth / previewWidth);
    const height = previewWidth === 390 ? 844 : 900;
    previewFrame.style.width = `${previewWidth}px`;
    previewFrame.style.height = `${height}px`;
    previewFrame.style.transform = `scale(${scale}) translateX(-50%)`;
    previewStage.style.height = `${height * scale}px`;
  }
  function fit() {
    fitPreview(frame, stage, width);
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
    clearTimeout(componentTimer);
    ++componentVersion;
    if (componentController) componentController.abort();
    if (activePreview) componentTimer = setTimeout(previewComponent, 350);
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
      const card = document.createElement('div');
      card.className = 'home-editor-card';
      const summary = document.createElement('h4');
      summary.className = 'font-bold';
      summary.textContent = `${index + 1}. ${labels[component.kind]}: ${component.title}`;
      card.append(summary);
      const dialog = document.createElement('dialog');
      dialog.className = 'home-component-dialog';
      dialog.setAttribute('aria-labelledby', `component-dialog-title-${index}`);
      const heading = document.createElement('h4');
      heading.id = `component-dialog-title-${index}`;
      heading.className = 'text-xl font-bold';
      heading.textContent = `Editar ${labels[component.kind]}`;
      const close = document.createElement('button');
      close.type = 'button'; close.className = 'btn btn-sm btn-ghost'; close.textContent = 'Fechar';
      close.addEventListener('click', () => dialog.close());
      const header = document.createElement('div');
      header.className = 'flex items-center justify-between gap-3';
      header.append(heading, close);
      dialog.append(header);
      const note = document.createElement('p');
      note.className = 'text-sm mt-3 text-base-content/70';
      note.textContent = 'As alterações ficam no rascunho. Use “Salvar e publicar home” para publicar.';
      dialog.append(note);
      const layout = document.createElement('div');
      layout.className = 'home-component-layout';
      const previewPanel = document.createElement('section');
      previewPanel.className = 'home-component-preview-panel';
      const previewHeading = document.createElement('h5');
      previewHeading.className = 'font-bold';
      previewHeading.textContent = 'Prévia';
      previewPanel.append(previewHeading);
      const settings = document.createElement('section');
      settings.className = 'home-component-settings';
      const settingsHeading = document.createElement('h5');
      settingsHeading.className = 'font-bold';
      settingsHeading.textContent = 'Configurações';
      settings.append(settingsHeading);
      layout.append(previewPanel, settings);
      dialog.append(layout);
      const componentPreview = document.createElement('iframe');
      componentPreview.className = 'home-component-preview';
      componentPreview.title = `Prévia de ${labels[component.kind]}`;
      componentPreview.setAttribute('sandbox', 'allow-scripts allow-same-origin');
      componentPreview.addEventListener('load', () => {
        const doc = componentPreview.contentDocument;
        if (doc) {
          doc.addEventListener('click', event => {if (event.target.closest('a')) event.preventDefault();});
          doc.addEventListener('submit', event => event.preventDefault());
        }
      });
      const componentStatus = document.createElement('p');
      componentStatus.className = 'text-sm mt-3 text-base-content/70';
      componentStatus.setAttribute('role', 'status');
      const deviceControls = document.createElement('div');
      deviceControls.className = 'flex flex-wrap gap-2 mt-3';
      deviceControls.setAttribute('role', 'group');
      deviceControls.setAttribute('aria-label', 'Tamanho da prévia do componente');
      const componentBox = document.createElement('div');
      componentBox.className = 'home-preview-box mt-3';
      const componentStage = document.createElement('div');
      componentStage.className = 'home-preview-stage';
      componentStage.append(componentPreview);
      componentBox.append(componentStage);
      let componentWidth = 1366;
      const fitComponent = () => fitPreview(componentPreview, componentStage, componentWidth);
      const componentObserver = new ResizeObserver(fitComponent);
      [[1366, 'Computador'], [390, 'Celular']].forEach(([deviceWidth, caption]) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `btn btn-sm ${deviceWidth === componentWidth ? 'btn-primary' : 'btn-outline'}`;
        button.textContent = caption;
        button.setAttribute('aria-pressed', String(deviceWidth === componentWidth));
        button.addEventListener('click', () => {
          componentWidth = deviceWidth;
          [...deviceControls.children].forEach(item => {
            const selected = item === button;
            item.setAttribute('aria-pressed', String(selected));
            item.classList.toggle('btn-primary', selected);
            item.classList.toggle('btn-outline', !selected);
          });
          fitComponent();
        });
        deviceControls.append(button);
      });
      previewPanel.append(deviceControls, componentStatus, componentBox);
      function openEditor() {
        dialog.showModal();
        componentObserver.observe(componentStage);
        fitComponent();
        activePreview = {component, frame: componentPreview, status: componentStatus};
        clearTimeout(componentTimer);
        previewComponent();
      }
      dialog.addEventListener('close', () => {
        componentObserver.disconnect();
        if (activePreview?.frame !== componentPreview) return;
        activePreview = null;
        ++componentVersion;
        clearTimeout(componentTimer);
        if (componentController) componentController.abort();
      });
      dialog.addEventListener('click', event => {
        if (event.target !== dialog) return;
        const bounds = dialog.getBoundingClientRect();
        if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
      });
      dialog.addEventListener('keydown', event => {
        if (event.key === 'Enter' && event.target.tagName === 'INPUT') event.preventDefault();
      });
      const controls = document.createElement('div');
      controls.className = 'flex flex-wrap gap-2 mt-3';
      const edit = document.createElement('button');
      edit.type = 'button'; edit.className = 'btn btn-primary btn-sm'; edit.textContent = 'Editar';
      edit.setAttribute('aria-haspopup', 'dialog');
      edit.setAttribute('aria-label', `Editar: ${component.title}`);
      edit.addEventListener('click', openEditor);
      controls.append(edit);
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
      if (component.kind === 'event') {
        const hint = document.createElement('p');
        hint.className = 'text-sm mt-3 text-base-content/70';
        hint.textContent = 'Mostra automaticamente o próximo LARP publicado, com capa, data, local e inscrição. Os dados são atualizados na área de LARPs.';
        settings.append(hint);
      }
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
        settings.append(picker);
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
        input.addEventListener('invalid', () => {if (!dialog.open) openEditor();});
        input.addEventListener('input', () => {
          component[key] = key === 'is_visible' ? input.checked : input.value;
          summary.textContent = `${index + 1}. ${labels[component.kind]}: ${component.title}`;
          edit.setAttribute('aria-label', `Editar: ${component.title}`);
          changed();
        });
        label.append(input); settings.append(label);
      });
      const done = document.createElement('button');
      done.type = 'button'; done.className = 'btn btn-primary mt-5'; done.textContent = 'Concluir edição';
      done.addEventListener('click', () => {
        const invalid = [...dialog.querySelectorAll('input, textarea')].find(input => !input.checkValidity());
        if (invalid) invalid.reportValidity();
        else dialog.close();
      });
      settings.append(done);
      card.append(dialog);
      list.append(card);
    });
    if (!components.length) list.textContent = 'Nenhum componente. Adicione um bloco para começar.';
  }
  root.querySelector('[data-add-component]').addEventListener('click', () => {
    const kind = root.querySelector('[data-component-kind]').value;
    components.push({kind, title: labels[kind], content:'', eyebrow:'', image_url:'', is_visible:true});
    draw(); changed();
    list.lastElementChild.querySelector('button').click();
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
