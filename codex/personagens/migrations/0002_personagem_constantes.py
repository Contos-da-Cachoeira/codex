from django.db import migrations, models


def _normalize(value):
    if value is None:
        return ''
    text = str(value).strip().lower()
    replacements = {
        'á': 'a',
        'à': 'a',
        'â': 'a',
        'ã': 'a',
        'é': 'e',
        'ê': 'e',
        'í': 'i',
        'ó': 'o',
        'ô': 'o',
        'õ': 'o',
        'ú': 'u',
        'ç': 'c',
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def migrate_personagem_data(apps, schema_editor):
    Personagem = apps.get_model('personagens', 'Personagem')

    guild_map = {
        'artistas da revolucao': 1,
        'circulo do fogo': 2,
        'floresta do sol': 3,
        'irmandade das tavernas': 4,
        'os rasga-mortalhas': 5,
        'rasga-mortalhas': 5,
        'sociedade zaori': 6,
        'mercenarios independentes': 7,
    }

    class_map = {
        'barbaro': 1,
        'bardo': 2,
        'cacador': 3,
        'clerigo': 4,
        'druida': 5,
        'guerreiro': 6,
        'ladino': 7,
        'mago': 8,
        'paladino': 9,
    }

    status_map = {
        'ATIVO': 1,
        'INATIVO': 2,
        'MORTO': 3,
        'RASCUNHO': 2,
    }

    for personagem in Personagem.objects.all().iterator():
        old_status = getattr(personagem, 'status', None)
        old_ativo = bool(getattr(personagem, 'ativo', True))
        old_aprovado = bool(getattr(personagem, 'aprovado', False))

        new_status = status_map.get(old_status, 1 if old_ativo else 2)
        if old_status != 'MORTO' and not old_ativo:
            new_status = 2

        old_guilda = _normalize(getattr(personagem, 'guilda', ''))
        old_classe = _normalize(getattr(personagem, 'classe', ''))

        new_guilda = None
        new_classe = None

        if old_guilda.isdigit():
            guilda_candidate = int(old_guilda)
            if 1 <= guilda_candidate <= 7:
                new_guilda = guilda_candidate
        elif old_guilda:
            new_guilda = guild_map.get(old_guilda)

        if old_classe.isdigit():
            classe_candidate = int(old_classe)
            if 1 <= classe_candidate <= 9:
                new_classe = classe_candidate
        elif old_classe:
            new_classe = class_map.get(old_classe)

        personagem.status_novo = new_status
        personagem.status_aprovacao = 2 if old_aprovado else 1
        personagem.guilda_nova = new_guilda
        personagem.classe_nova = new_classe
        personagem.save(update_fields=['status_novo', 'status_aprovacao', 'guilda_nova', 'classe_nova'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('personagens', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='personagem',
            name='classe_nova',
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[
                    (1, 'Barbaro'),
                    (2, 'Bardo'),
                    (3, 'Cacador'),
                    (4, 'Clerigo'),
                    (5, 'Druida'),
                    (6, 'Guerreiro'),
                    (7, 'Ladino'),
                    (8, 'Mago'),
                    (9, 'Paladino'),
                ],
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='personagem',
            name='guilda_nova',
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[
                    (1, 'Artistas da Revolucao'),
                    (2, 'Circulo do Fogo'),
                    (3, 'Floresta do Sol'),
                    (4, 'Irmandade das Tavernas'),
                    (5, 'Os Rasga-Mortalhas'),
                    (6, 'Sociedade Zaori'),
                    (7, 'Mercenarios Independentes'),
                ],
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='personagem',
            name='status_aprovacao',
            field=models.PositiveSmallIntegerField(
                choices=[(1, 'Pendente'), (2, 'Aprovado'), (3, 'Rejeitado')],
                default=1,
            ),
        ),
        migrations.AddField(
            model_name='personagem',
            name='status_novo',
            field=models.PositiveSmallIntegerField(
                choices=[(1, 'Ativo'), (2, 'Inativo'), (3, 'Morto'), (4, 'Aposentado')],
                default=1,
            ),
        ),
        migrations.RunPython(migrate_personagem_data, noop_reverse),
        migrations.RemoveField(
            model_name='personagem',
            name='aprovado',
        ),
        migrations.RemoveField(
            model_name='personagem',
            name='ativo',
        ),
        migrations.RemoveField(
            model_name='personagem',
            name='classe',
        ),
        migrations.RemoveField(
            model_name='personagem',
            name='guilda',
        ),
        migrations.RemoveField(
            model_name='personagem',
            name='status',
        ),
        migrations.RenameField(
            model_name='personagem',
            old_name='classe_nova',
            new_name='classe',
        ),
        migrations.RenameField(
            model_name='personagem',
            old_name='guilda_nova',
            new_name='guilda',
        ),
        migrations.RenameField(
            model_name='personagem',
            old_name='status_novo',
            new_name='status',
        ),
    ]
