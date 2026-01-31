from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # On importe les signaux ici pour qu'ils soient actifs 
        # dès que le serveur Django démarre
        import api.signals  # <--- TRÈS IMPORTANT