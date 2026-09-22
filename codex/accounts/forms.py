from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from core.models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class AccountPersonalDataForm(forms.ModelForm):
    avatar = forms.ImageField(required=False)
    nome_completo_jogador = forms.CharField(max_length=180, required=False)
    apelido_cla = forms.CharField(max_length=120, required=False)
    telefone = forms.CharField(max_length=30, required=False)
    cpf = forms.CharField(max_length=14, required=False)
    fobia_gatilho = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)

    class Meta:
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile
        self.fields['email'].required = True

        if self.profile is not None:
            self.fields['avatar'].initial = self.profile.avatar
            self.fields['nome_completo_jogador'].initial = self.profile.nome_completo_jogador
            self.fields['apelido_cla'].initial = self.profile.apelido_cla
            self.fields['telefone'].initial = self.profile.telefone
            self.fields['cpf'].initial = self.profile.cpf
            self.fields['fobia_gatilho'].initial = self.profile.fobia_gatilho

    def save(self, commit=True):
        user = super().save(commit=commit)
        user.first_name = ''
        user.last_name = ''
        if commit:
            user.save(update_fields=['username', 'email', 'first_name', 'last_name'])

        profile = self.profile or Profile.objects.get_or_create(user=user)[0]
        if self.cleaned_data.get('avatar'):
            profile.avatar = self.cleaned_data['avatar']
        profile.nome_completo_jogador = (self.cleaned_data.get('nome_completo_jogador') or '').strip()
        profile.apelido_cla = (self.cleaned_data.get('apelido_cla') or '').strip()
        profile.telefone = (self.cleaned_data.get('telefone') or '').strip()
        profile.cpf = (self.cleaned_data.get('cpf') or '').strip()
        profile.fobia_gatilho = (self.cleaned_data.get('fobia_gatilho') or '').strip()

        if commit:
            profile.save()
        return user
