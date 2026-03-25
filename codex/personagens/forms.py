from django import forms

from .models import Personagem


class PersonagemCreateForm(forms.ModelForm):
    class Meta:
        model = Personagem
        fields = (
            'nome',
            'historia',
            'aparencia',
            'objetivos',
            'personalidade',
            'guilda',
            'classe',
        )

        widgets = {
            'historia': forms.Textarea(attrs={'rows': 4}),
            'aparencia': forms.Textarea(attrs={'rows': 3}),
            'objetivos': forms.Textarea(attrs={'rows': 3}),
            'personalidade': forms.Textarea(attrs={'rows': 3}),
            'classe': forms.Select(),
            'guilda': forms.Select(),
        }


class PersonagemUpdateForm(forms.ModelForm):
    class Meta:
        model = Personagem
        fields = (
            'nome',
            'historia',
            'aparencia',
            'objetivos',
            'personalidade',
            'guilda',
            'classe',
        )

        widgets = {
            'historia': forms.Textarea(attrs={'rows': 4}),
            'aparencia': forms.Textarea(attrs={'rows': 3}),
            'objetivos': forms.Textarea(attrs={'rows': 3}),
            'personalidade': forms.Textarea(attrs={'rows': 3}),
            'classe': forms.Select(),
            'guilda': forms.Select(),
        }
