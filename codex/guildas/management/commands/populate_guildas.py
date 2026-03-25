from django.core.management.base import BaseCommand
from guildas.models import Guilda, GUILDA_NOMES


class Command(BaseCommand):
    help = 'Popula o banco de dados com as guildas iniciais'

    def handle(self, *args, **options):
        created_count = 0
        
        for guilda_id, nome in GUILDA_NOMES.items():
            guilda, created = Guilda.objects.get_or_create(
                guilda_id=guilda_id,
                defaults={
                    'descricao_interna': '',
                    'total_membros': 0,
                    'total_personagens': 0,
                    'ativa': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Criada: {nome}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Já existe: {nome}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal de guildas criadas: {created_count}')
        )
