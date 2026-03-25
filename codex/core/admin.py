from django.contrib import admin

from .models import HomeDynamicSection, HomePageConfig, Profile, SiteLayoutConfig


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
		('Cabecalho padrao', {
			'fields': ('header_visible', 'header_title'),
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
