from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from personagens.models import Personagem
from personagens.consts import STATUS_APROVACAO, STATUS_PERSONAGEM
from guildas.models import Guilda, GuildaMembro


def _recalcular_guilda(guilda_id):
    """Recalcula contadores e tabela de membros a partir dos personagens aprovados e ativos."""
    if guilda_id is None:
        return

    try:
        guilda = Guilda.objects.get(guilda_id=guilda_id)
    except Guilda.DoesNotExist:
        return

    personagens_ativos = Personagem.objects.filter(
        guilda=guilda_id,
        status_aprovacao=STATUS_APROVACAO.APROVADO,
        status=STATUS_PERSONAGEM.ATIVO,
    )

    total_personagens = personagens_ativos.count()
    usuarios_ids = list(personagens_ativos.values_list("usuario_id", flat=True).distinct())

    guilda.total_personagens = total_personagens
    guilda.total_membros = len(usuarios_ids)
    guilda.save(update_fields=["total_personagens", "total_membros", "data_atualizacao"])

    # Sincroniza tabela GuildaMembro para refletir exatamente os usuários com personagens ativos.
    GuildaMembro.objects.filter(guilda=guilda).exclude(usuario_id__in=usuarios_ids).delete()
    for usuario_id in usuarios_ids:
        GuildaMembro.objects.get_or_create(guilda=guilda, usuario_id=usuario_id)


@receiver(pre_save, sender=Personagem)
def guardar_guilda_antiga(sender, instance, **kwargs):
    """Guarda guilda antiga para permitir recálculo quando personagem troca de guilda."""
    instance._guilda_antiga = None
    if instance.pk:
        try:
            antigo = Personagem.objects.get(pk=instance.pk)
            instance._guilda_antiga = antigo.guilda
        except Personagem.DoesNotExist:
            pass


@receiver(post_save, sender=Personagem)
def atualizar_contadores_em_save(sender, instance, **kwargs):
    """Recalcula guilda atual e, se mudou, também a guilda anterior."""
    _recalcular_guilda(instance.guilda)
    guilda_antiga = getattr(instance, "_guilda_antiga", None)
    if guilda_antiga is not None and guilda_antiga != instance.guilda:
        _recalcular_guilda(guilda_antiga)


@receiver(post_delete, sender=Personagem)
def atualizar_contadores_em_delete(sender, instance, **kwargs):
    """Recalcula contadores quando personagem é removido."""
    _recalcular_guilda(instance.guilda)
