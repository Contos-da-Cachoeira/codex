from django.db import migrations


def register_guilds(apps, schema_editor):
    Guild = apps.get_model('guildas', 'Guilda')
    Member = apps.get_model('guildas', 'GuildaMembro')
    Character = apps.get_model('personagens', 'Personagem')
    alias = schema_editor.connection.alias
    slugs = ('artistas-da-revolucao', 'circulo-do-fogo', 'floresta-do-sol',
             'irmandade-das-tavernas', 'os-rasga-mortalhas', 'sociedade-zaori')
    for guild_id, slug in enumerate(slugs, 1):
        guild, _ = Guild.objects.using(alias).get_or_create(guilda_id=guild_id, defaults={'slug': slug, 'ativa': True})
        characters = Character.objects.using(alias).filter(guilda=guild_id, status=1, status_aprovacao=2)
        user_ids = list(characters.values_list('usuario_id', flat=True).distinct())
        Guild.objects.using(alias).filter(pk=guild.pk).update(total_personagens=characters.count(), total_membros=len(user_ids))
        Member.objects.using(alias).filter(guilda_id=guild_id).exclude(usuario_id__in=user_ids).delete()
        for user_id in user_ids:
            Member.objects.using(alias).get_or_create(guilda_id=guild_id, usuario_id=user_id)


class Migration(migrations.Migration):
    dependencies = [('guildas', '0001_initial'), ('personagens', '0008_compratalento_escolhas_classe_and_more')]
    operations = [migrations.RunPython(register_guilds, migrations.RunPython.noop)]
