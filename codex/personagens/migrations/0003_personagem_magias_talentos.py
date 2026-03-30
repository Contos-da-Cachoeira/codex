from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personagens', '0002_personagem_constantes'),
    ]

    operations = [
        migrations.AddField(
            model_name='personagem',
            name='magias_pretendidas',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='personagem',
            name='talentos_iniciais',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
