from django.core.management.base import BaseCommand

from guildas.models import Guilda, GuildaMembro
from personagens.models import Personagem
from personagens.consts import STATUS_APROVACAO, STATUS_PERSONAGEM


class Command(BaseCommand):
    help = 'Recalcula os contadores de membros e personagens de todas as guildas'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando recalculação de contadores...'))

        # Obter todas as guildas
        guildas = Guilda.objects.all()

        for guilda in guildas:
            # Contar personagens aprovados e ativos
            total_personagens = Personagem.objects.filter(
                guilda=guilda.guilda_id,
                status_aprovacao=STATUS_APROVACAO.APROVADO,
                status=STATUS_PERSONAGEM.ATIVO,
            ).count()

            # Contar usuários únicos com pelo menos 1 personagem aprovado e ativo
            usuarios_unicos = Personagem.objects.filter(
                guilda=guilda.guilda_id,
                status_aprovacao=STATUS_APROVACAO.APROVADO,
                status=STATUS_PERSONAGEM.ATIVO,
            ).values('usuario').distinct().count()

            # Atualizar guilda
            guilda.total_personagens = total_personagens
            guilda.total_membros = usuarios_unicos
            guilda.save()

            self.stdout.write(
                f'{guilda} - Membros: {usuarios_unicos}, Personagens: {total_personagens}'
            )

            # Sincronizar tabela GuildaMembro para refletir exatamente os ativos.
            usuarios_com_personagens = list(Personagem.objects.filter(
                guilda=guilda.guilda_id,
                status_aprovacao=STATUS_APROVACAO.APROVADO,
                status=STATUS_PERSONAGEM.ATIVO,
            ).values_list('usuario', flat=True).distinct())

            GuildaMembro.objects.filter(guilda=guilda).exclude(usuario_id__in=usuarios_com_personagens).delete()

            for usuario_id in usuarios_com_personagens:
                GuildaMembro.objects.get_or_create(
                    guilda=guilda,
                    usuario_id=usuario_id
                )

        self.stdout.write(self.style.SUCCESS('Recalculação concluída com sucesso!'))
