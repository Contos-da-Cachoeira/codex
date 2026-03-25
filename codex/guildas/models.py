from django.db import models
from django.utils.text import slugify


# Mapeamento entre IDs das guildas e nomes
GUILDA_IDS = {
    1: "ARTISTAS_REVOLUCAO",
    2: "CIRCULO_FOGO",
    3: "FLORESTA_SOL",
    4: "IRMANDADE_TAVERNAS",
    5: "RASGA_MORTALHAS",
    6: "SOCIEDADE_ZAORI",
    7: "MERCENARIOS",
}

GUILDA_NOMES = {
    1: "Artistas da Revolução",
    2: "Círculo do Fogo",
    3: "Floresta do Sol",
    4: "Irmandade das Tavernas",
    5: "Os Rasga-Mortalhas",
    6: "Sociedade Zaori",
    7: "Mercenários Independentes",
}


class Guilda(models.Model):
    """
    Modelo para informações privadas/administrativas das guildas.
    
    As informações públicas estão em core/constants/guildas.py
    """
    
    guilda_id = models.PositiveIntegerField(unique=True, primary_key=True)
    slug = models.SlugField(max_length=100, unique=True)
    
    # Informações privadas/administrativas
    descricao_interna = models.TextField(
        blank=True,
        help_text="Informações internas visíveis apenas para membros"
    )
    
    # Contadores e estatísticas
    total_membros = models.PositiveIntegerField(default=0)
    total_personagens = models.PositiveIntegerField(default=0)
    
    # Informações adicionais
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    ativa = models.BooleanField(default=True, help_text="Guilda visível e ativa")
    
    class Meta:
        verbose_name = "Guilda"
        verbose_name_plural = "Guildas"
        ordering = ["guilda_id"]
    
    def __str__(self):
        return GUILDA_NOMES.get(self.guilda_id, f"Guilda {self.guilda_id}")
    
    def save(self, *args, **kwargs):
        # Auto-gerar slug a partir do nome da guilda
        if not self.slug:
            self.slug = slugify(GUILDA_NOMES.get(self.guilda_id, f"guilda-{self.guilda_id}"))
        super().save(*args, **kwargs)


class GuildaMembro(models.Model):
    """
    Modelo para registrar membros de guildas.
    Criado automaticamente quando um personagem é associado a uma guilda.
    """
    
    guilda = models.ForeignKey(
        Guilda, 
        on_delete=models.CASCADE, 
        related_name='membros'
    )
    usuario = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='guildas_membro',
        help_text="Usuário que possui pelo menos 1 personagem na guilda"
    )
    data_entrada = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('guilda', 'usuario')
        verbose_name = "Membro da Guilda"
        verbose_name_plural = "Membros das Guildas"
    
    def __str__(self):
        return f"{self.usuario.username} - {self.guilda}"


class GuildaNoticia(models.Model):
    """
    Notícias e boletins internos das guildas.
    Visível apenas para membros.
    """
    
    guilda = models.ForeignKey(
        Guilda,
        on_delete=models.CASCADE,
        related_name='noticias'
    )
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    publicado = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Notícia da Guilda"
        verbose_name_plural = "Notícias das Guildas"
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"{self.guilda} - {self.titulo}"
