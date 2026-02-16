from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # On importe les signaux ici pour qu'ils soient actifs 
        # dès que le serveur Django démarre
        import api.signals
        # On importe ici pour être sûr que les modèles sont chargés
        # import sys
        # # On évite d'exécuter cela pendant les migrations ou les tests
        # if 'runserver' in sys.argv:
        #     from .models import Poste
            
        #     postes = [
        #         {"nom": "Directeur", "code": "DIRECTEUR"},
        #         {"nom": "Censeur", "code": "CENSEUR"},
        #         {"nom": "Surveillant", "code": "SURVEILLANT"},
        #         {"nom": "Comptable", "code": "COMPTABLE"}
        #     ]
        #     try:
        #         for poste in postes:
        #             # get_or_create vérifie si le 'code' existe déjà
        #             # Si non, il le crée avec les valeurs de 'defaults'
        #             Poste.objects.get_or_create(
        #                 code=poste["code"],
        #                 defaults={"nom": poste["nom"]}
        #             )
        #     except(KeyboardInterrupt, SystemExit):
        #         return