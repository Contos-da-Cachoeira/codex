import json
from pathlib import Path

from django.db import migrations


def seed_wiki(apps, schema_editor):
    Entry = apps.get_model('wiki', 'WikiEntry')
    entries = json.loads(Path(__file__).with_name('initial_content.json').read_text(encoding='utf-8'))
    Entry.objects.using(schema_editor.connection.alias).bulk_create([Entry(**entry) for entry in entries])


class Migration(migrations.Migration):
    dependencies = [('wiki', '0001_initial')]
    operations = [migrations.RunPython(seed_wiki, migrations.RunPython.noop)]
