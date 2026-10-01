from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse

from core.models import ImageAsset, Profile
from .forms import PersonagemCreateForm, PersonagemUpdateForm
from .models import Personagem


class CharacterPhotoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user('owner', first_name='Alice')
        cls.other = User.objects.create_user('other')
        cls.image = ImageAsset.objects.create(owner=cls.owner, url='https://example.com/portrait.png')
        cls.foreign_image = ImageAsset.objects.create(owner=cls.other, url='https://example.com/other.png')
        cls.character = Personagem.objects.create(usuario=cls.owner, nome='Aria', image_asset=cls.image)

    def create_form(self, image):
        return PersonagemCreateForm({
            'nome': 'Nova', 'descricao_personagem': 'Uma aventureira',
            'guilda': '1', 'classe': '6', 'ciencia_concordancia': 'on',
            'image_asset': image,
        }, user=self.owner)

    def test_create_with_photo_and_without_photo(self):
        for value in (self.image.pk, ''):
            with self.subTest(value=value):
                form = self.create_form(value)
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.save().image_asset_id, value or None)

    def test_foreign_photo_rejected_on_create_and_edit(self):
        create = self.create_form(self.foreign_image.pk)
        edit = PersonagemUpdateForm({'nome': 'Aria', 'image_asset': self.foreign_image.pk}, instance=self.character)
        for form in (create, edit):
            self.assertFalse(form.is_valid())
            self.assertIn('image_asset', form.errors)

    def test_edit_photo_and_remove_without_deleting_asset(self):
        for value in ('', self.image.pk):
            form = PersonagemUpdateForm({'nome': 'Aria', 'image_asset': value}, instance=self.character)
            self.assertTrue(form.is_valid(), form.errors)
            character = form.save()
            self.assertEqual(character.image_asset_id, value or None)
        self.assertTrue(ImageAsset.objects.filter(pk=self.image.pk).exists())

    def test_character_pages_render_photo_and_picker(self):
        self.client.force_login(self.owner)
        for name in ('detalhe_personagem', 'editar_personagem'):
            response = self.client.get(reverse(name, kwargs={'slug': self.character.slug}))
            self.assertContains(response, self.image.url)
        self.assertContains(self.client.get(reverse('criar_personagem')), 'data-profile-image-picker')
        self.assertContains(self.client.get(reverse('meus_personagens')), self.image.url)

    def test_another_user_cannot_edit_character(self):
        self.client.force_login(self.other)
        response = self.client.post(reverse('editar_personagem', kwargs={'slug': self.character.slug}), {'nome': 'Changed'})
        self.assertEqual(response.status_code, 404)
        self.character.refresh_from_db()
        self.assertEqual(self.character.nome, 'Aria')

    def test_user_avatar_profile_photo_and_initial(self):
        template = 'core/includes/user_avatar.html'
        profile, _ = Profile.objects.get_or_create(user=self.owner)
        profile.nome_completo_jogador = 'Beatriz'
        profile.save()
        self.owner.refresh_from_db()
        self.assertIn('>B</span>', render_to_string(template, {'avatar_user': self.owner}))
        profile.image_asset = self.image
        profile.save()
        self.owner.refresh_from_db()
        self.assertIn(self.image.url, render_to_string(template, {'avatar_user': self.owner}))
        self.assertIn('>O</span>', render_to_string(template, {'avatar_user': self.other}))
