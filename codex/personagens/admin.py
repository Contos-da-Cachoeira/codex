from django.contrib import admin
from .models import Personagem


@admin.register(Personagem)
class PersonagemAdmin(admin.ModelAdmin):
	list_display = ('nome', 'usuario', 'classe', 'guilda', 'status', 'status_aprovacao', 'data_criacao')
	list_filter = ('status', 'status_aprovacao', 'classe', 'guilda')
	search_fields = ('nome', 'slug', 'usuario__username', 'usuario__email')
	prepopulated_fields = {'slug': ('nome',)}
