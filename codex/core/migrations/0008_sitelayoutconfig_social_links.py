from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_sitelayoutconfig_theme_colors'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitelayoutconfig',
            name='social_instagram_url',
            field=models.URLField(blank=True, default='', verbose_name='URL do Instagram'),
        ),
        migrations.AddField(
            model_name='sitelayoutconfig',
            name='social_whatsapp_url',
            field=models.URLField(blank=True, default='', verbose_name='URL do WhatsApp'),
        ),
        migrations.AddField(
            model_name='sitelayoutconfig',
            name='social_x_url',
            field=models.URLField(blank=True, default='', verbose_name='URL do X/Twitter'),
        ),
        migrations.AddField(
            model_name='sitelayoutconfig',
            name='social_youtube_url',
            field=models.URLField(blank=True, default='', verbose_name='URL do YouTube'),
        ),
    ]
