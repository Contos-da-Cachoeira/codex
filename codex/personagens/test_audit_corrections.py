"""Regressões dos casos confirmados na auditoria de 15/10/2026."""
from decimal import Decimal
from importlib import import_module
from types import SimpleNamespace
from datetime import timedelta

from django.apps import apps
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.forms import AccountPersonalDataForm
from core.forms import EventCharacterBalanceForm
from core.money import GoldField
from core.models import Profile, LarpEvento, LarpInscricao
from guildas.models import Guilda, GuildaMembro
from wiki.catalog import spells_by_class
from wiki.forms import WikiEntryForm
from wiki.models import WikiEntry
from .forms import CompraTalentoForm, PersonagemUpdateForm, PersonagemCreateForm
from .models import Personagem, CompraTalento, MovimentoXP
from .rules import approve_purchase, activate_purchases, validate_base, complete_multiclass


class AuditCorrectionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user('audit-player', email='audit@example.com')
        cls.admin = User.objects.create_user('audit-admin', is_staff=True)
        Profile.objects.create(user=cls.owner, xp_disponivel=3000)

    def character(self, classe=6, **kwargs):
        values = dict(usuario=self.owner, nome='Ficha de auditoria', classe=classe, guilda=1, status_aprovacao=2,
                      historia='História fictícia.', magias_pretendidas=spells_by_class().get(classe, [])[:{2:3,4:3,8:4}.get(classe,100)],
                      feitico_antigo='Petrificação' if classe == 8 else '', divindade='Wukong' if classe in {4,9} else '',
                      afinidade='Urso' if classe == 5 else '', forma_selvagem='Brutal, +2 PV, imunidade a desmembramento; fala rosnando.' if classe == 5 else '')
        return Personagem.objects.create(**(values | kwargs))

    def request_purchase(self, character, key, **kwargs):
        form = CompraTalentoForm({'talento':key, 'justificativa':'Treinamento durante várias sessões.', **kwargs}, character=character)
        self.assertTrue(form.is_valid(), form.errors)
        return form.save()

    def buy(self, character, key, **kwargs):
        purchase = self.request_purchase(character, key, **kwargs)
        approve_purchase(purchase.pk, self.admin)
        purchase.refresh_from_db()
        return purchase

    def multiclass(self, character, second=8, **kwargs):
        related = [self.buy(character, 'ARMADURA_ADICIONAL') for _ in range(2)]
        return self.request_purchase(character, 'MULTICLASSE', segunda_classe=second,
                                     talentos_relacionados=[p.pk for p in related], detalhes='Jornada interpretada.', **kwargs)

    def test_personal_data_cannot_restore_xp_spent_after_profile_load(self):
        character = self.character()
        stale = Profile.objects.get(user=self.owner)
        form = AccountPersonalDataForm({'username':self.owner.username, 'email':self.owner.email,
              'data_nascimento':'1995-01-01', 'possui_fobia_gatilho':'nao'}, instance=self.owner, profile=stale)
        self.assertTrue(form.is_valid(), form.errors)
        purchase = self.buy(character, 'ARMADURA_ADICIONAL')
        form.save()
        self.assertEqual(Profile.objects.get(user=self.owner).xp_disponivel, 2975)
        self.assertEqual(MovimentoXP.objects.get(compra=purchase).valor, -25)

    def test_conjurar_and_previous_spell_remain_active_after_multiclass(self):
        character = self.character()
        conj = self.buy(character, 'CONJURAR', magia='Exorcismo', foco='Amuleto')
        activate_purchases(character.pk, [conj.pk])
        spell = self.buy(character, 'MAGIA_OUTRA_CLASSE', magia='Bola de Fogo')
        activate_purchases(character.pk, [conj.pk, spell.pk])
        multi = self.request_purchase(character, 'MULTICLASSE', segunda_classe=8, magia='Necromancia',
                    talentos_relacionados=[conj.pk, spell.pk], detalhes='Jornada arcana interpretada.')
        approve_purchase(multi.pk, self.admin)
        activate_purchases(character.pk, [conj.pk, spell.pk, multi.pk])
        self.assertEqual(set(character.magias_conhecidas), {'Exorcismo', 'Bola de Fogo'})
        self.assertEqual(character.capacidades_classes[0]['feitico'], 'Necromancia')
        self.assertEqual(character.classe, 6)
        self.assertNotIn('Cajado', character.capacidades_classes[0]['focos'])

    def test_foreign_magic_does_not_become_invalid_when_second_class_learns_it(self):
        character = self.character(2)
        spells = [self.buy(character, 'MAGIA_OUTRA_CLASSE', magia=name) for name in ('Bola de Fogo','Raio Elétrico')]
        multi = self.request_purchase(character, 'MULTICLASSE', segunda_classe=8, magia='Controle Mental',
                    talentos_relacionados=[p.pk for p in spells], detalhes='Jornada arcana interpretada.')
        approve_purchase(multi.pk, self.admin)
        activate_purchases(character.pk, [p.pk for p in spells] + [multi.pk])
        self.assertEqual(character.compras_talentos.filter(ativo=True).count(), 3)

    def test_multiclass_mage_requires_an_ancient_choice(self):
        character = self.character()
        form = CompraTalentoForm({'talento':'MULTICLASSE', 'segunda_classe':8, 'justificativa':'Treinamento'}, character=character)
        self.assertFalse(form.is_valid())
        multi = self.multiclass(character, magia='Necromancia')
        approve_purchase(multi.pk, self.admin)
        activate_purchases(character.pk, [multi.pk])
        self.client.force_login(self.owner)
        response = self.client.get(reverse('detalhe_personagem', args=[character.slug]))
        self.assertContains(response, 'Multiclasse: Mago')
        self.assertContains(response, 'Necromancia')

    def test_multiclass_druid_requires_commission_form_and_rolls_back_failure(self):
        character = self.character()
        multi = self.multiclass(character, second=5, afinidade='Urso')
        before = Profile.objects.get(user=self.owner).xp_disponivel
        with self.assertRaises(ValidationError):
            approve_purchase(multi.pk, self.admin)
        self.assertEqual(Profile.objects.get(user=self.owner).xp_disponivel, before)
        definition = 'Brutal, +2 PV, imunidade a desmembramento; não fala.'
        approve_purchase(multi.pk, self.admin, commission_details=definition)
        activate_purchases(character.pk, [multi.pk])
        self.assertEqual(character.capacidades_classes[0]['forma_selvagem'], definition)

    def test_multiclass_sacred_class_requires_divinity(self):
        character = self.character()
        multi = self.multiclass(character, second=9, divindade='Lunna')
        approve_purchase(multi.pk, self.admin)
        activate_purchases(character.pk, [multi.pk])
        self.assertEqual(character.capacidades_classes[0]['divindade'], 'Lunna')

    def test_old_multiclass_choices_can_be_completed_once_without_new_charge(self):
        character = self.character()
        purchase = CompraTalento.objects.create(personagem=character,talento='MULTICLASSE',segunda_classe=8,
            custo_xp=70,status='approved',detalhes='Jornada aprovada.',justificativa='Treinou ao longo de várias sessões.',aprovado_por=self.admin)
        before = Profile.objects.get(user=self.owner).xp_disponivel
        self.client.force_login(self.admin)
        url = reverse('talentos_personagem',args=[character.slug])
        self.assertContains(self.client.get(url),'Completar escolhas antigas')
        self.assertEqual(self.client.post(url,{'action':'complete_choices','purchase':purchase.pk,'magia':'Necromancia'}).status_code,302)
        self.assertEqual(Profile.objects.get(user=self.owner).xp_disponivel,before)
        self.assertFalse(MovimentoXP.objects.filter(compra=purchase).exists())
        purchase.refresh_from_db()
        self.assertEqual(purchase.magia,'Necromancia')
        self.assertIn('revisao_comissao',purchase.escolhas_classe)
        with self.assertRaises(ValidationError):
            complete_multiclass(purchase.pk,self.admin,{'magia':'Petrificação'})

    def test_old_choice_review_is_admin_only(self):
        character = self.character()
        purchase = CompraTalento.objects.create(personagem=character,talento='MULTICLASSE',segunda_classe=8,
            custo_xp=70,status='approved',detalhes='Jornada aprovada.',justificativa='Treinamento.')
        self.client.force_login(self.owner)
        url = reverse('talentos_personagem',args=[character.slug])
        self.assertEqual(self.client.post(url,{'action':'complete_choices','purchase':purchase.pk,'magia':'Necromancia'}).status_code,403)

    def test_defined_druid_form_is_readonly_for_admin_edit(self):
        character = self.character(5)
        original = character.forma_selvagem
        form = PersonagemUpdateForm({'nome':character.nome, 'historia':character.historia, 'guilda':1,
                  'forma_selvagem':'Voo e nenhum defeito.'}, instance=character, admin=True)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        character.refresh_from_db()
        self.assertEqual(character.forma_selvagem, original)
        self.assertEqual(character.status_aprovacao, 2)

    def test_repeated_approval_cannot_change_wild_form(self):
        character = self.character(5)
        purchase = self.buy(character, 'FORMA_SELVAGEM', detalhes='Forma original da comissão.')
        self.client.force_login(self.admin)
        response = self.client.post(reverse('talentos_personagem', args=[character.slug]),
                {'action':'approve','purchase':purchase.pk,'commission_details':'Outra forma sem custo.'})
        self.assertEqual(response.status_code, 200)
        purchase.refresh_from_db()
        self.assertEqual(purchase.detalhes, 'Forma original da comissão.')
        self.assertEqual(MovimentoXP.objects.filter(compra=purchase).count(), 1)

    def test_failed_approval_does_not_save_commission_changes(self):
        character = self.character(5)
        purchase = self.request_purchase(character, 'FORMA_SELVAGEM', detalhes='Afinidade sugerida pelo jogador.')
        Profile.objects.filter(user=self.owner).update(xp_disponivel=0)
        with self.assertRaises(ValidationError):
            approve_purchase(purchase.pk, self.admin, commission_details='Forma definida pela comissão.')
        purchase.refresh_from_db()
        self.assertEqual(purchase.detalhes, 'Afinidade sugerida pelo jogador.')
        self.assertEqual(purchase.status, 'pending')

    def test_gold_accepts_silver_units_and_rejects_other_fractions(self):
        for value in ('0.5','0,5','1.5','1.50','3.5','20'):
            form = EventCharacterBalanceForm({'xp':100, 'ouro':value})
            self.assertTrue(form.is_valid(), form.errors)
        for value in ('0.1','1.25','-0.5','NaN','Infinity','2147483648'):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                GoldField().clean(value)
        character = self.character(ouro=Decimal('0.5'))
        character.refresh_from_db()
        self.assertEqual(character.ouro, Decimal('0.5'))

    def test_weapon_focus_is_rejected_even_if_claimed_to_be_an_amulet(self):
        character = self.character()
        for focus in ('Espada', 'Espada-amuleto', 'Cajado', 'Lança', 'Escudo'):
            form = CompraTalentoForm({'talento':'CONJURAR','magia':'Exorcismo','foco':focus,
                        'tipo_foco':'amuleto','justificativa':'Treinamento'}, character=character)
            self.assertFalse(form.is_valid(), focus)

    def test_guild_rank_excludes_mercenaries_and_records_granted_guild(self):
        merc = self.character(guilda=7)
        form = CompraTalentoForm({'talento':'BENEFICIOS_DE_PATENTE','justificativa':'Participou de duas sessões.'}, character=merc)
        self.assertFalse(form.is_valid())
        character = self.character(guilda=2)
        for number in range(2):
            event = LarpEvento.objects.create(titulo=f'Passada {number}', local='Praça',
                data_evento=timezone.now()-timedelta(days=number+1), data_limite_inscricao=timezone.now()-timedelta(days=number+2))
            LarpInscricao.objects.create(evento=event,usuario=self.owner,personagem=character,presenca_confirmada=True,
                    nome_completo_jogador='Fictício',telefone='123',cpf='123')
        purchase = self.request_purchase(character,'BENEFICIOS_DE_PATENTE')
        with self.assertRaises(ValidationError):
            approve_purchase(purchase.pk,self.admin)
        approve_purchase(purchase.pk,self.admin,commission_details='Vantagens e obrigações decididas pelo mestre.')
        purchase.refresh_from_db()
        self.assertEqual(purchase.escolhas_classe['guilda'],2)
        activate_purchases(character.pk,[purchase.pk])
        character.guilda = 1
        character.save(update_fields=['guilda'])
        with self.assertRaises(ValidationError):
            activate_purchases(character.pk,[purchase.pk])

    def test_wiki_price_changes_apply_to_new_quotes_only(self):
        character = self.character()
        old = self.request_purchase(character,'ARMADURA_ADICIONAL')
        entry = WikiEntry.objects.get(category='talentos',slug='armadura-adicional')
        form = WikiEntryForm({'name':entry.name,'slug':entry.slug,'visible':'on','custo_xp':35,'stackavel':'on'},instance=entry,category='talentos')
        self.assertTrue(form.is_valid(),form.errors)
        form.save()
        new = self.request_purchase(character,'ARMADURA_ADICIONAL')
        self.assertEqual((old.custo_xp,new.custo_xp),(25,35))
        approve_purchase(old.pk,self.admin)
        approve_purchase(new.pk,self.admin)
        self.assertEqual(Profile.objects.get(user=self.owner).xp_disponivel,2940)

    def test_hide_or_delete_preserves_acquired_talent_but_blocks_new_requests(self):
        character = self.character()
        purchase = self.buy(character,'ARMADURA_ADICIONAL')
        entry = WikiEntry.objects.get(category='talentos',slug='armadura-adicional')
        entry.visible = False
        entry.save()
        form = CompraTalentoForm({'talento':'ARMADURA_ADICIONAL','justificativa':'Treino'},character=character)
        self.assertFalse(form.is_valid())
        entry.delete()
        activate_purchases(character.pk,[purchase.pk])
        self.assertEqual(purchase.nome,'Armadura adicional')

    def test_wiki_repeatability_controls_new_purchases(self):
        character = self.character()
        self.buy(character,'ARMADURA_ADICIONAL')
        entry = WikiEntry.objects.get(category='talentos',slug='armadura-adicional')
        entry.data['stackavel'] = False
        entry.save()
        form = CompraTalentoForm({'talento':'ARMADURA_ADICIONAL','justificativa':'Treino'},character=character)
        self.assertFalse(form.is_valid())

    def test_new_published_wiki_talent_can_be_requested(self):
        character = self.character()
        entry = WikiEntry.objects.create(category='talentos',slug='dom-da-comissao',name='Dom da comissão',visible=True,
                    data={'custo_xp':15,'descricao':'Efeito personalizado decidido pela comissão.'})
        purchase = self.buy(character,f'WIKI_{entry.pk}')
        self.assertEqual((purchase.nome,purchase.custo_xp),('Dom da comissão',15))

    def test_spell_who_uses_changes_creation_choices(self):
        entry = WikiEntry.objects.get(category='magias',slug='bola-de-fogo')
        entry.data['quem_usa'].append('Bardo')
        entry.save()
        self.assertIn('Bola de Fogo',spells_by_class()[2])
        form = PersonagemCreateForm({'nome':'Bardo','descricao_personagem':'História','guilda':1,'classe':2,
                'magias_pretendidas':['Bola de Fogo','Silenciar','Lentidão'],'ciencia_concordancia':True},user=self.owner)
        self.assertTrue(form.is_valid(),form.errors)

    def test_catalog_refreshes_between_requests_and_reuses_queries_within_one(self):
        from wiki.catalog import talent_catalog
        from wiki.catalog_cache import CatalogMiddleware
        from django.test import RequestFactory
        from django.http import HttpResponse
        seen = []
        def view(request):
            with self.assertNumQueries(1):
                seen.append(talent_catalog()['ARMADURA_ADICIONAL']['custo_xp'])
                talent_catalog()
                talent_catalog()
            return HttpResponse('ok')
        handler = CatalogMiddleware(view)
        handler(RequestFactory().get('/'))
        entry = WikiEntry.objects.get(category='talentos',slug='armadura-adicional')
        entry.data['custo_xp'] = 45
        entry.save()
        handler(RequestFactory().get('/'))
        self.assertEqual(seen,[25,45])

    def test_learned_spell_cannot_be_silently_renamed(self):
        self.character(8)
        entry = WikiEntry.objects.get(category='magias',slug='bola-de-fogo')
        # Garante que a magia consta na ficha, independentemente da ordenação.
        character = self.character(8,magias_pretendidas=['Bola de Fogo','Lentidão','Silenciar','Exorcismo'])
        form = WikiEntryForm({'name':'Chama diferente','slug':entry.slug,'quem_usa':'Mago'},instance=entry,category='magias')
        self.assertFalse(form.is_valid())
        self.assertIn('name',form.errors)

    def test_sacred_classes_reject_explicit_atheism_and_allow_commission_choice(self):
        for classe in (4,9):
            character = self.character(classe)
            character.divindade = 'Nenhuma; sou ateu'
            with self.assertRaises(ValidationError):
                validate_base(character,require_commission=True)
            character.divindade = 'Entidade local sob avaliação'
            validate_base(character,require_commission=True)

    def test_six_guild_records_exist_and_mercenaries_have_no_shared_private_area(self):
        self.assertEqual(set(Guilda.objects.values_list('pk',flat=True)),set(range(1,7)))
        character = self.character(guilda=2)
        self.assertTrue(GuildaMembro.objects.filter(guilda_id=2,usuario=self.owner).exists())
        self.client.force_login(self.owner)
        response = self.client.get('/guildas/mercenarios-independentes/')
        self.assertEqual(response.status_code,200)
        self.assertNotContains(response,'Notícias internas')

    def test_content_corrections_and_scenario_are_published(self):
        response = self.client.get('/wiki/itens/sangue-de-dragao/')
        self.assertContains(response,'Apenas Água Primordial')
        self.assertContains(response,'máximo de 10 PV')
        self.assertContains(self.client.get('/wiki/classes/druida/'),'cristais')
        self.assertContains(self.client.get('/wiki/cenario/'),'Contos da Cachoeira')
        self.assertContains(self.client.get('/wiki/cenario/zona-neutra-e-pactos/'),'divergência')
