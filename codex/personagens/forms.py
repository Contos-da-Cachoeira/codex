from django import forms
from django.db import transaction
from accounts.forms import birth_date_field

from core.models import LarpInscricao, Profile
from wiki.constants.talentos import TALENTOS_WIKI

from .consts import (
    CLASSES_CHOICES,
    CLASSES_CONJURADORAS,
    CLASSES_CONJURADORAS_FIXAS,
    GUILDAS_CHOICES,
    MAGIAS_POR_CLASSE,
)
from .models import Personagem


def _talentos_choices():
    talentos = []
    for talento in TALENTOS_WIKI.values():
        nome = talento.get('nome', '').strip()
        if nome:
            talentos.append((nome, nome))
    talentos.sort(key=lambda item: item[0].lower())
    return talentos


class PersonagemCreateForm(forms.Form):
    nome = forms.CharField(max_length=120, required=True)
    descricao_personagem = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=True)
    guilda = forms.ChoiceField(choices=GUILDAS_CHOICES, required=True)
    classe = forms.ChoiceField(choices=CLASSES_CHOICES, required=True)

    magias_pretendidas = forms.MultipleChoiceField(
        choices=(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    talentos_iniciais = forms.MultipleChoiceField(
        choices=_talentos_choices(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    ciencia_concordancia = forms.BooleanField(required=True)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        classe_value = self.data.get('classe') if self.is_bound else self.initial.get('classe')
        try:
            classe_id = int(classe_value)
        except (TypeError, ValueError):
            classe_id = None

        magias = MAGIAS_POR_CLASSE.get(classe_id, [])
        self.fields['magias_pretendidas'].choices = [(magia, magia) for magia in magias]

    def clean(self):
        cleaned_data = super().clean()

        classe_raw = cleaned_data.get('classe')
        try:
            classe_id = int(classe_raw)
        except (TypeError, ValueError):
            classe_id = None

        talentos = cleaned_data.get('talentos_iniciais') or []
        if len(talentos) > 5:
            self.add_error('talentos_iniciais', 'O limite de talentos iniciais e 5.')

        if classe_id in CLASSES_CONJURADORAS:
            magias_disponiveis = MAGIAS_POR_CLASSE.get(classe_id, [])
            if classe_id in CLASSES_CONJURADORAS_FIXAS:
                cleaned_data['magias_pretendidas'] = magias_disponiveis
            else:
                magias = cleaned_data.get('magias_pretendidas') or []
                magias_invalidas = [magia for magia in magias if magia not in magias_disponiveis]
                if magias_invalidas:
                    self.add_error('magias_pretendidas', 'As magias selecionadas nao sao validas para essa classe.')
                if not magias:
                    self.add_error('magias_pretendidas', 'Selecione ao menos uma magia que o personagem sabe.')
        else:
            cleaned_data['magias_pretendidas'] = []

        return cleaned_data

    @transaction.atomic
    def save(self):
        if self.user is None:
            raise ValueError('PersonagemCreateForm requer um usuario para salvar.')

        personagem = Personagem.objects.create(
            usuario=self.user,
            nome=self.cleaned_data['nome'].strip(),
            historia=self.cleaned_data['descricao_personagem'].strip(),
            aparencia='',
            objetivos='',
            personalidade='',
            guilda=int(self.cleaned_data['guilda']),
            classe=int(self.cleaned_data['classe']),
            magias_pretendidas=self.cleaned_data.get('magias_pretendidas', []),
            talentos_iniciais=self.cleaned_data.get('talentos_iniciais', []),
        )
        return personagem


class LarpInscricaoEventoForm(forms.Form):
    data_nascimento = birth_date_field()
    nome_confirmado = forms.BooleanField(required=False)
    nome_completo_jogador = forms.CharField(max_length=180, required=False)
    apelido_cla = forms.CharField(max_length=120, required=False)

    telefone_cpf_confirmado = forms.BooleanField(required=False)
    telefone = forms.CharField(max_length=30, required=False)
    cpf = forms.CharField(max_length=14, required=False)

    possui_fobia_gatilho = forms.ChoiceField(
        choices=(('sim', 'Sim'), ('nao', 'Nao')),
        required=False,
    )
    fobia_gatilho = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)

    personagem = forms.ModelChoiceField(queryset=Personagem.objects.none(), required=True)
    ciencia_concordancia = forms.BooleanField(required=True)

    def __init__(self, *args, user=None, evento=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.evento = evento
        self.profile = None

        if user is not None:
            self.profile, _ = Profile.objects.get_or_create(user=user)
            self.fields['personagem'].queryset = Personagem.objects.filter(usuario=user).order_by('nome')

        nome_sistema = self._nome_sistema()
        nome_profile = (self.profile.nome_completo_jogador.strip() if self.profile else '')
        apelido_profile = (self.profile.apelido_cla.strip() if self.profile else '')
        contato_no_sistema = bool(
            self.profile
            and self.profile.telefone.strip()
            and self.profile.cpf.strip()
        )
        fobia_no_sistema = bool(self.profile and self.profile.fobia_gatilho.strip())

        self.player_data_status = {
            'nome_existe': bool(nome_sistema),
            'nome_em_profile_existe': bool(nome_profile),
            'apelido_existe': bool(apelido_profile),
            'contato_existe': contato_no_sistema,
            'fobia_existe': fobia_no_sistema,
        }
        self.player_data_preview = {
            'nome_completo_jogador': nome_sistema,
            'apelido_cla': apelido_profile,
        }

        if self.profile and not self.is_bound:
            self.fields['data_nascimento'].initial = self.profile.data_nascimento
            self.fields['nome_completo_jogador'].initial = nome_profile or nome_sistema
            self.fields['apelido_cla'].initial = apelido_profile
            self.fields['telefone'].initial = self.profile.telefone
            self.fields['cpf'].initial = self.profile.cpf
            self.fields['possui_fobia_gatilho'].initial = 'sim' if self.profile.fobia_gatilho.strip() else 'nao'
            self.fields['fobia_gatilho'].initial = self.profile.fobia_gatilho

    def _nome_sistema(self):
        if self.profile and self.profile.nome_completo_jogador.strip():
            return self.profile.nome_completo_jogador.strip()
        if self.user:
            nome = ' '.join(part for part in [self.user.first_name, self.user.last_name] if part).strip()
            return nome
        return ''

    def clean(self):
        cleaned_data = super().clean()

        nome_existe = self.player_data_status.get('nome_existe', False)
        nome_em_profile_existe = self.player_data_status.get('nome_em_profile_existe', False)
        contato_existe = self.player_data_status.get('contato_existe', False)

        if nome_existe:
            if not cleaned_data.get('nome_confirmado'):
                self.add_error('nome_confirmado', 'Confirme se o nome do jogador esta correto para continuar.')
            if not nome_em_profile_existe and not (cleaned_data.get('nome_completo_jogador') or '').strip():
                self.add_error('nome_completo_jogador', 'Complete o nome do jogador para salvar no cadastro.')
        else:
            if not (cleaned_data.get('nome_completo_jogador') or '').strip():
                self.add_error('nome_completo_jogador', 'Informe o nome completo do jogador.')

        if contato_existe:
            if not cleaned_data.get('telefone_cpf_confirmado'):
                self.add_error('telefone_cpf_confirmado', 'Confirme telefone e CPF para continuar.')
        else:
            if not (cleaned_data.get('telefone') or '').strip():
                self.add_error('telefone', 'Informe o telefone.')
            if not (cleaned_data.get('cpf') or '').strip():
                self.add_error('cpf', 'Informe o CPF.')

        possui_fobia_gatilho = cleaned_data.get('possui_fobia_gatilho')
        if possui_fobia_gatilho not in ('sim', 'nao'):
            self.add_error('possui_fobia_gatilho', 'Responda se possui fobia ou gatilho psicologico.')
        elif possui_fobia_gatilho == 'sim':
            if not (cleaned_data.get('fobia_gatilho') or '').strip():
                self.add_error('fobia_gatilho', 'Descreva qual fobia ou gatilho psicologico voce possui.')
        else:
            cleaned_data['fobia_gatilho'] = ''

        personagem = cleaned_data.get('personagem')
        if personagem and self.user and personagem.usuario_id != self.user.id:
            self.add_error('personagem', 'Selecione um personagem da sua conta.')

        if self.evento and self.user:
            if LarpInscricao.objects.filter(evento=self.evento, usuario=self.user).exists():
                self.add_error('personagem', 'Voce ja possui inscricao neste LARP.')

        return cleaned_data

    @transaction.atomic
    def save(self):
        if self.user is None or self.evento is None:
            raise ValueError('LarpInscricaoEventoForm requer usuario e evento para salvar.')

        profile, _ = Profile.objects.get_or_create(user=self.user)
        profile.data_nascimento = self.cleaned_data['data_nascimento']
        if not self.player_data_status.get('nome_existe'):
            profile.nome_completo_jogador = self.cleaned_data['nome_completo_jogador'].strip()
            profile.apelido_cla = self.cleaned_data.get('apelido_cla', '').strip()
        else:
            if not profile.nome_completo_jogador.strip() and (self.cleaned_data.get('nome_completo_jogador') or '').strip():
                profile.nome_completo_jogador = self.cleaned_data['nome_completo_jogador'].strip()
            if not profile.apelido_cla.strip() and (self.cleaned_data.get('apelido_cla') or '').strip():
                profile.apelido_cla = self.cleaned_data['apelido_cla'].strip()

        if not self.player_data_status.get('contato_existe'):
            profile.telefone = self.cleaned_data['telefone'].strip()
            profile.cpf = self.cleaned_data['cpf'].strip()

        if self.cleaned_data.get('possui_fobia_gatilho') == 'sim':
            profile.fobia_gatilho = self.cleaned_data['fobia_gatilho'].strip()
        else:
            profile.fobia_gatilho = ''

        profile.save()

        inscricao = LarpInscricao.objects.create(
            evento=self.evento,
            usuario=self.user,
            personagem=self.cleaned_data['personagem'],
            nome_completo_jogador=profile.nome_completo_jogador.strip(),
            apelido_cla=profile.apelido_cla.strip(),
            telefone=profile.telefone.strip(),
            cpf=profile.cpf.strip(),
            fobia_gatilho=profile.fobia_gatilho.strip(),
            confirmacao_final=self.cleaned_data['ciencia_concordancia'],
        )
        return inscricao


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
