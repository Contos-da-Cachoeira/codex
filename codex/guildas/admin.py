from django.contrib import admin

from .models import Guilda, GuildaMembro, GuildaNoticia


@admin.register(Guilda)
class GuildaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'slug', 'total_membros', 'total_personagens', 'ativa')
    list_filter = ('ativa', 'data_criacao')
    search_fields = ('slug',)
    readonly_fields = ('guilda_id', 'data_criacao', 'data_atualizacao', 'total_membros', 'total_personagens')
    
    fieldsets = (
        ('Identificação', {
            'fields': ('guilda_id', 'slug')
        }),
        ('Informações', {
            'fields': ('descricao_interna', 'ativa')
        }),
        ('Estatísticas', {
            'fields': ('total_membros', 'total_personagens'),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': ('data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GuildaMembro)
class GuildaMembroAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'guilda', 'data_entrada')
    list_filter = ('guilda', 'data_entrada')
    search_fields = ('usuario__username', 'guilda__slug')
    readonly_fields = ('data_entrada',)


@admin.register(GuildaNoticia)
class GuildaNoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'guilda', 'criado_em', 'publicado')
    list_filter = ('guilda', 'publicado', 'criado_em')
    search_fields = ('titulo', 'guilda__slug')
    readonly_fields = ('criado_em', 'atualizado_em')
    
    fieldsets = (
        ('Guilda', {
            'fields': ('guilda',)
        }),
        ('Conteúdo', {
            'fields': ('titulo', 'conteudo')
        }),
        ('Status', {
            'fields': ('publicado',)
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
