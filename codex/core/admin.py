from django.contrib import admin

from .models import HomeDynamicSection, HomePageConfig, LarpEvento, LarpInscricao, Profile, SiteLayoutConfig


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'role')
	search_fields = ('user__username', 'user__email')
	list_filter = ('role',)


class SingletonAdminMixin:
	def has_add_permission(self, request):
		if self.model.objects.exists():
			return False
		return super().has_add_permission(request)


@admin.register(SiteLayoutConfig)
class SiteLayoutConfigAdmin(SingletonAdminMixin, admin.ModelAdmin):
	fieldsets = (
		('Paleta azul escura', {
			'fields': (
				'primary_color',
				'primary_content_color',
				'secondary_color',
				'secondary_content_color',
				'site_background_color',
				'site_surface_color',
				'site_accent_color',
				'site_accent_content_color',
				'site_text_color',
				'site_muted_text_color',
			),
		}),
		('Cabecalho padrao', {
			'fields': ('header_visible', 'header_title'),
		}),
		('Redes sociais do cabecalho', {
			'fields': ('social_instagram_url', 'social_whatsapp_url', 'social_x_url', 'social_youtube_url'),
		}),
		('Rodape padrao', {
			'fields': (
				'footer_visible',
				'footer_title',
				'footer_description',
				'footer_copyright',
			),
		}),
	)


@admin.register(HomePageConfig)
class HomePageConfigAdmin(SingletonAdminMixin, admin.ModelAdmin):
	fieldsets = (
		('Banner (longo horizontal)', {
			'fields': (
				'banner_visible',
				'banner_badge_text',
				'banner_title',
				'banner_subtitle',
				'banner_image',
			),
		}),
		('Menu Home', {
			'fields': ('menu_section_visible', 'menu_section_title'),
		}),
		('Secao de texto', {
			'fields': (
				'text_section_visible',
				'text_section_title',
				'text_section_content',
			),
		}),
	)


@admin.register(HomeDynamicSection)
class HomeDynamicSectionAdmin(admin.ModelAdmin):
	list_display = ('title', 'display_order', 'is_visible')
	list_filter = ('is_visible',)
	search_fields = ('title', 'content')
	ordering = ('display_order', 'id')


@admin.register(LarpEvento)
class LarpEventoAdmin(admin.ModelAdmin):
	list_display = ('titulo', 'local', 'data_evento', 'visivel_publicamente')
	list_filter = ('visivel_publicamente', 'data_evento')
	search_fields = ('titulo', 'local', 'historia')
	readonly_fields = ('inscricao_token',)
	prepopulated_fields = {'slug': ('titulo',)}


@admin.register(LarpInscricao)
class LarpInscricaoAdmin(admin.ModelAdmin):
	list_display = ('evento', 'usuario', 'personagem', 'taxa_paga', 'data_inscricao')
	list_filter = ('evento', 'taxa_paga', 'data_inscricao')
	search_fields = (
		'evento__titulo',
		'usuario__username',
		'nome_completo_jogador',
		'personagem__nome',
	)
