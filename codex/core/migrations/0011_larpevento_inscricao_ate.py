from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_larpinscricao_dinheiro_pego_larp'),
    ]

    operations = [
        migrations.AddField(
            model_name='larpevento',
            name='inscricao_ate',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Inscricoes abertas ate'),
        ),
    ]
