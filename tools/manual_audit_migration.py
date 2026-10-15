"""Verifica a migração de saldos e compras antigas somente em SQLite em memória."""
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'codex'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'wiki.test_settings'
import django
django.setup()
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from core.models import Profile
from wiki.models import WikiEntry

assert connection.vendor == 'sqlite' and connection.settings_dict['NAME'] == ':memory:'
call_command('migrate', verbosity=0)
executor = MigrationExecutor(connection)
leaves = executor.loader.graph.leaf_nodes()
target = [('personagens', '0007_player_wallet_and_legacy_review')]
executor.migrate(target)
state = executor.loader.project_state(target).apps
OldCharacter = state.get_model('personagens', 'Personagem')
OldPurchase = state.get_model('personagens', 'CompraTalento')
owner = User.objects.create_user('migration-proof')
Profile.objects.create(user=owner, xp_disponivel=500)
records = [OldCharacter.objects.create(usuario_id=owner.pk,nome=f'Legado {amount}',slug=f'legado-{amount}',
              classe=6,guilda=2,ouro=amount) for amount in (0,7,2147483647)]
purchase = OldPurchase.objects.create(personagem_id=records[0].pk,talento='ARMADURA_ADICIONAL',
                custo_xp=25,status='approved',justificativa='Compra antiga.')
item = WikiEntry.objects.get(category='itens',slug='sangue-de-dragao')
item.data['descricao'] = 'Texto personalizado da comissão, preservado.'
item.save()
talent = WikiEntry.objects.get(category='talentos',slug='armadura-adicional')
talent.data['custo_xp'] = 60
talent.save()
executor = MigrationExecutor(connection)
executor.migrate(leaves)
from personagens.models import Personagem, CompraTalento
values = list(Personagem.objects.filter(pk__in=[item.pk for item in records]).order_by('pk').values_list('ouro',flat=True))
assert values == [Decimal('0.0'),Decimal('7.0'),Decimal('2147483647.0')], values
assert Profile.objects.get(user=owner).xp_disponivel == 500
current = CompraTalento.objects.get(pk=purchase.pk)
assert current.custo_xp == current.regra_snapshot['custo_xp'] == 25
item.refresh_from_db()
assert item.data['descricao'] == 'Texto personalizado da comissão, preservado.'
print(json.dumps({'gold_preserved':[str(value) for value in values], 'xp_preserved':True,
                  'historical_purchase_cost_preserved':True,'custom_content_preserved':True,
                  'database':'SQLite :memory:'},ensure_ascii=False))
