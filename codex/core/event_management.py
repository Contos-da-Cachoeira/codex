"""Contexto e gravação atômica da gestão de participantes de um LARP."""
from django.core.exceptions import ValidationError
from django.db import transaction

from personagens.models import Personagem
from personagens.rules import set_player_xp
from .constants.guildas import GUILDAS
from .forms import EventCharacterBalanceForm
from .models import LarpInscricao, Profile


EDITABLE = ('xp', 'ouro', 'taxa_paga', 'presenca')
GUILD_IMAGES = {guild['nome']: guild['imagem'] for guild in GUILDAS.values()}


def participant_values(registration, profile=None):
    profile = profile or registration.usuario.profile
    return {'xp': profile.xp_disponivel, 'ouro': str(registration.personagem.ouro),
            'taxa_paga': registration.taxa_paga, 'presenca': registration.presenca_confirmada}


def event_metrics(registrations):
    total = len(registrations)
    paid = sum(bool(item.taxa_paga) for item in registrations)
    present = sum(bool(item.presenca_confirmada) for item in registrations)
    return {'total': total, 'paid': paid, 'pending': total - paid, 'present': present,
            'alerts': sum(bool(item.fobia_gatilho.strip()) for item in registrations),
            'paid_percent': round(paid * 100 / total) if total else 0,
            'present_percent': round(present * 100 / total) if total else 0}


def participant_rows(registrations, data=None):
    rows = []
    for registration in registrations:
        profile = getattr(registration.usuario, 'profile', None)
        if profile is None:
            profile, _ = Profile.objects.get_or_create(user=registration.usuario)
        current = participant_values(registration, profile)
        form = EventCharacterBalanceForm(data, prefix=f'character-{registration.personagem_id}',
            initial={**current, 'xp_anterior': current['xp'], 'ouro_anterior': current['ouro'],
                     'taxa_anterior': str(int(current['taxa_paga'])), 'presenca_anterior': str(int(current['presenca']))})
        for name in EDITABLE:
            form.fields[name].widget.attrs['data-event-field'] = name
            value = current[name]
            form.fields[name].widget.attrs['data-initial'] = str(int(value)) if isinstance(value, bool) else str(value)
        guild_name = registration.personagem.get_guilda_display() or 'Sem guilda'
        rows.append({'registration': registration, 'form': form,
                     'guild_name': guild_name, 'guild_image': GUILD_IMAGES.get(guild_name, '')})
    return rows


class ParticipantConflict(ValidationError):
    def __init__(self, ids):
        self.ids = ids
        super().__init__('Alguns dados foram alterados por outra operação. Recarregue os participantes em conflito antes de salvar; suas outras edições foram mantidas.')


@transaction.atomic
def save_participants(event, rows, actor, changes=None, include_payments=True):
    """Bloqueia saldos em ordem estável e verifica tudo antes de gravar.

    ``changes`` limita uma edição em segundo plano aos campos alterados. Reenvios
    com o mesmo resultado são inofensivos, inclusive após uma resposta perdida.
    """
    staged, conflicts = [], []
    for row in sorted(rows, key=lambda item: item['registration'].usuario_id):
        source = row['registration']
        wallet = Profile.objects.select_for_update().get(user_id=source.usuario_id)
        character = Personagem.objects.select_for_update().get(pk=source.personagem_id)
        registration = LarpInscricao.objects.select_for_update().get(pk=source.pk, evento=event)
        if (registration.usuario_id, registration.personagem_id) != (source.usuario_id, source.personagem_id):
            conflicts.append(registration.pk)
            continue
        cleaned = row['form'].cleaned_data
        fields = changes[source.pk] if changes is not None else tuple(name for name in EDITABLE if name != 'taxa_paga' or include_payments)
        actual = {'xp': wallet.xp_disponivel, 'ouro': character.ouro,
                  'taxa_paga': registration.taxa_paga, 'presenca': registration.presenca_confirmada}
        for name, previous in (('xp','xp_anterior'),('ouro','ouro_anterior'),
                               ('taxa_paga','taxa_anterior'),('presenca','presenca_anterior')):
            if name not in fields:
                continue
            expected = cleaned.get(previous)
            if (changes is not None and expected is None) or (expected is not None and actual[name] != expected and actual[name] != cleaned[name]):
                conflicts.append(registration.pk)
                break
        staged.append((registration, character, wallet, cleaned, fields))
    if conflicts:
        raise ParticipantConflict(sorted(set(conflicts)))
    saved = []
    for registration, character, wallet, cleaned, fields in staged:
        if 'xp' in fields and wallet.xp_disponivel != cleaned['xp']:
            set_player_xp(registration.usuario, cleaned['xp'], actor, 'Ajuste na planilha: ' + event.titulo,
                          expected=cleaned.get('xp_anterior'))
            wallet.xp_disponivel = cleaned['xp']
        if 'ouro' in fields and character.ouro != cleaned['ouro']:
            character.ouro = cleaned['ouro']
            character.save(update_fields=['ouro', 'data_atualizacao'])
        changed = []
        for name, model_name in (('taxa_paga','taxa_paga'),('presenca','presenca_confirmada')):
            if name in fields and getattr(registration, model_name) != cleaned[name]:
                setattr(registration, model_name, cleaned[name])
                changed.append(model_name)
        if changed:
            registration.save(update_fields=changed)
        saved.append({'id': registration.pk, 'xp': wallet.xp_disponivel, 'ouro': str(character.ouro),
                      'taxa_paga': registration.taxa_paga, 'presenca': registration.presenca_confirmada})
    return saved
