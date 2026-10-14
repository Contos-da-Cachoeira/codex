from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='WikiEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('regras', 'Regras'), ('classes', 'Classes'), ('talentos', 'Talentos'), ('magias', 'Magias'), ('itens', 'Itens'), ('magia_geral', 'Regras gerais de magia')], max_length=20, verbose_name='Seção')),
                ('slug', models.SlugField(max_length=160)),
                ('name', models.CharField(max_length=200, verbose_name='Nome')),
                ('data', models.JSONField(default=dict)),
                ('image', models.ImageField(blank=True, upload_to='wiki/', verbose_name='Imagem')),
                ('visible', models.BooleanField(default=False, verbose_name='Visível para os jogadores')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['category', 'name'], 'constraints': [models.UniqueConstraint(fields=('category', 'slug'), name='wiki_category_slug_unique')]},
        ),
    ]
