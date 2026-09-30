from django.db import migrations


def seed(apps, schema_editor):
    Section = apps.get_model('core', 'HomeDynamicSection')
    sections = Section.objects.using(schema_editor.connection.alias)
    if not sections.filter(kind='community').exists():
        sections.create(kind='community', eyebrow='Comunidade', title='Guildas em destaque',
                        content='Conheça os grupos que dão vida ao mundo do Codex.', display_order=1)


class Migration(migrations.Migration):
    dependencies = [('core', '0014_homedynamicsection_eyebrow_and_more')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
