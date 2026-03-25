from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

from .consts import (
	CLASSES_CHOICES,
	GUILDAS_CHOICES,
	STATUS_APROVACAO,
	STATUS_APROVACAO_CHOICES,
	STATUS_PERSONAGEM,
	STATUS_PERSONAGEM_CHOICES,
)


class Personagem(models.Model):
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
	xp_atual = models.PositiveIntegerField(default=0)
	ouro = models.PositiveIntegerField(default=0)
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

	def __str__(self):
		return self.nome
