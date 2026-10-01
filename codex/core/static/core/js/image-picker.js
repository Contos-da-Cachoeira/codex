window.CodexImagePicker = {
  open({ratio = 1, fixedRatio = false, initial = {}, onSelect}) {
    const dialog = document.createElement('dialog');
    dialog.className = 'modal';
    dialog.innerHTML = `<div class="modal-box" style="max-width:46rem"><h2 class="text-xl font-bold">Escolher e enquadrar imagem</h2>
      <p class="text-sm my-3">Escolha um arquivo ou cole uma URL. A área abaixo mostra exatamente o recorte; o restante ficará fora da imagem.</p>
      <label style="display:block">Galeria / computador<input type="file" accept="image/*" class="file-input file-input-bordered w-full" data-file></label>
      <label style="display:block;margin-top:1rem">URL direta da imagem<input type="url" placeholder="https://…" class="input input-bordered w-full" data-url></label>
      <label style="display:block;margin-top:1rem">Proporção<select data-ratio class="select select-bordered"><option value="1">Quadrada (1:1)</option><option value="1.7777777778">Horizontal (16:9)</option><option value="3">Banner (3:1)</option><option value="0.75">Vertical (3:4)</option></select></label>
      <div data-crop tabindex="0" role="group" aria-label="Enquadramento: arraste para mover, use a roda ou pinça para ampliar. No teclado, use as setas e as teclas mais e menos." style="position:relative;overflow:hidden;background:#171717;max-height:320px;margin:1rem auto;width:100%;touch-action:none;user-select:none;cursor:grab;outline-offset:4px"><img draggable="false" alt="Prévia do enquadramento" style="width:100%;height:100%;object-fit:cover;display:block;pointer-events:none"><div aria-hidden="true" style="position:absolute;inset:0;pointer-events:none;background:linear-gradient(to right,transparent 33.1%,#ffffff55 33.1%,#ffffff55 33.5%,transparent 33.5%,transparent 66.4%,#ffffff55 66.4%,#ffffff55 66.8%,transparent 66.8%),linear-gradient(to bottom,transparent 33.1%,#ffffff55 33.1%,#ffffff55 33.5%,transparent 33.5%,transparent 66.4%,#ffffff55 66.4%,#ffffff55 66.8%,transparent 66.8%)"></div></div>
      <p class="text-sm">Arraste a imagem para posicionar. Use a roda do mouse ou dois dedos para ampliar.</p>
      <div class="flex gap-2 mt-3"><button type="button" class="btn btn-outline btn-sm" data-zoom-out aria-label="Diminuir zoom">−</button><button type="button" class="btn btn-outline btn-sm" data-zoom-in aria-label="Aumentar zoom">+</button><button type="button" class="btn btn-ghost btn-sm" data-reset>Centralizar e ajustar</button></div>
      <input type="hidden" value="1" data-zoom><input type="hidden" value="50" data-x><input type="hidden" value="50" data-y>
      <p data-status role="status" class="text-sm mt-3"></p><div class="modal-action"><button type="button" class="btn btn-outline" data-cancel>Cancelar</button><button type="button" class="btn btn-primary" data-apply disabled>Usar imagem</button></div></div>`;
    document.body.append(dialog);
    const query = selector => dialog.querySelector(selector);
    const img = query('img'), crop = query('[data-crop]'), file = query('[data-file]'), url = query('[data-url]');
    const ratioInput = query('[data-ratio]'), apply = query('[data-apply]'), status = query('[data-status]');
    ratioInput.value = ratio === 1 ? '1' : '1.7777777778';
    ratioInput.disabled = fixedRatio;
    if (fixedRatio) crop.style.borderRadius='50%';
    let objectUrl, ready = false, urlTimer;
    function update() {
      const r = Number(ratioInput.value);
      crop.style.width = `${Math.min(600, 300 * r)}px`;
      crop.style.maxWidth = '100%'; crop.style.aspectRatio = String(r);
      const x=query('[data-x]').value, y=query('[data-y]').value, zoom=query('[data-zoom]').value;
      img.style.objectPosition = `${x}% ${y}%`; img.style.transformOrigin = `${x}% ${y}%`; img.style.transform = `scale(${zoom})`;
    }
    img.onload = () => {ready=true; apply.disabled=false; status.textContent='Ajuste o enquadramento e clique em Usar imagem.';};
    img.onerror = () => {ready=false; apply.disabled=true; status.textContent='Não foi possível abrir a imagem. Confira o arquivo ou a URL.';};
    file.addEventListener('change', () => {
      ready=false; apply.disabled=true;
      if (!file.files[0]) return;
      if (file.files[0].size > 10 * 1024 * 1024) {status.textContent='Escolha uma imagem de até 10 MB.'; return;}
      clearTimeout(urlTimer); url.value='';
      if(objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl=URL.createObjectURL(file.files[0]); img.src=objectUrl;
    });
    url.addEventListener('input', () => {
      ready=false; apply.disabled=true; file.value=''; clearTimeout(urlTimer);
      urlTimer=setTimeout(() => {
        try {const parsed=new URL(url.value); if(!['http:','https:'].includes(parsed.protocol)) throw new Error(); img.src=parsed.href;}
        catch {status.textContent='Informe uma URL HTTP ou HTTPS válida.';}
      }, 400);
    });
    const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
    function geometry() {
      const rect = crop.getBoundingClientRect();
      const cover = Math.max(rect.width / img.naturalWidth, rect.height / img.naturalHeight);
      const zoom = Number(query('[data-zoom]').value);
      return {rect, zoom, width: img.naturalWidth * cover, height: img.naturalHeight * cover};
    }
    function pan(dx, dy) {
      if (!ready) return;
      const g = geometry();
      [['x', dx, g.width * g.zoom - g.rect.width], ['y', dy, g.height * g.zoom - g.rect.height]].forEach(([key, delta, overflow]) => {
        if (overflow > .01) query(`[data-${key}]`).value = clamp(Number(query(`[data-${key}]`).value) - delta / overflow * 100, 0, 100);
      });
      update();
    }
    function zoomBy(factor, clientX, clientY) {
      if (!ready) return;
      const g = geometry(), next = clamp(g.zoom * factor, 1, 3);
      const ax = clientX === undefined ? g.rect.width / 2 : clientX - g.rect.left;
      const ay = clientY === undefined ? g.rect.height / 2 : clientY - g.rect.top;
      [['x', ax, g.width, g.rect.width], ['y', ay, g.height, g.rect.height]].forEach(([key, anchor, size, viewport]) => {
        const overflow = size * next - viewport;
        const oldOffset = (size * g.zoom - viewport) * Number(query(`[data-${key}]`).value) / 100;
        query(`[data-${key}]`).value = overflow > .01 ? clamp(((anchor + oldOffset) * next / g.zoom - anchor) / overflow * 100, 0, 100) : 50;
      });
      query('[data-zoom]').value = next;
      update();
    }
    const pointers = new Map();
    const gesture = () => {
      const points = [...pointers.values()];
      if (points.length < 2) return null;
      return {x:(points[0].x+points[1].x)/2, y:(points[0].y+points[1].y)/2,
        distance:Math.hypot(points[0].x-points[1].x,points[0].y-points[1].y)};
    };
    crop.addEventListener('pointerdown', event => {
      if (!ready || (event.pointerType === 'mouse' && event.button !== 0)) return;
      pointers.set(event.pointerId, {x:event.clientX,y:event.clientY});
      crop.setPointerCapture(event.pointerId); crop.style.cursor='grabbing'; crop.focus({preventScroll:true});
    });
    crop.addEventListener('pointermove', event => {
      const previous=pointers.get(event.pointerId); if(!previous)return;
      const before=gesture(); pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
      const after=gesture();
      if(before && after) {
        pan(after.x-before.x,after.y-before.y);
        if(before.distance>0)zoomBy(after.distance/before.distance,after.x,after.y);
      } else pan(event.clientX-previous.x,event.clientY-previous.y);
    });
    ['pointerup','pointercancel','lostpointercapture'].forEach(type=>crop.addEventListener(type,event=>{
      pointers.delete(event.pointerId);if(!pointers.size)crop.style.cursor='grab';
    }));
    crop.addEventListener('wheel',event=>{
      if(!ready)return;
      event.preventDefault(); zoomBy(Math.exp(-event.deltaY*(event.deltaMode === 1 ? .035 : .002)),event.clientX,event.clientY);
    },{passive:false});
    crop.addEventListener('keydown',event=>{
      const moves={ArrowLeft:[-10,0],ArrowRight:[10,0],ArrowUp:[0,-10],ArrowDown:[0,10]};
      if(moves[event.key]){event.preventDefault();pan(...moves[event.key]);}
      if(['+','=','-'].includes(event.key)){event.preventDefault();zoomBy(event.key==='-'?1/1.15:1.15);}
    });
    query('[data-zoom-in]').onclick=()=>zoomBy(1.15);
    query('[data-zoom-out]').onclick=()=>zoomBy(1/1.15);
    query('[data-reset]').onclick=()=>{
      query('[data-x]').value=50;query('[data-y]').value=50;query('[data-zoom]').value=1;update();
    };
    ratioInput.addEventListener('input',update);
    query('[data-cancel]').onclick=()=>dialog.close();
    dialog.addEventListener('close',()=>{clearTimeout(urlTimer);if(objectUrl)URL.revokeObjectURL(objectUrl);dialog.remove();});
    apply.onclick=async()=>{
      if(!ready)return;
      apply.disabled=true; status.textContent='Salvando imagem…';
      const data=new FormData();
      if(file.files[0])data.append('file',file.files[0]);else data.append('url',url.value);
      ['x','y','zoom'].forEach(key=>data.append(key,query(`[data-${key}]`).value));
      data.append('ratio',ratioInput.value);
      data.append('csrfmiddlewaretoken',document.querySelector('[name=csrfmiddlewaretoken]').value);
      try {
        const response=await fetch(document.body.dataset.imageUploadUrl,{
          method:'POST',body:data,credentials:'same-origin',
          headers:{'Accept':'application/json','X-Requested-With':'XMLHttpRequest'}
        });
        if(response.redirected || response.status===401)throw new Error('Sua sessão expirou. Entre novamente e tente salvar a imagem.');
        if(response.status===403)throw new Error('O envio foi bloqueado pela verificação de segurança. Atualize a página e tente novamente.');
        if(response.status===404)throw new Error('O servidor não carregou a rota de imagens. Recarregue o servidor e atualize a página.');
        if(response.status===413)throw new Error('A imagem excede o limite de envio. Escolha um arquivo de até 10 MB.');
        if(!(response.headers.get('content-type') || '').includes('application/json')) {
          throw new Error(`O servidor não conseguiu salvar a imagem (HTTP ${response.status}). Tente novamente; se persistir, informe este código.`);
        }
        const result=await response.json(); if(!response.ok)throw new Error(result.error || 'Falha ao salvar imagem.');
        onSelect(result);dialog.close();
      } catch(error){status.textContent=error.message;apply.disabled=false;}
    };
    if (initial.source) {
      url.value = new URL(initial.source, location.href).href;
      ['x','y','zoom'].forEach(key=>{if(initial[key] !== undefined)query(`[data-${key}]`).value=initial[key];});
      if (!fixedRatio && initial.ratio) ratioInput.value = Math.abs(initial.ratio-16/9)<.01 ? '1.7777777778' : String(initial.ratio);
      img.src=url.value;
    }
    update();dialog.showModal();
  }
};
document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('[data-profile-image-picker]').forEach(button=>button.addEventListener('click',()=>{
    const initial=button.dataset.selectedImage ? JSON.parse(button.dataset.selectedImage) : {
      source:button.dataset.imageSource,
      x:Number(button.dataset.imageX || 50), y:Number(button.dataset.imageY || 50), zoom:Number(button.dataset.imageZoom || 1)
    };
    window.CodexImagePicker.open({fixedRatio:true,initial,onSelect:asset=>{
      button.dataset.selectedImage=JSON.stringify(asset);
      const scope=button.closest('form') || document;
      scope.querySelector('[name=image_asset]').value=asset.id;
      const box=scope.querySelector('[data-profile-image-preview]');
      box.replaceChildren();const img=document.createElement('img');img.src=asset.source;img.alt='Foto de perfil';
      img.style.cssText=`width:100%;height:100%;object-fit:cover;object-position:${asset.x}% ${asset.y}%;transform:scale(${asset.zoom});transform-origin:${asset.x}% ${asset.y}%`;
      box.append(img);
    }});
  }));
  document.querySelectorAll('[data-remove-character-image]').forEach(button=>button.addEventListener('click',()=>{
    const field=button.closest('[data-character-image-field]');
    field.querySelector('[name=image_asset]').value='';
    const picker=field.querySelector('[data-profile-image-picker]');
    delete picker.dataset.selectedImage;
    picker.dataset.imageSource='';
    const initial=document.createElement('span');
    initial.textContent=(button.closest('form').querySelector('[name=nome]').value.trim()[0] || '?').toUpperCase();
    field.querySelector('[data-profile-image-preview]').replaceChildren(initial);
  }));
});
