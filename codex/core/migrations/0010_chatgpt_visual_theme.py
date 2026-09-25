from django.db import migrations, models
from django.core.validators import RegexValidator


def apply_chatgpt_palette(apps, schema_editor):
    SiteLayoutConfig = apps.get_model('core', 'SiteLayoutConfig')
    SiteLayoutConfig.objects.filter(primary_color__in=['#111111', '#1B74B9']).update(primary_color='#3A83F7')
    SiteLayoutConfig.objects.filter(secondary_color__in=['#E5E5E5', '#0E2E52']).update(secondary_color='#303030')
    SiteLayoutConfig.objects.filter(secondary_content_color='#111111').update(secondary_content_color='#EDEDED')
    SiteLayoutConfig.objects.filter(site_background_color='#061426').update(site_background_color='#000000')
    SiteLayoutConfig.objects.filter(site_surface_color='#0D2845').update(site_surface_color='#212121')
    SiteLayoutConfig.objects.filter(site_accent_color='#4FD7FF').update(site_accent_color='#3A83F7')
    SiteLayoutConfig.objects.filter(site_accent_content_color='#041422').update(site_accent_content_color='#FFFFFF')
    SiteLayoutConfig.objects.filter(site_text_color='#F2F7FF').update(site_text_color='#EDEDED')
    SiteLayoutConfig.objects.filter(site_muted_text_color='#A9C1D8').update(site_muted_text_color='#AFAFAF')


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0009_sitelayoutconfig_blue_palette'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitelayoutconfig',
            name='primary_color',
            field=models.CharField(default='#3A83F7', max_length=7, validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Cor principal'),
        ),
        migrations.AlterField(
            model_name='sitelayoutconfig',
            name='secondary_color',
            field=models.CharField(default='#303030', max_length=7, validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Cor secundaria'),
        ),
        migrations.AlterField(
            model_name='sitelayoutconfig',
            name='secondary_content_color',
            field=models.CharField(default='#EDEDED', max_length=7, validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Conteudo da cor secundaria'),
        ),
        migrations.AlterField(
            model_name='sitelayoutconfig',
            name='site_background_color',
            field=models.CharField(default='#000000', max_length=7, validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Fundo principal'),
        ),
        migrations.AlterField(
            model_name='sitelayoutconfig',
            name='site_surface_color',
            field=models.CharField(default='#212121', max_length=7, validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Superficie principal'),
        ),
        migrations.AlterField(
            model_name='sitelayoutconfig',
            name='site_accent_color',
            field=models.CharField(default='#3A83F7', max_length=7, validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Azul de destaque'),
        ),
        migrations.AlterField(
            model_name='sitelayoutconfig',
            name='site_accent_content_color',
            field=models.CharField(default='#FFFFFF', max_length=7, validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Texto do destaque'),
        ),
        migrations.AlterField(
            model_name='sitelayoutconfig',
            name='site_text_color',
            field=models.CharField(default='#EDEDED', max_length=7, validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Texto principal'),
        ),
        migrations.AlterField(
            model_name='sitelayoutconfig',
            name='site_muted_text_color',
            field=models.CharField(default='#AFAFAF', max_length=7, validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Texto secundario'),
        ),
        migrations.RunPython(apply_chatgpt_palette, migrations.RunPython.noop),
    ]
