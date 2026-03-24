from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'role')
	search_fields = ('user__username', 'user__email')
	list_filter = ('role',)
