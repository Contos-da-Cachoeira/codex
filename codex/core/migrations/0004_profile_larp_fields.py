from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_homedynamicsection'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='apelido_cla',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='profile',
            name='cpf',
            field=models.CharField(blank=True, max_length=14),
        ),
        migrations.AddField(
            model_name='profile',
            name='fobia_gatilho',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='nome_completo_jogador',
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name='profile',
            name='telefone',
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
