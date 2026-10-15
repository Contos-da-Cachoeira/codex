from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from core.money import validate_gold

from .consts import (
	CLASSES_CHOICES,
	GUILDAS_CHOICES,
	STATUS_APROVACAO,
	STATUS_APROVACAO_CHOICES,
	STATUS_PERSONAGEM,
	STATUS_PERSONAGEM_CHOICES,
)


class Personagem(models.Model):
	image_asset = models.ForeignKey('core.ImageAsset', null=True, blank=True, on_delete=models.SET_NULL)
	portrait_mode = models.CharField(max_length=10, choices=(('name', 'Nome'), ('class', 'Imagem da classe'), ('photo', 'Foto própria')), default='name')
	usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personagens')
	nome = models.CharField(max_length=120)
	slug = models.SlugField(max_length=140, unique=True, blank=True)
	historia = models.TextField(blank=True)
	aparencia = models.TextField(blank=True)
	objetivos = models.TextField(blank=True)
	personalidade = models.TextField(blank=True)
	status = models.PositiveSmallIntegerField(
		choices=STATUS_PERSONAGEM_CHOICES,
		default=STATUS_PERSONAGEM.ATIVO,
	)
	status_aprovacao = models.PositiveSmallIntegerField(
		choices=STATUS_APROVACAO_CHOICES,
		default=STATUS_APROVACAO.PENDENTE,
	)
	guilda = models.PositiveSmallIntegerField(choices=GUILDAS_CHOICES, null=True, blank=True)
	classe = models.PositiveSmallIntegerField(choices=CLASSES_CHOICES, null=True, blank=True)
	magias_pretendidas = models.JSONField(default=list, blank=True)
	talentos_iniciais = models.JSONField(default=list, blank=True)
	feitico_antigo = models.CharField(max_length=40, blank=True)
	divindade = models.CharField(max_length=120, blank=True)
	afinidade = models.CharField(max_length=200, blank=True)
	forma_selvagem = models.TextField(blank=True, help_text='Definição da comissão: três características e um defeito.')
	revisao_manual = models.BooleanField(default=False)
	xp_atual = models.PositiveIntegerField(default=0)
	ouro = models.DecimalField(max_digits=11, decimal_places=1, default=0, validators=[MinValueValidator(0), validate_gold], verbose_name='Ouro (DO)')
	data_criacao = models.DateTimeField(auto_now_add=True)
	data_atualizacao = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-data_criacao']
		verbose_name = 'Personagem'
		verbose_name_plural = 'Personagens'

	def save(self, *args, **kwargs):
		if not self.slug:
			base_slug = slugify(self.nome) or f'personagem-{self.usuario_id}'
			candidate = base_slug
			index = 1
			while Personagem.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
				candidate = f'{base_slug}-{index}'
				index += 1
			self.slug = candidate
		super().save(*args, **kwargs)

	@property
	def class_image(self):
		from wiki.catalog import class_catalog
		return class_catalog().get(self.classe, {}).get('imagem', '')

	@property
	def class_image_url(self):
		from wiki.catalog import class_catalog
		from django.templatetags.static import static
		data = class_catalog().get(self.classe, {})
		return data.get('image_url') or (static(data['imagem']) if data.get('imagem') else '')

	@property
	def xp_jogador(self):
		return getattr(getattr(self.usuario, 'profile', None), 'xp_disponivel', 0)

	@property
	def magias_conhecidas(self):
		magias = list(self.magias_pretendidas)
		for compra in self.compras_talentos.filter(status='approved', ativo=True):
			if compra.talento in {'MAGIA_EXTRA_CLASSE', 'MAGIA_OUTRA_CLASSE', 'CONJURAR'} and compra.magia and compra.magia not in magias:
				magias.append(compra.magia)
		return magias

	@property
	def capacidades_classes(self):
		from wiki.catalog import class_catalog
		from .rules import FOCI
		catalog = class_catalog()
		result = []
		for purchase in self.compras_talentos.filter(status='approved', ativo=True, talento='MULTICLASSE'):
			data = catalog.get(purchase.segunda_classe, {})
			result.append({'nome': data.get('nome', purchase.get_segunda_classe_display()),
				'habilidade': data.get('habilidade_especial', ''), 'dons': data.get('extra', ''),
				'focos': FOCI.get(purchase.segunda_classe, '').replace('Cajado, ', '').replace('Cajado; ', ''),
				'feitico': purchase.magia, **purchase.escolhas_classe})
		return result


class CompraTalento(models.Model):
	personagem = models.ForeignKey(Personagem, related_name='compras_talentos', on_delete=models.CASCADE)
	talento = models.CharField(max_length=40)
	custo_xp = models.PositiveIntegerField()
	magia = models.CharField(max_length=120, blank=True)
	segunda_classe = models.PositiveSmallIntegerField(choices=CLASSES_CHOICES, null=True, blank=True)
	foco = models.CharField(max_length=120, blank=True)
	tipo_foco = models.CharField(max_length=20, blank=True)
	escolhas_classe = models.JSONField(default=dict, blank=True)
	regra_snapshot = models.JSONField(default=dict, blank=True)
	detalhes = models.TextField(blank=True)
	talentos_relacionados = models.JSONField(default=list, blank=True)
	justificativa = models.TextField()
	status = models.CharField(max_length=10, choices=(('pending', 'Aguardando comissão'), ('approved', 'Adquirido'), ('rejected', 'Recusado')), default='pending')
	ativo = models.BooleanField(default=False)
	aprovado_por = models.ForeignKey(User, null=True, blank=True, related_name='+', on_delete=models.SET_NULL)
	data_criacao = models.DateTimeField(auto_now_add=True)

	@property
	def nome(self):
		from wiki.catalog import talent_catalog
		return (self.regra_snapshot or talent_catalog(include_hidden=True).get(self.talento, {})).get('nome', self.talento)

	@property
	def precisa_completar_escolhas(self):
		if self.status != 'approved' or self.talento != 'MULTICLASSE':
			return False
		if self.segunda_classe == 8:
			from .rules import ANCIENT_SPELLS
			return self.magia not in ANCIENT_SPELLS
		if self.segunda_classe == 5:
			return not all(self.escolhas_classe.get(key, '').strip() for key in ('afinidade', 'forma_selvagem'))
		return self.segunda_classe in {4, 9} and not self.escolhas_classe.get('divindade', '').strip()


class MovimentoXP(models.Model):
	jogador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movimentos_xp')
	valor = models.IntegerField()
	saldo = models.PositiveIntegerField()
	motivo = models.CharField(max_length=240)
	compra = models.OneToOneField(CompraTalento, null=True, blank=True, on_delete=models.PROTECT)
	responsavel = models.ForeignKey(User, null=True, blank=True, related_name='+', on_delete=models.SET_NULL)
	data_criacao = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.nome
