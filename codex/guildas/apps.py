from django.apps import AppConfig


class GuildasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'guildas'
    
    def ready(self):
        import guildas.signals  # noqa
