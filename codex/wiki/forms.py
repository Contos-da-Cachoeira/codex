from django import forms

from .models import WikiEntry


FIELDS = {
    'regras': 'categoria resumo ordem secoes',
    'classes': 'tipo descricao sabe_usar defesas magia foco item_inicial habilidade_especial habilidade_detalhes extra',
    'talentos': 'descricao custo_xp stackavel requisito restricao extra',
    'magias': 'tipo quem_usa invocacao descricao extra',
    'itens': 'tipo descricao valor raridade alquimico',
    'magia_geral': 'itens',
    'cenario': 'categoria resumo ordem secoes',
}
LABELS = {'descricao': 'Descrição', 'sabe_usar': 'Sabe usar', 'item_inicial': 'Item inicial',
          'habilidade_especial': 'Habilidade especial', 'habilidade_detalhes': 'Detalhes da habilidade',
          'custo_xp': 'Custo em XP', 'stackavel': 'Pode acumular', 'restricao': 'Restrição',
          'quem_usa': 'Quem usa', 'invocacao': 'Invocação', 'alquimico': 'Alquímico',
          'secoes': 'Seções', 'itens': 'Regras', 'foco': 'Focos de magia'}
LISTS = {'habilidade_detalhes', 'quem_usa', 'itens'}


class WikiEntryForm(forms.ModelForm):
    remove_image = forms.BooleanField(label='Remover imagem atual', required=False)
    class Meta:
        model = WikiEntry
        fields = ['name', 'slug', 'image', 'visible']
        help_texts = {'slug': 'Identificador do link. Use letras sem acentos e hífens.'}

    def __init__(self, *args, category, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.category = category
        if category == 'classes':
            self.fields['name'].help_text = 'As nove classes jogáveis seguem o Manual 3.3. Novas entradas nesta seção são referências; não criam uma nova classe mecânica.'
        for key in FIELDS[category].split():
            value = self.instance.data.get(key, '')
            options = {'label': LABELS.get(key, key.replace('_', ' ').capitalize()), 'required': False}
            if key in {'stackavel', 'alquimico'}:
                field = forms.BooleanField(**options)
            elif key in {'ordem', 'custo_xp'}:
                field = forms.IntegerField(min_value=0, **options)
            else:
                field = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), **options)
                if key in LISTS:
                    value = '\n'.join(value) if value else ''
                    field.help_text = 'Um item por linha.'
                if key == 'secoes':
                    value = '\n\n'.join('\n'.join([s['titulo'], *s['itens']]) for s in value) if value else ''
                    field.help_text = 'Em cada bloco: título na primeira linha e tópicos nas próximas. Separe os blocos com uma linha vazia.'
            field.initial = value
            self.fields[key] = field
        if category == 'talentos':
            self.fields['custo_xp'].help_text = 'Valor aplicado às novas solicitações. Compras e solicitações já registradas mantêm o preço informado na aquisição.'
            self.fields['stackavel'].help_text = 'Permite novas compras repetidas. Aquisições anteriores são preservadas.'
        if category == 'magias':
            self.fields['quem_usa'].help_text = 'Um nome por linha: Bardo, Clérigo, Druida, Mago ou Paladino. Esta lista também define as escolhas na ficha.'
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                css = 'checkbox'
            elif isinstance(field.widget, forms.Textarea):
                css = 'textarea textarea-bordered w-full'
            else:
                css = 'input input-bordered w-full'
            field.widget.attrs.setdefault('class', css)

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and image.size > 10 * 1024 * 1024:
            raise forms.ValidationError('A imagem deve ter no máximo 10 MB.')
        return image

    def clean(self):
        cleaned = super().clean()
        if self.instance.category == 'magia_geral' and WikiEntry.objects.filter(category='magia_geral').exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('As regras gerais de magia já existem. Edite a entrada existente.')
        if WikiEntry.objects.filter(category=self.instance.category, slug=cleaned.get('slug')).exclude(pk=self.instance.pk).exists():
            self.add_error('slug', 'Já existe uma entrada com esse link nesta seção.')
        data = dict(self.instance.data)
        for key in FIELDS[self.instance.category].split():
            value = cleaned.get(key)
            if key in LISTS:
                value = [line.strip() for line in (value or '').splitlines() if line.strip()]
            elif key == 'secoes':
                value = [{'titulo': lines[0], 'itens': lines[1:]} for block in (value or '').replace('\r\n', '\n').split('\n\n')
                         if (lines := [line.strip() for line in block.splitlines() if line.strip()])]
            elif key in {'ordem', 'custo_xp'}:
                value = value or 0
            data[key] = value
        self.instance.data = data
        if self.instance.category == 'magias':
            allowed = {'Bardo', 'Clérigo', 'Druida', 'Mago', 'Paladino'}
            if set(data['quem_usa']) - allowed:
                self.add_error('quem_usa', 'Use os nomes das classes conjuradoras: Bardo, Clérigo, Druida, Mago ou Paladino.')
            # O nome é a identidade utilizada nas fichas existentes; nunca renomear silenciosamente uma magia aprendida.
            if self.instance.pk:
                previous = WikiEntry.objects.get(pk=self.instance.pk)
                if previous.name != cleaned.get('name'):
                    from personagens.models import Personagem, CompraTalento
                    used = CompraTalento.objects.filter(magia=previous.name).exists() or any(
                        previous.name in names for names in Personagem.objects.values_list('magias_pretendidas', flat=True))
                    if used:
                        self.add_error('name', 'Esta magia consta em fichas ou compras. Preserve o nome; edite a descrição ou crie outra magia.')
        return cleaned

    def save(self, commit=True):
        if self.cleaned_data.get('remove_image'):
            self.instance.image = ''
            self.instance.data.pop('imagem', None)
        return super().save(commit=commit)
