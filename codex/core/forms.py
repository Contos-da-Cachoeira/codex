from django import forms

from .models import LarpEvento, ImageAsset


class ImageAssetForm(forms.ModelForm):
    class Meta:
        model = ImageAsset
        fields = ('file', 'url', 'x', 'y', 'zoom', 'ratio')

    def clean(self):
        data = super().clean()
        if bool(data.get('file')) == bool(data.get('url')):
            raise forms.ValidationError('Escolha um arquivo ou informe uma URL.')
        if data.get('url') and not data['url'].startswith(('https://', 'http://')):
            self.add_error('url', 'Use uma URL HTTP ou HTTPS.')
        file = data.get('file')
        if file and file.size > 10 * 1024 * 1024:
            self.add_error('file', 'Limite de 10 MB por imagem.')
        for name, minimum, maximum in [('x', 0, 100), ('y', 0, 100), ('zoom', 1, 3), ('ratio', .25, 4)]:
            value = data.get(name)
            if name in self.errors:
                continue
            if value is None or not minimum <= value <= maximum:
                self.add_error(name, 'Enquadramento inválido.')
        return data


class EventCharacterBalanceForm(forms.Form):
    xp = forms.IntegerField(label='XP', min_value=0, max_value=2147483647)
    ouro = forms.IntegerField(label='Ouro', min_value=0, max_value=2147483647)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'input input-bordered', 'style': 'width:8rem', 'step': '1'})


class LarpEventoForm(forms.ModelForm):
    class Meta:
        model = LarpEvento
        fields = ('titulo', 'capa', 'local', 'data_evento', 'data_limite_inscricao', 'historia', 'visivel_publicamente')
        labels = {
            'titulo': 'Título', 'capa': 'Capa do evento', 'local': 'Local', 'data_evento': 'Data e horário do evento',
            'data_limite_inscricao': 'Inscrições até', 'historia': 'História',
            'visivel_publicamente': 'Visível para usuários comuns',
        }
        widgets = {
            'data_evento': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
            'data_limite_inscricao': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
            'historia': forms.Textarea(attrs={'rows': 5}),
            'capa': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'checkbox'
            else:
                field.widget.attrs['class'] = 'textarea textarea-bordered' if isinstance(field.widget, forms.Textarea) else 'input input-bordered'
                field.widget.attrs['style'] = 'width:100%;max-width:none'
