from django.db import models


class WikiEntry(models.Model):
    CATEGORIES = [('regras', 'Regras'), ('classes', 'Classes'), ('talentos', 'Talentos'),
                  ('magias', 'Magias'), ('itens', 'Itens'), ('magia_geral', 'Regras gerais de magia')]
    category = models.CharField('Seção', max_length=20, choices=CATEGORIES)
    slug = models.SlugField(max_length=160)
    name = models.CharField('Nome', max_length=200)
    data = models.JSONField(default=dict)
    image = models.ImageField('Imagem', upload_to='wiki/', blank=True)
    visible = models.BooleanField('Visível para os jogadores', default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        constraints = [models.UniqueConstraint(fields=['category', 'slug'], name='wiki_category_slug_unique')]

    def __str__(self):
        return self.name

    def as_content(self):
        content = {**self.data, 'slug': self.slug, 'nome': self.name, 'titulo': self.name}
        if self.image:
            content['image_url'] = self.image.url
        return content
