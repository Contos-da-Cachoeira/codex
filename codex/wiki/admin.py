from django.contrib import admin
from .models import WikiEntry


@admin.register(WikiEntry)
class WikiEntryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'visible', 'updated_at']
    list_filter = ['category', 'visible']
    search_fields = ['name', 'slug']
