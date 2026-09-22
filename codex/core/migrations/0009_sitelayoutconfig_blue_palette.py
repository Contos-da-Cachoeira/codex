from django.db import migrations, models
from django.core.validators import RegexValidator


def apply_blue_defaults(apps, schema_editor):
    SiteLayoutConfig = apps.get_model('core', 'SiteLayoutConfig')
    SiteLayoutConfig.objects.filter(primary_color='#111111').update(primary_color='#1B74B9')
    SiteLayoutConfig.objects.filter(primary_content_color='#FFFFFF').update(primary_content_color='#FFFFFF')
    SiteLayoutConfig.objects.filter(secondary_color='#E5E5E5').update(secondary_color='#0E2E52')
    SiteLayoutConfig.objects.filter(secondary_content_color='#111111').update(secondary_content_color='#FFFFFF')


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0008_sitelayoutconfig_social_links'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitelayoutconfig',
            name='site_background_color',
            field=models.CharField(default='#061426', max_length=7, validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Fundo azul escuro'),
        ),
        migrations.AddField(
            model_name='sitelayoutconfig',
            name='site_surface_color',
            field=models.CharField(default='#0D2845', max_length=7, validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Superficie azul'),
        ),
        migrations.AddField(
            model_name='sitelayoutconfig',
            name='site_accent_color',
            field=models.CharField(default='#4FD7FF', max_length=7, validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Azul de destaque'),
        ),
        migrations.AddField(
            model_name='sitelayoutconfig',
            name='site_accent_content_color',
            field=models.CharField(default='#041422', max_length=7, validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Texto do destaque'),
        ),
        migrations.AddField(
            model_name='sitelayoutconfig',
            name='site_text_color',
            field=models.CharField(default='#F2F7FF', max_length=7, validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Texto claro'),
        ),
        migrations.AddField(
            model_name='sitelayoutconfig',
            name='site_muted_text_color',
            field=models.CharField(default='#A9C1D8', max_length=7, validators=[RegexValidator(message='Use uma cor hexadecimal no formato #RRGGBB.', regex='^#[0-9A-Fa-f]{6}$')], verbose_name='Texto secundario'),
        ),
        migrations.RunPython(apply_blue_defaults, migrations.RunPython.noop),
    ]
