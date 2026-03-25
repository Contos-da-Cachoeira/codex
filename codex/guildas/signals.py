from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import IntegrityError

from personagens.models import Personagem
from guildas.models import Guilda, GuildaMembro


@receiver(post_save, sender=Personagem)
def registrar_user_como_membro_guilda(sender, instance, created, **kwargs):
    """
    Signal que registra automaticamente um usuário como membro de uma guilda
    quando ele cria um personagem naquela guilda.
    """
    
    # Apenas processar se a guilda foi definida
    if instance.guilda is None:
        return
    
    # Apenas processar quando o personagem é criado
    if not created:
        return
    
    try:
        guilda = Guilda.objects.get(guilda_id=instance.guilda)
        
        # Criar o registro de membro
        membro, membro_created = GuildaMembro.objects.get_or_create(
            guilda=guilda,
            usuario=instance.usuario
        )
        
        # Atualizar contadores (incrementar)
        if membro_created:
            guilda.total_membros += 1
        
        guilda.total_personagens += 1
        guilda.save()
        
    except Guilda.DoesNotExist:
        # Se a guilda não existir, apenas ignorar
        pass
    except IntegrityError:
        # Se houver erro de integridade, apenas ignorar
        pass


@receiver(post_save, sender=Personagem)
def atualizar_status_personagem_guilda(sender, instance, **kwargs):
    """
    Signal para atualizar os contadores quando o status de um personagem muda.
    """
    # Este é um exemplo de como você poderia expandir a lógica
    # Por enquanto, apenas acionamos o primeiro signal
    pass
