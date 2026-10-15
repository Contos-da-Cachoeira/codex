from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from .models import Personagem
from .rules import validate_base


class AdminCharacterForm(forms.ModelForm):
	class Meta:
		model = Personagem
		fields = '__all__'

	def clean(self):
		data = super().clean()
		if data.get('status_aprovacao') == 2:
			candidate = Personagem(**{field: data.get(field, getattr(self.instance, field)) for field in
				('classe', 'magias_pretendidas', 'feitico_antigo', 'divindade', 'afinidade', 'forma_selvagem', 'revisao_manual')})
			try:
				validate_base(candidate, require_commission=True)
			except ValidationError as error:
				self.add_error(None, '; '.join(error.messages))
		return data


@admin.register(Personagem)
class PersonagemAdmin(admin.ModelAdmin):
	form = AdminCharacterForm
	readonly_fields = ('xp_atual', 'talentos_iniciais', 'revisao_manual')

	def get_readonly_fields(self, request, obj=None):
		return self.readonly_fields + (('classe', 'magias_pretendidas', 'feitico_antigo', 'afinidade') if obj else ()) + (('forma_selvagem',) if obj and obj.forma_selvagem else ())
	list_display = ('nome', 'usuario', 'classe', 'guilda', 'status', 'status_aprovacao', 'data_criacao')
	list_filter = ('status', 'status_aprovacao', 'classe', 'guilda')
	search_fields = ('nome', 'slug', 'usuario__username', 'usuario__email')
	prepopulated_fields = {'slug': ('nome',)}
