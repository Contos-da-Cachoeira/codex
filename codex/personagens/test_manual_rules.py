from datetime import timedelta
from importlib import import_module
import json
from types import SimpleNamespace

from django.apps import apps
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Profile, LarpEvento, LarpInscricao, ImageAsset
from .consts import MAGIAS_POR_CLASSE
from .forms import PersonagemCreateForm, PersonagemUpdateForm, CompraTalentoForm
from .models import Personagem, CompraTalento, MovimentoXP
from .rules import activate_purchases, approve_purchase, set_player_xp, validate_talent


class ManualRulesTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('jogador')
        self.admin = User.objects.create_user('comissao', is_staff=True)
        Profile.objects.create(user=self.owner, xp_disponivel=300)
        self.character = Personagem.objects.create(usuario=self.owner, nome='Guerreiro', classe=6, guilda=1)

    def create_form(self, classe, spells=(), **extra):
        return PersonagemCreateForm(dict(nome='Novo', descricao_personagem='Uma história', guilda=1, classe=classe,
            magias_pretendidas=list(spells), ciencia_concordancia=True, **extra), user=self.owner)

    def purchase(self, key='ARMADURA_ADICIONAL', character=None, **extra):
        from wiki.constants.talentos import TALENTOS_WIKI
        return CompraTalento.objects.create(personagem=character or self.character, talento=key,
            custo_xp=TALENTOS_WIKI[key]['custo_xp'], justificativa='Treinamento durante a jornada.', **extra)

    def test_exact_initial_spell_counts(self):
        for classe, count in ((2, 3), (4, 3), (8, 4)):
            available = MAGIAS_POR_CLASSE[classe]
            for selected in (available[:1], available[:count], available):
                with self.subTest(classe=classe, selected=selected):
                    form = self.create_form(classe, selected, divindade='Wukong', feitico_antigo='Petrificação')
                    self.assertEqual(form.is_valid(), len(selected) == count, form.errors)

    def test_fixed_spells_and_special_class_choices(self):
        for classe, extra in ((5, {'afinidade':'Lobo'}), (9, {'divindade':'Wukong'})):
            form = self.create_form(classe, **extra)
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.save().magias_pretendidas, MAGIAS_POR_CLASSE[classe])
        for classe, spells in ((8, MAGIAS_POR_CLASSE[8][:4]), (4, MAGIAS_POR_CLASSE[4][:3]), (5, [])):
            self.assertFalse(self.create_form(classe, spells).is_valid())

    def test_no_free_talents_and_no_injected_spells(self):
        self.assertFalse(self.create_form(6, talentos_iniciais=['Armadura adicional']).is_valid())
        self.assertFalse(self.create_form(6, ['Bola de Fogo']).is_valid())
        form = CompraTalentoForm({'talento':'ARMADURA_ADICIONAL', 'magia':'Bola de Fogo', 'justificativa':'Treino'}, character=self.character)
        self.assertFalse(form.is_valid())

    def test_creation_talents_are_pending_and_do_not_spend_xp(self):
        requests = [{'talento':'ARMADURA_ADICIONAL', 'justificativa':'Treinou com armadura.', 'custo_xp':0, 'status':'approved', 'ativo':True}] * 2
        form = self.create_form(6, talent_requests=json.dumps(requests))
        self.assertTrue(form.is_valid(), form.errors)
        character = form.save()
        self.assertEqual(character.compras_talentos.count(), 2)
        self.assertEqual(list(character.compras_talentos.values_list('custo_xp', 'status', 'ativo')), [(25,'pending',False)] * 2)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.profile.xp_disponivel, 300)
        self.assertFalse(MovimentoXP.objects.exists())

    def test_creation_talents_validate_balance_limit_and_prerequisites(self):
        item = {'talento':'ARMADURA_ADICIONAL', 'justificativa':'Treinou com armadura.'}
        cases = [[item] * 6, [{'talento':'FEITICO_ANTIGO', 'magia':'Necromancia', 'justificativa':'Treino'}],
                 [{'talento':'ALQUIMISTA', 'justificativa':'Estudou poções.'}] * 2, {'talento':'ALQUIMISTA'}]
        for requests in cases:
            with self.subTest(requests=requests):
                form = self.create_form(6, talent_requests=json.dumps(requests))
                self.assertFalse(form.is_valid())
                self.assertIn('talent_requests', form.errors)
        Profile.objects.filter(user=self.owner).update(xp_disponivel=20)
        self.owner.refresh_from_db()
        form = self.create_form(6, talent_requests=json.dumps([item]))
        self.assertFalse(form.is_valid())
        self.assertIn('saldo', str(form.errors))
        self.assertEqual(CompraTalento.objects.count(), 0)

    def test_creation_extra_spell_is_linked_to_request(self):
        spells = MAGIAS_POR_CLASSE[2]
        request = {'talento':'MAGIA_EXTRA_CLASSE', 'magia':spells[3], 'justificativa':'Estudou uma nova canção.'}
        form = self.create_form(2, spells[:3], talent_requests=json.dumps([request]))
        self.assertTrue(form.is_valid(), form.errors)
        character = form.save()
        self.assertEqual(character.magias_pretendidas, spells[:3])
        self.assertEqual(character.compras_talentos.get().magia, spells[3])
        duplicate = self.create_form(2, spells[:3], talent_requests=json.dumps([request, request]))
        self.assertFalse(duplicate.is_valid())

    def test_same_player_wallet_spent_once_across_characters(self):
        other = Personagem.objects.create(usuario=self.owner, nome='Outra', classe=1, guilda=1)
        first, second = self.purchase(), self.purchase(character=other)
        approve_purchase(first.pk, self.admin)
        approve_purchase(second.pk, self.admin)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.profile.xp_disponivel, 250)
        self.assertEqual(MovimentoXP.objects.filter(compra__isnull=False).count(), 2)
        with self.assertRaises(ValidationError):
            approve_purchase(first.pk, self.admin)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.profile.xp_disponivel, 250)
        self.assertEqual(first.personagem_id, self.character.pk)

    def test_insufficient_balance_leaves_everything_unchanged(self):
        set_player_xp(self.owner, 10, self.admin, 'Teste')
        purchase = self.purchase()
        with self.assertRaises(ValidationError):
            approve_purchase(purchase.pk, self.admin)
        purchase.refresh_from_db()
        self.assertEqual(purchase.status, 'pending')
        self.assertFalse(MovimentoXP.objects.filter(compra=purchase).exists())

    def test_repeated_purchases_each_count_as_one_of_five_slots(self):
        purchases = [self.purchase() for _ in range(6)]
        for purchase in purchases:
            approve_purchase(purchase.pk, self.admin)
        activate_purchases(self.character.pk, [p.pk for p in purchases[:2]])
        self.assertEqual(self.character.compras_talentos.filter(ativo=True).count(), 2)
        activate_purchases(self.character.pk, [p.pk for p in purchases[:5]])
        with self.assertRaises(ValidationError):
            activate_purchases(self.character.pk, [p.pk for p in purchases])
        self.assertEqual(self.character.compras_talentos.filter(ativo=True).count(), 5)
        activate_purchases(self.character.pk, [purchases[-1].pk])
        self.assertEqual(self.character.compras_talentos.filter(status='approved').count(), 6)

    def test_cannot_activate_foreign_character_purchase(self):
        other = Personagem.objects.create(usuario=self.owner, nome='Outra', classe=1)
        purchase = self.purchase(character=other, status='approved')
        with self.assertRaises(ValidationError):
            activate_purchases(self.character.pk, [purchase.pk])

    def test_weapon_chain_and_conditional_guild_benefit(self):
        mage = Personagem.objects.create(usuario=self.owner, nome='Mago', classe=8, guilda=2,
            magias_pretendidas=MAGIAS_POR_CLASSE[8][:4], feitico_antigo='Necromancia')
        medium = self.purchase('ARMAS_MEDIAS', character=mage)
        with self.assertRaises(ValidationError):
            validate_talent(mage, medium)
        short = self.purchase('ARMAS_CURTAS', character=mage)
        approve_purchase(short.pk, self.admin)
        activate_purchases(mage.pk, [short.pk])
        approve_purchase(medium.pk, self.admin)
        activate_purchases(mage.pk, [short.pk, medium.pk])
        with self.assertRaises(ValidationError):
            activate_purchases(mage.pk, [medium.pk])

    def test_class_specific_and_capability_prerequisites(self):
        for key in ('ARREMESSO_EXTRA','FLECHAS_ADICIONAIS','ESFERAS_ADICIONAIS','FEITICO_ANTIGO','FORMA_SELVAGEM','USAR_ESFERAS','MAGIA_OUTRA_CLASSE'):
            with self.subTest(talent=key), self.assertRaises(ValidationError):
                validate_talent(self.character, self.purchase(key))
        cleric = Personagem.objects.create(usuario=self.owner, nome='Clérigo', classe=4, divindade='Wukong', magias_pretendidas=MAGIAS_POR_CLASSE[4][:3])
        with self.assertRaises(ValidationError):
            validate_talent(cleric, self.purchase('USO_EXTRA', character=cleric))

    def test_conjurar_and_foreign_magic_are_separate_paid_choices(self):
        conjurar = self.purchase('CONJURAR', magia='Exorcismo', foco='Amuleto')
        approve_purchase(conjurar.pk, self.admin)
        activate_purchases(self.character.pk, [conjurar.pk])
        spell = self.purchase('MAGIA_OUTRA_CLASSE', magia='Bola de Fogo')
        approve_purchase(spell.pk, self.admin)
        activate_purchases(self.character.pk, [conjurar.pk, spell.pk])
        self.assertEqual(self.character.magias_pretendidas, [])
        self.assertEqual(set(self.character.magias_conhecidas), {'Exorcismo','Bola de Fogo'})
        staff = self.purchase('USAR_CAJADO')
        validate_talent(self.character, staff)  # Exorcismo é uma magia de toque.
        with self.assertRaises(ValidationError):
            validate_talent(self.character, self.purchase('MAGIA_EXTRA_CLASSE', magia='Bola de Fogo'))

    def test_extra_class_spell_does_not_change_initial_selection(self):
        bard = Personagem.objects.create(usuario=self.owner, nome='Bardo', classe=2, magias_pretendidas=MAGIAS_POR_CLASSE[2][:3])
        purchase = self.purchase('MAGIA_EXTRA_CLASSE', character=bard, magia=MAGIAS_POR_CLASSE[2][3])
        approve_purchase(purchase.pk, self.admin)
        activate_purchases(bard.pk, [purchase.pk])
        self.assertEqual(len(bard.magias_pretendidas), 3)
        self.assertEqual(len(bard.magias_conhecidas), 4)

    def test_multiclass_records_two_prior_purchases_without_weapon_grants(self):
        purchases = [self.purchase(status='approved'), self.purchase(status='approved')]
        multi = self.purchase('MULTICLASSE', segunda_classe=8, magia='Necromancia', talentos_relacionados=[p.pk for p in purchases], detalhes='Jornada descrita para avaliação da comissão.')
        approve_purchase(multi.pk, self.admin)
        activate_purchases(self.character.pk, [multi.pk])
        self.assertEqual(self.character.classe, 6)
        self.assertEqual(self.character.magias_conhecidas, [])
        incomplete = self.purchase('MULTICLASSE', segunda_classe=8, talentos_relacionados=[purchases[0].pk])
        with self.assertRaises(ValidationError):
            validate_talent(self.character, incomplete)

    def test_patent_requires_confirmed_past_attendance(self):
        purchase = self.purchase('BENEFICIOS_DE_PATENTE')
        for i in range(2):
            event = LarpEvento.objects.create(titulo=f'Sessão {i}', local='Praça', data_evento=timezone.now()-timedelta(days=i+1), data_limite_inscricao=timezone.now()-timedelta(days=i+2))
            LarpInscricao.objects.create(evento=event, usuario=self.owner, personagem=self.character, nome_completo_jogador='Jogador', telefone='123', cpf='123')
        with self.assertRaises(ValidationError):
            validate_talent(self.character, purchase)
        self.character.inscricoes_larp.update(presenca_confirmada=True)
        validate_talent(self.character, purchase)

    def test_owner_cannot_change_class_or_spells_through_edit(self):
        bard = Personagem.objects.create(usuario=self.owner, nome='Bardo', classe=2, guilda=1, magias_pretendidas=MAGIAS_POR_CLASSE[2][:3], status_aprovacao=2)
        form = PersonagemUpdateForm({'nome':'Bardo','classe':6,'guilda':1,'magias_pretendidas':['Bola de Fogo']}, instance=bard)
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        self.assertEqual(saved.classe, 2)
        self.assertEqual(saved.magias_pretendidas, MAGIAS_POR_CLASSE[2][:3])

    def test_portrait_modes_validate_owned_photo(self):
        photo = ImageAsset.objects.create(owner=self.owner, url='https://example.com/portrait.png')
        for mode in ('name','class','photo'):
            form = self.create_form(6, portrait_mode=mode, image_asset=photo.pk if mode == 'photo' else '')
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.save().portrait_mode, mode)
        self.assertFalse(self.create_form(6, portrait_mode='photo').is_valid())

    def test_pending_talent_approval_is_admin_only_and_csrf_protected(self):
        self.client.force_login(self.owner)
        purchase = self.purchase()
        url = reverse('talentos_personagem', args=[self.character.slug])
        self.assertEqual(self.client.post(url, {'action':'approve','purchase':purchase.pk}).status_code, 403)
        self.assertContains(self.client.get(url), 'Duas compras de Armadura adicional ocupam duas vagas.')
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(url, {'action':'approve','purchase':purchase.pk}).status_code, 302)
        purchase.refresh_from_db()
        self.assertEqual(purchase.status, 'approved')

    def test_stale_admin_balance_cannot_restore_spent_xp(self):
        purchase = self.purchase()
        approve_purchase(purchase.pk, self.admin)
        with self.assertRaises(ValidationError):
            set_player_xp(self.owner, 350, self.admin, 'Ajuste', expected=300)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.profile.xp_disponivel, 275)

    def test_data_migration_preserves_old_balances_and_flags_review(self):
        self.character.xp_atual = 35
        self.character.talentos_iniciais = ['Armadura adicional']
        self.character.save()
        other = Personagem.objects.create(usuario=self.owner, nome='Legado', classe=2, xp_atual=40, magias_pretendidas=MAGIAS_POR_CLASSE[2])
        Profile.objects.filter(user=self.owner).update(xp_disponivel=0)
        migrate = import_module('personagens.migrations.0007_player_wallet_and_legacy_review').consolidate
        migrate(apps, SimpleNamespace(connection=connection))
        self.owner.refresh_from_db()
        self.character.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(self.owner.profile.xp_disponivel, 75)
        self.assertEqual(self.character.xp_atual, 35)
        self.assertEqual(self.character.talentos_iniciais, ['Armadura adicional'])
        self.assertTrue(self.character.revisao_manual)
        self.assertEqual(other.magias_pretendidas, MAGIAS_POR_CLASSE[2])
        self.assertEqual(CompraTalento.objects.count(), 0)
