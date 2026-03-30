from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
import secrets


class Profile(models.Model):
	class UserRole(models.TextChoices):
		ADMIN = 'ADMIN', 'Admin'
		COMMON = 'COMMON', 'Usuario comum'

	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	role = models.CharField(max_length=10, choices=UserRole.choices, default=UserRole.COMMON)
	nome_completo_jogador = models.CharField(max_length=180, blank=True)
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
	class BannerType(models.TextChoices):
		EDITORIAL = 'EDITORIAL', 'Banner Editorial (com texto)'
		ROTATIVO = 'ROTATIVO', 'Banner Rotativo (solo imagem)'

	banner_visible = models.BooleanField(default=True, verbose_name='Mostrar banner')
	banner_type = models.CharField(
		max_length=10,
		choices=BannerType.choices,
		default=BannerType.EDITORIAL,
		verbose_name='Tipo de banner'
	)
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


class RotativeBanner(models.Model):
	"""Modelo para banners rotativos (2000x542) com link clicavel."""
	imagem = models.ImageField(
		upload_to='home/banners_rotativos/',
		verbose_name='Imagem do banner (2000x542)',
	)
	url_redirecionamento = models.URLField(
		max_length=500,
		verbose_name='URL para redirecionamento',
	)
	texto_alternativo = models.CharField(
		max_length=200,
		blank=True,
		verbose_name='Texto alternativo (alt) da imagem',
	)
	ordem_exibicao = models.PositiveIntegerField(
		default=1,
		verbose_name='Ordem de exibicao',
	)
	ativo = models.BooleanField(
		default=True,
		verbose_name='Mostrar este banner',
	)
	data_criacao = models.DateTimeField(auto_now_add=True)
	data_atualizacao = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = 'Banner Rotativo'
		verbose_name_plural = 'Banners Rotativos'
		ordering = ('ordem_exibicao', 'id')

	def __str__(self):
		return f'Banner #{self.ordem_exibicao}'


class LarpEvento(models.Model):
	titulo = models.CharField(max_length=180)
	slug = models.SlugField(max_length=220, unique=True, blank=True)
	historia = models.TextField()
	local = models.CharField(max_length=180)
	data_evento = models.DateTimeField()
	inscricao_ate = models.DateTimeField(blank=True, null=True, verbose_name='Inscricoes abertas ate')
	visivel_publicamente = models.BooleanField(default=False)
	inscricao_token = models.CharField(max_length=32, unique=True, editable=False)
	criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='eventos_larp_criados')
	data_criacao = models.DateTimeField(auto_now_add=True)
	data_atualizacao = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ('-data_evento', '-id')
		verbose_name = 'Evento LARP'
		verbose_name_plural = 'Eventos LARP'

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
	dinheiro_inicio_larp = models.IntegerField(blank=True, null=True, verbose_name='Dinheiro no inicio do LARP')
	dinheiro_pego_larp = models.IntegerField(default=0, verbose_name='Dinheiro pego para o LARP')
	dinheiro_final_larp = models.IntegerField(blank=True, null=True, verbose_name='Dinheiro no final do LARP')
	entrada_larp = models.DateTimeField(blank=True, null=True, verbose_name='Entrada no LARP')
	saida_larp = models.DateTimeField(blank=True, null=True, verbose_name='Saida do LARP')
	dinheiro_ganho = models.IntegerField(default=0, verbose_name='Dinheiro ganho no LARP')
	dinheiro_gasto = models.IntegerField(default=0, verbose_name='Dinheiro gasto no LARP')
	xp_ganho = models.IntegerField(default=0, verbose_name='XP ganho no LARP')
	morreu_no_larp = models.BooleanField(default=False, verbose_name='Morreu no LARP')
	faltou_no_larp = models.BooleanField(default=False, verbose_name='Faltou no LARP')
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
