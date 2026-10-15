from django import forms
from django.core.files.uploadedfile import UploadedFile

from .models import LarpEvento, ImageAsset
from .money import GoldField


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
    ouro = GoldField(label='Ouro (DO)')
    presenca = forms.BooleanField(label='Presença confirmada', required=False)
    taxa_paga = forms.BooleanField(label='Taxa paga', required=False)
    xp_anterior = forms.IntegerField(min_value=0, required=False, widget=forms.HiddenInput)
    ouro_anterior = GoldField(required=False, widget=forms.HiddenInput)
    taxa_anterior = forms.TypedChoiceField(choices=(('0', 'Não'), ('1', 'Sim')), coerce=lambda value: bool(int(value)), empty_value=None, required=False, widget=forms.HiddenInput)
    presenca_anterior = forms.TypedChoiceField(choices=(('0', 'Não'), ('1', 'Sim')), coerce=lambda value: bool(int(value)), empty_value=None, required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('xp', 'ouro'):
            self.fields[name].widget.attrs.update({'class': 'em-number', 'step': '1', 'inputmode': 'decimal' if name == 'ouro' else 'numeric'})
        for name in ('presenca', 'taxa_paga'):
            self.fields[name].widget.attrs['class'] = 'em-checkbox'
        self.fields['ouro'].widget.attrs['step'] = '0.5'


class LarpEventoForm(forms.ModelForm):
    def clean_capa(self):
        image = self.cleaned_data.get('capa')
        if isinstance(image, UploadedFile) and image.size > 10 * 1024 * 1024:
            raise forms.ValidationError('A capa deve ter no máximo 10 MB.')
        return image

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
