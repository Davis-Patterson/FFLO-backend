from django.apps import AppConfig


class ServerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Server'

    from django.apps import AppConfig

    def ready(self):
        import Server.signals