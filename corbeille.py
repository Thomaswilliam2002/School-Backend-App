# class EleveConsumer(AsyncWebsocketConsumer):
#     """
#     cette classe gere les connexions websockrt pour les eleves,
#     elle est async pour ne pas bloquer le serveur pendant qu'elle attend des messages
#     """
#     async def connect(self):
#         #appeller quand l'app electron tente de se connecter
#         self.group_name = 'eleves_groupe'
        
#         #on ajoute cette connexion au groupe 'eleves_groupe'
#         #cela permet d'envoyer un message a tous les utilisateursconnecter d'un groupe
#         await self.channel_layer.group_add(
#             self.group_name,
#             self.channel_name
#         )
        
#         #on accepte la connexion
#         await self.accept()
#         print(f"WebSocket connecter: {self.channel_name}")
        
#     async def disconnect(self, close_code):
#         """
#         Appele qund l'utilisateur ferme l'app ou perd la connexion.
#         """
#         #on retire l'utilisateur du groupe
#         await self.channel_layer.group_discard(
#             self.group_name,
#             self.channel_name
#         )
#         print("WebSocket deconnecter")
        
#     async def receive(self, text_data):
#         """Appeler si le frontend envoie un message au serveurvia le socket
#         (optionel si tu ne fais que recevoire des notification du serveur)
#         """
#         data = json.loads(text_data)
#         print(f"message recu du frontend : {data}")
        
#     async def liste_update(self, event):
#         """CETTE METHODE EST LA PLUS IMPORTANTE
#         Elle est appeler par le SIGNAL (api/signals.py) quand un eleve est modifier
#         """
#         message = event['message']
#         data_type = event['data_type']
        
#         #on envois l'information reelement au format JSON vers le frontend(react)
#         await self.send(text_data=json.dumps({
#             'type': 'liste_update',
#             'message': message,
#             'data_type': data_type
#         }))


# ---------------------------------------------------------------------------------------
@receiver(post_save, sender=Eleve)
def notifier_changement_eleve(sender, instance, created, **kwargs):
    """
    Signal déclenché après l'enregistrement d'un élève (Création ou Modification).
    'instance' est l'objet élève qui vient d'être manipulé par votre vue.
    created: True si c'est une création, False si c'est une modification.
    """
    
    # On définit le type d'action pour informer le front-end
    action = "CREATED" if created else "UPDATED"
    
    # On envoie un message au groupe "eleves_group" défini dans le consumer
    # group_send est asynchrone, mais les signaux Django sont synchrones.
    # On utilise async_to_sync pour faire le pont.
    async_to_sync(channel_layer.group_send)(
        "eleves_groupe", # Le nom du groupe défini dans ton consumer
        {
            "type": "liste_update", # Appelle la méthode 'liste_update' dans consumers.py,La méthode à appeler dans ton consumer
            "action": action,
            "nom": instance.nom, # Optionnel : envoyer le nom pour une notification
            "message": f"L'élève {instance.nom} a été {action}.",
            "data_type": "ELEVE"
        }
    )

@receiver(post_delete, sender=Eleve)
def notifier_suppression_eleve(sender, instance, **kwargs):
    """
    Signal déclenché après la suppression d'un élève.
    """
    async_to_sync(channel_layer.group_send)(
        "eleves_groupe",
        {
            "type": "liste_update",
            "action": "DELETED",
            "message": f"L'élève {instance.nom} a été supprimé.",
            "data_type": "ELEVE"
        }
    )

class EnseignantDashboardView(APIView):
    def get(self, request, pk_ens, pk_etab):
        # 1. Vérifier si l'enseignant et l'établissement existent
        try:
            enseignant = Enseignant.objects.get(id_ens=pk_ens)
            etablissement = Etablissement.objects.get(id_etab=pk_etab)
        except (Enseignant.DoesNotExist, Etablissement.DoesNotExist):
            return Response({"error": "Enseignant ou Établissement introuvable"}, status=status.HTTP_404_NOT_FOUND)

        # 2. Récupérer les cours de cet enseignant dans cet établissement
        # On filtre les cours par l'enseignant ET par les classes disponibles dans cet établissement
        cours = Cour.objects.filter(
            enseignant=enseignant,
            classe__disponible_classe__etablissement=etablissement
        ).select_related('classe', 'matiere').distinct()

        # 3. Récupérer des statistiques (ex: nombre de classes, nombre d'élèves total)
        classes_ids = cours.values_list('classe', flat=True)
        total_eleves = Inscrit.objects.filter(
            classe__in=classes_ids, 
            etablissement=etablissement
        ).count()

        # 4. Structure de la réponse
        data = {
            "enseignant": EnseignantSerializers(enseignant).data,
            "etablissement": EtablissementSerializers(etablissement).data,
            "statistiques": {
                "nombre_cours": cours.count(),
                "nombre_classes": len(set(classes_ids)),
                "total_eleves_impactes": total_eleves
            },
            "planning_cours": CoursSerializers(cours, many=True).data
        }
        
        return Response(data, status=status.HTTP_200_OK)
        

