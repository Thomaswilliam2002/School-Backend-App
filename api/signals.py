from django.db.models.signals import post_save, post_delete # Le type de signal (après l'enregistrement)
from django.dispatch import receiver # Le décorateur pour "recevoir" le signal
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import * # Basé sur votre models.py
from .serializers import *

# On récupère la couche de communication de Django Channels
channel_layer = get_channel_layer()

#------------------- ELEVE -------------------------------------
@receiver(post_save, sender=Inscrit)
def notify_eleve_change(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    etab_id = str(instance.etablissement.id_etab)
    group_name = f'etablissement_{etab_id}'

    if created:
        action = "CREATE"
    else:
        action = "UPDATE"

    # On prépare les données de l'élève lié à cette inscription
    data = EleveSerializers(instance.eleve).data

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "eleve_event", # Nom de la fonction dans le consumer
            "action": action,
            "data": data
        }
    )

@receiver(post_delete, sender=Inscrit)
def notify_eleve_delete(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    etab_id = str(instance.etablissement.id_etab)
    
    async_to_sync(channel_layer.group_send)(
        f'etablissement_{etab_id}',
        {
            "type": "eleve_event",
            "action": "DELETE",
            "eleve_id": str(instance.eleve.id_eleve)
        }
    )

