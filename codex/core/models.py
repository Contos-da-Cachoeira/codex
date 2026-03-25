from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
	class UserRole(models.TextChoices):
		ADMIN = 'ADMIN', 'Admin'
		COMMON = 'COMMON', 'Usuario comum'

	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	role = models.CharField(max_length=10, choices=UserRole.choices, default=UserRole.COMMON)

	def __str__(self):
		return f'{self.user.username} ({self.get_role_display()})'


class SingletonBaseModel(models.Model):
	"""Base for models that must keep a single database row."""

	class Meta:
		abstract = True

	def save(self, *args, **kwargs):
		self.pk = 1
		super().save(*args, **kwargs)

	@classmethod
	def load(cls):
		obj, _ = cls.objects.get_or_create(pk=1)
		return obj


class SiteLayoutConfig(SingletonBaseModel):
	header_visible = models.BooleanField(default=True, verbose_name='Mostrar cabecalho')
	header_title = models.CharField(max_length=120, default='Codex', verbose_name='Titulo do cabecalho')

	footer_visible = models.BooleanField(default=True, verbose_name='Mostrar rodape')
	footer_title = models.CharField(max_length=120, default='Codex da Cachoeira', verbose_name='Titulo do rodape')
	footer_description = models.CharField(
		max_length=220,
		default='Plataforma com login, registro e perfis de acesso.',
		verbose_name='Descricao do rodape',
	)
	footer_copyright = models.CharField(
		max_length=160,
		default='© 2026 - Todos os direitos reservados.',
		verbose_name='Linha de copyright',
	)

	class Meta:
		verbose_name = 'Layout padrao do site'
		verbose_name_plural = 'Layout padrao do site'

	def __str__(self):
		return 'Layout padrao do site'


class HomePageConfig(SingletonBaseModel):
	banner_visible = models.BooleanField(default=True, verbose_name='Mostrar banner')
	banner_badge_text = models.CharField(
		max_length=80,
		default='Sistema de Autenticacao',
		verbose_name='Texto da badge do banner',
	)
	banner_title = models.CharField(max_length=180, default='Bem-vindo ao Codex', verbose_name='Titulo do banner')
	banner_subtitle = models.TextField(
		default='Home com area personalizada para Admin e Usuario comum.',
		verbose_name='Subtitulo do banner',
	)
	banner_image = models.ImageField(
		upload_to='home/banner/',
		blank=True,
		null=True,
		verbose_name='Imagem do banner (horizontal)',
	)

	menu_section_visible = models.BooleanField(default=True, verbose_name='Mostrar secao de menu')
	menu_section_title = models.CharField(max_length=120, default='Menu', verbose_name='Titulo da secao de menu')

	text_section_visible = models.BooleanField(default=True, verbose_name='Mostrar secao de texto')
	text_section_title = models.CharField(max_length=140, default='Sobre a plataforma', verbose_name='Titulo da secao de texto')
	text_section_content = models.TextField(
		default='Edite este conteudo no admin para destacar informacoes importantes na Home.',
		verbose_name='Conteudo da secao de texto',
	)

	class Meta:
		verbose_name = 'Configuracao da Home'
		verbose_name_plural = 'Configuracao da Home'

	def __str__(self):
		return 'Configuracao da Home'
