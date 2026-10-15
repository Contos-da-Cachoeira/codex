from django.db import migrations
from django.db.models import Sum


def consolidate(apps, schema_editor):
    Character = apps.get_model('personagens', 'Personagem')
    Profile = apps.get_model('core', 'Profile')
    Movement = apps.get_model('personagens', 'MovimentoXP')
    alias = schema_editor.connection.alias
    # Preserva os saldos anteriores sem inventar compras nem cobrar talentos antigos.
    for row in Character.objects.using(alias).values('usuario_id').annotate(total=Sum('xp_atual')):
        profile, _ = Profile.objects.using(alias).get_or_create(user_id=row['usuario_id'])
        total = row['total'] or 0
        profile.xp_disponivel += total
        profile.save(using=alias, update_fields=['xp_disponivel'])
        if total:
            Movement.objects.using(alias).create(jogador_id=row['usuario_id'], valor=total,
                saldo=profile.xp_disponivel, motivo='Migração dos saldos anteriores dos personagens')
    Character.objects.using(alias).update(revisao_manual=True)
    Character.objects.using(alias).filter(image_asset__isnull=False).update(portrait_mode='photo')


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0021_larpinscricao_presenca_confirmada_and_more'),
        ('personagens', '0006_personagem_afinidade_personagem_divindade_and_more'),
    ]
    operations = [migrations.RunPython(consolidate, migrations.RunPython.noop)]
