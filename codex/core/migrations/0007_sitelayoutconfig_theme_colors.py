from django.core.validators import RegexValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_larpinscricao_taxa_paga'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitelayoutconfig',
            name='primary_color',
            field=models.CharField(
                default='#111111',
                max_length=7,
                validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')],
                verbose_name='Cor principal',
            ),
        ),
        migrations.AddField(
            model_name='sitelayoutconfig',
            name='primary_content_color',
            field=models.CharField(
                default='#FFFFFF',
                max_length=7,
                validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')],
                verbose_name='Conteudo da cor principal',
            ),
        ),
        migrations.AddField(
            model_name='sitelayoutconfig',
            name='secondary_color',
            field=models.CharField(
                default='#E5E5E5',
                max_length=7,
                validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')],
                verbose_name='Cor secundaria',
            ),
        ),
        migrations.AddField(
            model_name='sitelayoutconfig',
            name='secondary_content_color',
            field=models.CharField(
                default='#111111',
                max_length=7,
                validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')],
                verbose_name='Conteudo da cor secundaria',
            ),
        ),
    ]
