from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import secrets
from .validators import validate_birth_date


class ImageAsset(models.Model):
	owner = models.ForeignKey(User, on_delete=models.CASCADE)
	file = models.ImageField(upload_to='images/', blank=True)
	url = models.URLField(blank=True)
	x = models.FloatField(default=50)
	y = models.FloatField(default=50)
	zoom = models.FloatField(default=1)
	ratio = models.FloatField(default=1)

	@property
	def source(self):
		return self.file.url if self.file else self.url


class Profile(models.Model):
	image_asset = models.ForeignKey(ImageAsset, null=True, blank=True, on_delete=models.SET_NULL)
	class UserRole(models.TextChoices):
		ADMIN = 'ADMIN', 'Admin'
		COMMON = 'COMMON', 'Usuario comum'

	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	role = models.CharField(max_length=10, choices=UserRole.choices, default=UserRole.COMMON)
	avatar = models.ImageField(upload_to='profiles/avatars/', blank=True, null=True, verbose_name='Foto de perfil')
	nome_completo_jogador = models.CharField(max_length=180, blank=True)
	data_nascimento = models.DateField(null=True, blank=True, validators=[validate_birth_date], verbose_name='Data de nascimento')
	apelido_cla = models.CharField(max_length=120, blank=True)
	telefone = models.CharField(max_length=30, blank=True)
	cpf = models.CharField(max_length=14, blank=True)
	fobia_gatilho = models.TextField(blank=True)

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
	color_validator = RegexValidator(
		regex=r'^#[0-9A-Fa-f]{6}$',
		message='Use uma cor hexadecimal no formato #RRGGBB.',
	)
	header_visible = models.BooleanField(default=True, verbose_name='Mostrar cabecalho')
	header_title = models.CharField(max_length=120, default='Codex', verbose_name='Titulo do cabecalho')
	primary_color = models.CharField(max_length=7, default='#3A83F7', validators=[color_validator], verbose_name='Cor principal')
	primary_content_color = models.CharField(max_length=7, default='#FFFFFF', validators=[color_validator], verbose_name='Conteudo da cor principal')
	secondary_color = models.CharField(max_length=7, default='#303030', validators=[color_validator], verbose_name='Cor secundaria')
	secondary_content_color = models.CharField(max_length=7, default='#EDEDED', validators=[color_validator], verbose_name='Conteudo da cor secundaria')
	site_background_color = models.CharField(max_length=7, default='#000000', validators=[color_validator], verbose_name='Fundo principal')
	site_surface_color = models.CharField(max_length=7, default='#212121', validators=[color_validator], verbose_name='Superficie principal')
	site_accent_color = models.CharField(max_length=7, default='#3A83F7', validators=[color_validator], verbose_name='Azul de destaque')
	site_accent_content_color = models.CharField(max_length=7, default='#FFFFFF', validators=[color_validator], verbose_name='Texto do destaque')
	site_text_color = models.CharField(max_length=7, default='#EDEDED', validators=[color_validator], verbose_name='Texto principal')
	site_muted_text_color = models.CharField(max_length=7, default='#AFAFAF', validators=[color_validator], verbose_name='Texto secundario')

	social_instagram_url = models.URLField(blank=True, default='', verbose_name='URL do Instagram')
	social_whatsapp_url = models.URLField(blank=True, default='', verbose_name='URL do WhatsApp')
	social_x_url = models.URLField(blank=True, default='', verbose_name='URL do X/Twitter')
	social_youtube_url = models.URLField(blank=True, default='', verbose_name='URL do YouTube')

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


class HomeDynamicSection(models.Model):
	image_asset = models.ForeignKey(ImageAsset, null=True, blank=True, on_delete=models.SET_NULL)
	kind = models.CharField(max_length=20, choices=[('text', 'Texto'), ('community', 'Comunidade / guildas'), ('banner', 'Banner dividido'), ('callout', 'Chamada centralizada'), ('links', 'Atalhos')], default='text')
	button_label = models.CharField(max_length=60, blank=True)
	button_url = models.CharField(max_length=500, blank=True)
	secondary_label = models.CharField(max_length=60, blank=True)
	secondary_url = models.CharField(max_length=500, blank=True)
	eyebrow = models.CharField(max_length=80, blank=True)
	image_url = models.URLField(blank=True)
	title = models.CharField(max_length=140, verbose_name='Titulo')
	content = models.TextField(verbose_name='Conteudo')
	is_visible = models.BooleanField(default=True, verbose_name='Mostrar secao')
	display_order = models.PositiveIntegerField(default=1, verbose_name='Ordem de exibicao')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name = 'Componente extra da Home'
		verbose_name_plural = 'Componentes extras da Home'
		ordering = ('display_order', 'id')

	def __str__(self):
		return f'#{self.display_order} - {self.title}'


class LarpEvento(models.Model):
	titulo = models.CharField(max_length=180)
	slug = models.SlugField(max_length=220, unique=True, blank=True)
	capa = models.ImageField(upload_to='larps/capas/', blank=True, null=True, verbose_name='Capa do evento')
	historia = models.TextField()
	local = models.CharField(max_length=180)
	data_evento = models.DateTimeField()
	data_limite_inscricao = models.DateTimeField(verbose_name='Inscrições até')
	visivel_publicamente = models.BooleanField(default=False)
	inscricao_token = models.CharField(max_length=32, unique=True, editable=False)
	criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='eventos_larp_criados')
	data_criacao = models.DateTimeField(auto_now_add=True)
	data_atualizacao = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ('-data_evento', '-id')
		verbose_name = 'Evento LARP'
		verbose_name_plural = 'Eventos LARP'

	def clean(self):
		super().clean()
		if self.data_limite_inscricao and self.data_evento and self.data_limite_inscricao > self.data_evento:
			raise ValidationError({'data_limite_inscricao': 'O prazo de inscrição não pode ser posterior ao evento.'})

	@property
	def inscricoes_abertas(self):
		return bool(self.data_limite_inscricao and timezone.now() <= min(self.data_limite_inscricao, self.data_evento))

	def save(self, *args, **kwargs):
		if not self.slug:
			base_slug = slugify(self.titulo) or f'larp-{timezone.now().strftime("%Y%m%d")}'
			candidate = base_slug
			index = 1
			while LarpEvento.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
				candidate = f'{base_slug}-{index}'
				index += 1
			self.slug = candidate

		if not self.inscricao_token:
			self.inscricao_token = secrets.token_hex(16)

		super().save(*args, **kwargs)

	def __str__(self):
		return f'{self.titulo} ({self.data_evento:%d/%m/%Y})'


class LarpInscricao(models.Model):
	evento = models.ForeignKey(LarpEvento, on_delete=models.CASCADE, related_name='inscricoes')
	usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inscricoes_larp')
	personagem = models.ForeignKey('personagens.Personagem', on_delete=models.PROTECT, related_name='inscricoes_larp')
	taxa_paga = models.BooleanField(default=False)
	nome_completo_jogador = models.CharField(max_length=180)
	apelido_cla = models.CharField(max_length=120, blank=True)
	telefone = models.CharField(max_length=30)
	cpf = models.CharField(max_length=14)
	fobia_gatilho = models.TextField(blank=True)
	confirmacao_final = models.BooleanField(default=False)
	data_inscricao = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ('-data_inscricao', '-id')
		verbose_name = 'Inscricao LARP'
		verbose_name_plural = 'Inscricoes LARP'
		constraints = [
			models.UniqueConstraint(fields=('evento', 'usuario'), name='unique_inscricao_por_evento_usuario'),
		]

	def __str__(self):
		return f'{self.usuario.username} - {self.evento.titulo}'