class EtablissementDashboardView(APIView):
    def get(self, request, pk_etab):
        try:
            # 1. Tenter de récupérer l'établissement cible via son UUID
            # On le stocke dans une variable pour filtrer toutes les autres requêtes
            etablissement = Etablissement.objects.get(id_etab=pk_etab)
        except Etablissement.DoesNotExist:
            # Si l'ID est faux, on arrête tout et on renvoie une erreur 404
            return Response({"error": "Établissement introuvable"}, status=status.HTTP_404_NOT_FOUND)

        # --- SECTION : COMPTEURS GLOBAUX (KPIs) ---
        
        # Compte le nombre d'élèves uniques inscrits dans cet établissement
        total_eleves = Inscrit.objects.filter(etablissement=etablissement).count()
        
        # Compte combien d'enseignants sont affectés à cet établissement via la table 'Enseigne'
        total_enseignants = Enseigne.objects.filter(etablissement=etablissement).count()
        
        # Compte le nombre de classes déclarées comme disponibles dans cet établissement
        total_classes = Disponible.objects.filter(etablissement=etablissement).count()
        
        # Calcule la somme de toutes les dépenses. aggregate renvoie un dictionnaire, d'où le ['montant__sum']
        # Le "or 0" gère le cas où il n'y a aucune dépense (évite de renvoyer None)
        total_depenses = Depense.objects.filter(etablissement=etablissement).aggregate(Sum('montant'))['montant__sum'] or 0

        # --- SECTION : ANALYSE DES ENSEIGNANTS ---

        # On récupère la répartition des enseignants par genre pour un graphique dédié
        # .values('enseignant__genre') groupe les résultats par le champ genre de la table Enseignant
        repartition_enseignant_genre = Enseigne.objects.filter(etablissement=etablissement).values('enseignant__genre').annotate(
            total=Count('enseignant')
        )

        # --- SECTION : ANALYSE DU STAFF (ADMINISTRATIF) ---

        # On récupère tous les membres du personnel liés à cet établissement
        # Note : Votre modèle Staff actuel n'a pas de lien direct 'etablissement' dans le snippet, 
        # j'adapte ici en supposant que vous filtrez par établissement si le champ existe.
        staff_query = Staff.objects.all() # .filter(etablissement=etablissement) si champ présent
        total_staff = staff_query.count()
        
        # On groupe le staff par "Poste" pour savoir combien de secrétaires, comptables, etc.
        repartition_staff_poste = staff_query.values('poste__libelle').annotate(
            nombre=Count('id_staff')
        )

        # --- SECTION : DÉTAIL PAR CLASSE (DÉMOGRAPHIE) ---

        # Requête complexe pour obtenir l'état civil de chaque classe en une seule fois
        # Q() permet d'ajouter des filtres conditionnels à l'intérieur du Count
        stats_classes = Inscrit.objects.filter(etablissement=etablissement).values(
            'classe__id_classe', 'classe__nom'
        ).annotate(
            effectif_total=Count('eleve'), # Total d'élèves dans la classe
            # iexact ignore la casse (M ou m)
            garcons=Count('eleve', filter=Q(eleve__genre__iexact='Garçon') | Q(eleve__genre__iexact='M') | Q(eleve__genre__iexact='Masculin')),
            filles=Count('eleve', filter=Q(eleve__genre__iexact='Fille') | Q(eleve__genre__iexact='F') | Q(eleve__genre__iexact='Feminin'))
        ).order_by('classe__nom') # Tri alphabétique par nom de classe

        # --- SECTION : PRÉSENCES & COURS ---

        # Taux d'absentéisme global basé sur les enregistrements de présence
        stats_presence = Presence.objects.filter(
            eleve__inscrit_eleve__etablissement=etablissement
        ).values('status').annotate(total=Count('status'))

        # --- CONSTRUCTION DE LA RÉPONSE FINALE ---

        data = {
            # Infos de base sur l'école
            "etablissement": EtablissementSerializers(etablissement).data,
            
            # Les petits carrés de stats en haut du dashboard
            "kpis": {
                "total_eleves": total_eleves,
                "total_enseignants": total_enseignants,
                "total_staff": total_staff,
                "total_classes": total_classes,
                "total_depenses": total_depenses
            },
            
            # Données pour les graphiques (Charts)
            "graphiques": {
                "eleves_par_genre": Inscrit.objects.filter(etablissement=etablissement).values('eleve__genre').annotate(total=Count('eleve')),
                "enseignants_par_genre": repartition_enseignant_genre,
                "repartition_staff_poste": repartition_staff_poste,
                "detail_classes": stats_classes
            },
            
            # Données de suivi
            "presences_globales": stats_presence,
            
            # Liste des 5 dernières dépenses pour le tableau d'activité
            "dernieres_depenses": DepenseSerializers(
                Depense.objects.filter(etablissement=etablissement).order_by('-created_at')[:5], 
                many=True
            ).data
        }
        
        # Envoi de la réponse structurée au Frontend avec un code 200 OK
        return Response(data, status=status.HTTP_200_OK)