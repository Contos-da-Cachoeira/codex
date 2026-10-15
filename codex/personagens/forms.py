from django import forms
from django.db import transaction
from django.core.exceptions import ValidationError
from accounts.forms import birth_date_field

from core.models import ImageAsset, LarpInscricao, Profile
from wiki.constants.talentos import TALENTOS_WIKI
from wiki.catalog import talent_catalog, spells_by_class, all_spells

from .consts import (
    CLASSES_CHOICES,
    CLASSES_CONJURADORAS,
    CLASSES_CONJURADORAS_FIXAS,
    GUILDAS_CHOICES,
    MAGIAS_POR_CLASSE,
)
from .models import Personagem, CompraTalento
from .rules import ANCIENT_SPELLS, ALL_SPELLS, REPEATABLE, validate_base, validate_talent
from .identity import FOCUS_TYPES, validate_divinity


def _talentos_choices():
    talentos = []
    for talento in TALENTOS_WIKI.values():
        nome = talento.get('nome', '').strip()
        if nome:
            talentos.append((nome, nome))
    talentos.sort(key=lambda item: item[0].lower())
    return talentos


class PersonagemCreateForm(forms.Form):
    image_asset = forms.ModelChoiceField(queryset=ImageAsset.objects.none(), required=False, widget=forms.HiddenInput)
    nome = forms.CharField(max_length=120, required=True)
    descricao_personagem = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=True)
    guilda = forms.ChoiceField(choices=GUILDAS_CHOICES, required=True)
    classe = forms.ChoiceField(choices=CLASSES_CHOICES, required=True)
    portrait_mode = forms.ChoiceField(choices=Personagem._meta.get_field('portrait_mode').choices, required=False)
    feitico_antigo = forms.ChoiceField(choices=[('', 'Selecione')] + [(s, s) for s in ANCIENT_SPELLS], required=False)
    divindade = forms.CharField(max_length=120, required=False)
    afinidade = forms.CharField(max_length=200, required=False)

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
    talent_requests = forms.JSONField(required=False, widget=forms.HiddenInput, initial=list)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.pending_talents = []

        self.fields['image_asset'].queryset = ImageAsset.objects.filter(owner=user) if user else ImageAsset.objects.none()

        classe_value = self.data.get('classe') if self.is_bound else self.initial.get('classe')
        try:
            classe_id = int(classe_value)
        except (TypeError, ValueError):
            classe_id = None

        magias = spells_by_class().get(classe_id, [])
        self.fields['magias_pretendidas'].choices = [(magia, magia) for magia in magias]

    def clean(self):
        cleaned_data = super().clean()

        classe_raw = cleaned_data.get('classe')
        try:
            classe_id = int(classe_raw)
        except (TypeError, ValueError):
            classe_id = None

        if cleaned_data.get('talentos_iniciais'):
            self.add_error('talentos_iniciais', 'Talentos precisam ser adquiridos com XP na evolução da ficha; não há talentos gratuitos na criação.')

        if classe_id in CLASSES_CONJURADORAS:
            magias_disponiveis = spells_by_class().get(classe_id, [])
            if classe_id in CLASSES_CONJURADORAS_FIXAS:
                cleaned_data['magias_pretendidas'] = magias_disponiveis
            else:
                magias = cleaned_data.get('magias_pretendidas') or []
                magias_invalidas = [magia for magia in magias if magia not in magias_disponiveis]
                if magias_invalidas:
                    self.add_error('magias_pretendidas', 'As magias selecionadas nao sao validas para essa classe.')
        else:
            if self.data.get('magias_pretendidas'):
                self.add_error('magias_pretendidas', 'Esta classe não possui magias iniciais.')
            cleaned_data['magias_pretendidas'] = []

        candidate = Personagem(classe=classe_id, magias_pretendidas=cleaned_data.get('magias_pretendidas', []),
                               feitico_antigo=cleaned_data.get('feitico_antigo', ''),
                               divindade=cleaned_data.get('divindade', ''), afinidade=cleaned_data.get('afinidade', ''))
        try:
            validate_base(candidate)
        except ValidationError as error:
            for field, errors in error.message_dict.items():
                self.add_error(field, errors)
        mode = cleaned_data.get('portrait_mode') or ('photo' if cleaned_data.get('image_asset') else 'class')
        if mode == 'photo' and not cleaned_data.get('image_asset'):
            self.add_error('image_asset', 'Escolha uma foto ou use o nome ou a imagem da classe.')
        cleaned_data['portrait_mode'] = mode

        requests = cleaned_data.get('talent_requests') or []
        if not isinstance(requests, list) or len(requests) > 5:
            self.add_error('talent_requests', 'Selecione até cinco compras de talentos nesta etapa.')
            return cleaned_data
        seen, learned, total = set(), set(), 0
        for index, item in enumerate(requests, 1):
            if not isinstance(item, dict):
                self.add_error('talent_requests', 'Solicitação de talento inválida.')
                continue
            purchase_form = CompraTalentoForm(item, character=candidate)
            if not purchase_form.is_valid():
                details = '; '.join(str(error) for errors in purchase_form.errors.values() for error in errors)
                self.add_error('talent_requests', f'Talento {index}: {details}')
                continue
            purchase = purchase_form.save(commit=False)
            if purchase.talento in seen and not purchase.regra_snapshot.get('stackavel'):
                self.add_error('talent_requests', f'{purchase.nome} não permite compras repetidas.')
            if purchase.magia and purchase.magia in learned:
                self.add_error('talent_requests', f'A magia {purchase.magia} foi escolhida mais de uma vez.')
            seen.add(purchase.talento)
            learned.add(purchase.magia)
            total += purchase.custo_xp
            self.pending_talents.append(purchase)
        balance = getattr(getattr(self.user, 'profile', None), 'xp_disponivel', 0)
        if total > balance:
            self.add_error('talent_requests', f'As solicitações somam {total} XP. Seu saldo disponível é {balance} XP.')

        return cleaned_data

    @transaction.atomic
    def save(self):
        if self.user is None:
            raise ValueError('PersonagemCreateForm requer um usuario para salvar.')

        personagem = Personagem.objects.create(
            usuario=self.user,
            image_asset=self.cleaned_data.get('image_asset'),
            portrait_mode=self.cleaned_data['portrait_mode'],
            nome=self.cleaned_data['nome'].strip(),
            historia=self.cleaned_data['descricao_personagem'].strip(),
            aparencia='',
            objetivos='',
            personalidade='',
            guilda=int(self.cleaned_data['guilda']),
            classe=int(self.cleaned_data['classe']),
            magias_pretendidas=self.cleaned_data.get('magias_pretendidas', []),
            talentos_iniciais=self.cleaned_data.get('talentos_iniciais', []),
            feitico_antigo=self.cleaned_data.get('feitico_antigo', '') if int(self.cleaned_data['classe']) == 8 else '',
            divindade=self.cleaned_data.get('divindade', '') if int(self.cleaned_data['classe']) in {4, 9} else '',
            afinidade=self.cleaned_data.get('afinidade', '') if int(self.cleaned_data['classe']) == 5 else '',
        )
        for purchase in self.pending_talents:
            purchase.personagem = personagem
            purchase.save()
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

        profile.save(update_fields=['data_nascimento', 'nome_completo_jogador', 'apelido_cla', 'telefone', 'cpf', 'fobia_gatilho'])

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
    image_asset = forms.ModelChoiceField(queryset=ImageAsset.objects.none(), required=False, widget=forms.HiddenInput)
    magias_pretendidas = forms.MultipleChoiceField(choices=(), required=False, widget=forms.CheckboxSelectMultiple)
    feitico_antigo = forms.ChoiceField(choices=[('', 'Selecione')] + [(s, s) for s in ANCIENT_SPELLS], required=False)

    def __init__(self, *args, admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin = admin
        self.fields['image_asset'].queryset = ImageAsset.objects.filter(owner_id=self.instance.usuario_id)
        self.fields['classe'].disabled = not (admin and self.instance.revisao_manual)
        try:
            class_id = int(self.data.get('classe') or self.instance.classe or 0) if not self.fields['classe'].disabled else self.instance.classe
        except (TypeError, ValueError):
            class_id = None
        self.fields['magias_pretendidas'].choices = [(s, s) for s in spells_by_class(include_hidden=True).get(class_id, [])]
        for name in ('magias_pretendidas', 'feitico_antigo', 'afinidade'):
            self.fields[name].disabled = not (admin and self.instance.revisao_manual)
        self.fields['forma_selvagem'].disabled = not admin or bool(self.instance.forma_selvagem.strip())
        self.fields['forma_selvagem'].help_text = 'Definição permanente da comissão: três características e um defeito. Outra forma exige um novo talento.'
        self.fields['portrait_mode'].required = False
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxSelectMultiple, forms.HiddenInput)):
                field.widget.attrs['class'] = 'textarea textarea-bordered w-full' if isinstance(field.widget, forms.Textarea) else 'input input-bordered w-full'

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get('portrait_mode') or ('photo' if cleaned.get('image_asset') else 'name')
        if mode == 'photo' and not cleaned.get('image_asset'):
            self.add_error('image_asset', 'Escolha uma foto ou outra opção de identificação.')
        cleaned['portrait_mode'] = mode
        if self.instance.classe in {4, 9}:
            try:
                validate_divinity(cleaned.get('divindade', ''))
            except ValidationError as error:
                self.add_error('divindade', error)
        if self.admin and self.instance.revisao_manual:
            candidate = Personagem(classe=cleaned.get('classe'), magias_pretendidas=cleaned.get('magias_pretendidas', []),
                                   feitico_antigo=cleaned.get('feitico_antigo', ''), divindade=cleaned.get('divindade', ''),
                                   afinidade=cleaned.get('afinidade', ''), forma_selvagem=cleaned.get('forma_selvagem', ''))
            try:
                validate_base(candidate, require_commission=True)
            except ValidationError as error:
                for field, errors in error.message_dict.items():
                    self.add_error(field, errors)
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.admin and instance.revisao_manual:
            instance.revisao_manual = False
            instance.status_aprovacao = 1
        if any(field in self.changed_data for field in ('historia', 'divindade', 'guilda', 'forma_selvagem')):
            instance.status_aprovacao = 1
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Personagem
        fields = (
            'image_asset',
            'nome',
            'historia',
            'aparencia',
            'objetivos',
            'personalidade',
            'guilda',
            'classe',
            'portrait_mode', 'magias_pretendidas', 'feitico_antigo', 'divindade', 'afinidade', 'forma_selvagem',
        )

        widgets = {
            'historia': forms.Textarea(attrs={'rows': 4}),
            'aparencia': forms.Textarea(attrs={'rows': 3}),
            'objetivos': forms.Textarea(attrs={'rows': 3}),
            'personalidade': forms.Textarea(attrs={'rows': 3}),
            'classe': forms.Select(),
            'guilda': forms.Select(),
        }


