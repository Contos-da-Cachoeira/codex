from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0009_sitelayoutconfig_blue_palette'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='profiles/avatars/', verbose_name='Foto de perfil'),
        ),
    ]
