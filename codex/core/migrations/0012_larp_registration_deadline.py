from django.db import migrations, models


def fill_deadlines(apps, schema_editor):
    Event = apps.get_model('core', 'LarpEvento')
    Event.objects.using(schema_editor.connection.alias).update(data_limite_inscricao=models.F('data_evento'))


class Migration(migrations.Migration):
    dependencies = [('core', '0011_merge_0010_core_migrations')]
    operations = [
        migrations.AddField(
            model_name='larpevento', name='data_limite_inscricao',
            field=models.DateTimeField(null=True, verbose_name='Inscrições até'),
        ),
        migrations.RunPython(fill_deadlines, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='larpevento', name='data_limite_inscricao',
            field=models.DateTimeField(verbose_name='Inscrições até'),
        ),
    ]