class CompraTalentoForm(forms.ModelForm):
    talento = forms.ChoiceField(choices=())
    magia = forms.ChoiceField(choices=(), required=False, label='Magia ou feitiço antigo da segunda classe')
    tipo_foco = forms.ChoiceField(choices=[('', 'Selecione')] + list(FOCUS_TYPES), required=False)
    divindade = forms.CharField(max_length=120, required=False, label='Divindade da segunda classe')
    afinidade = forms.CharField(max_length=200, required=False, label='Afinidade da segunda classe Druida')
    talentos_relacionados = forms.MultipleChoiceField(choices=(), required=False, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = CompraTalento
        fields = ('talento', 'magia', 'segunda_classe', 'tipo_foco', 'foco', 'divindade', 'afinidade', 'detalhes', 'talentos_relacionados', 'justificativa')

    def __init__(self, *args, character, **kwargs):
        super().__init__(*args, **kwargs)
        self.character = character
        self.catalog = talent_catalog()
        self.fields['talento'].choices = [(k, f"{t['nome']} — {t['custo_xp']} XP") for k, t in self.catalog.items()]
        self.fields['magia'].choices = [('', 'Nenhuma')] + [(s, s) for s in all_spells() + list(ANCIENT_SPELLS)]
        self.fields['foco'].help_text = 'Um único foco, sem arma, escudo ou cajado. Objetos personalizados são avaliados pela comissão.'
        self.fields['divindade'].help_text = 'Informe uma divindade do cenário; escolhas personalizadas dependem da comissão.'
        self.fields['talentos_relacionados'].choices = [(str(p.pk), p.nome) for p in character.compras_talentos.filter(status='approved')] if character.pk else []
        for field in self.fields.values():
            field.widget.attrs['class'] = 'input input-bordered' if not isinstance(field.widget, (forms.Textarea, forms.CheckboxSelectMultiple)) else 'textarea textarea-bordered'

    def clean(self):
        cleaned = super().clean()
        purchase = CompraTalento(personagem=self.character, talento=cleaned.get('talento', ''),
                                 magia=cleaned.get('magia', ''), segunda_classe=cleaned.get('segunda_classe'),
                                 foco=cleaned.get('foco', ''), detalhes=cleaned.get('detalhes', ''),
                                 tipo_foco=cleaned.get('tipo_foco', ''),
                                 escolhas_classe={'divindade': cleaned.get('divindade', '').strip(), 'afinidade': cleaned.get('afinidade', '').strip()},
                                 talentos_relacionados=[int(i) for i in cleaned.get('talentos_relacionados', [])],
                                 justificativa=cleaned.get('justificativa', ''))
        try:
            validate_talent(self.character, purchase)
        except ValidationError as error:
            self.add_error(None, error)
        cleaned['talentos_relacionados'] = purchase.talentos_relacionados
        cleaned['escolhas_classe'] = purchase.escolhas_classe if purchase.talento == 'MULTICLASSE' else {}
        return cleaned

    def save(self, commit=True):
        purchase = super().save(commit=False)
        purchase.personagem = self.character
        purchase.regra_snapshot = self.catalog[purchase.talento]
        purchase.custo_xp = purchase.regra_snapshot['custo_xp']
        purchase.escolhas_classe = self.cleaned_data['escolhas_classe']
        if commit:
            purchase.save()
        return purchase


class MulticlassReviewForm(forms.Form):
    magia = forms.ChoiceField(choices=[('', 'Selecione')] + [(s, s) for s in ANCIENT_SPELLS], required=False, label='Feitiço antigo inicial')
    divindade = forms.CharField(max_length=120, required=False)
    afinidade = forms.CharField(max_length=200, required=False)
    forma_selvagem = forms.CharField(widget=forms.Textarea, required=False, label='Três características e um defeito definidos pela comissão')

    def __init__(self, *args, purchase, **kwargs):
        super().__init__(*args, **kwargs)
        names = {8: ('magia',), 4: ('divindade',), 9: ('divindade',), 5: ('afinidade','forma_selvagem')}.get(purchase.segunda_classe, ())
        for name in list(self.fields):
            if name not in names:
                del self.fields[name]
            else:
                self.fields[name].initial = purchase.magia if name == 'magia' else purchase.escolhas_classe.get(name, '')
                if name == 'magia' and self.fields[name].initial not in ANCIENT_SPELLS:
                    self.fields[name].initial = ''
                self.fields[name].disabled = bool(self.fields[name].initial)
                self.fields[name].required = True
                self.fields[name].widget.attrs['class'] = 'input input-bordered w-full' if name != 'forma_selvagem' else 'textarea textarea-bordered w-full'
