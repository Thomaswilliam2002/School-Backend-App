import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Etablissement, Occupe, Enseigne, Inscrit

class EtablissementConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Récupération de l'ID de l'établissement depuis l'URL
        self.etab_id = self.scope['url_route']['kwargs']['etab_id']
        
        #recuperer les infos de celui qui envois la requete
        self.user = self.scope['user']
        print(self.user)
        
        # Le nom du groupe est unique à l'établissement pour l'isolation
        self.room_group_name = f'etablissement_{self.etab_id}'
        
        # 1. Vérification de l'authentification de base / Vérification de l'accès (Logique SaaS)
        if self.user.is_anonymous:
            await self.close()
            return

        # 2. Vérification de l'appartenance à l'établissement (Isolation SaaS)
        is_member = await self.check_user_membership()
        
        if is_member:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        else:
            # Refus de connexion si l'utilisateur n'appartient pas à l'école
            await self.close()
            
    @database_sync_to_async
    def check_user_membership(self):
        """
        Vérifie si l'utilisateur appartient à l'établissement via les tables de liaison.
        """
        eid = self.etab_id #id de l'etablissement
        
        # Vérification pour le Staff (via modèle Occupe)
        if Occupe.objects.filter(staff__email=self.user.email, etablissement_id=eid, is_active=True).exists():
            return True
        
        # Vérification pour l'Enseignant (via modèle Enseigne)
        if Enseigne.objects.filter(enseignant__email=self.user.email, etablissement_id=eid, is_active=True).exists():
            return True
            
        # Vérification pour l'Élève/Parent (via modèle Inscrit)
        # On vérifie si l'email de l'user correspond à l'un des parents
        if Inscrit.objects.filter(
            eleve__email_parent_1=self.user.email, 
            etablissement_id=eid, 
            is_active=True
        ).exists() or Inscrit.objects.filter(
            eleve__email_parent_2=self.user.email, 
            etablissement_id=eid, 
            is_active=True
        ).exists():
            return True

        return False

    async def disconnect(self, close_code):
        # On quitte le groupe de l'établissement
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Cette méthode reçoit les événements envoyés par le signal ci-dessus
    async def eleve_event(self, event):
        await self.send_json({
            "category": "ELEVE_SYNC",
            "action": event["action"],
            "data": event.get("data"),
            "eleve_id": event.get("eleve_id")
        })
