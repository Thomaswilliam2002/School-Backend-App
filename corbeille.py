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
    
    
class CreatEtablissement(generics.CreateAPIView):
    queryset = Etablissement.objects.all()
    serializer_class = EtablissementSerializers
    
    def create(self, request):
        # Initialisation du serializer avec les données de la requête
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not serializer.is_valid():
            print("!!! ERREUR DE VALIDATION :", serializer.errors) # Regarde ton terminal Python !
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                # 1. Génération d'un code unique
                # Génère un code type ETAB-7812
                suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                code = f"ETAB-{suffix}"
                
                # Vérification de l'unicité
                while Etablissement.objects.filter(code=code).exists():
                    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                    code = f"ETAB-{suffix}"
                
                # 2. Vérification du nom
                nom = self.request.data.get("nom")
                if Etablissement.objects.filter(nom__iexact=nom).exists():
                    raise serializers.ValidationError({"nom": "Un établissement portant ce nom existe déjà."})

                # 3. Sauvegarde
                instance = serializer.save(code=code.upper())
                
                # 4. Envoi de l'email de confirmation avec le code
                """Utiliser serializer.validated_data (Recommandé)
                ex:nom_etab = serializer.validated_data.get('nom')
                C'est la méthode la plus propre car elle utilise les données déjà vérifiées et nettoyées par le Serializer.
                """
                
                email = self.request.data.get('email')
                if not email:
                    raise serializers.ValidationError({"email": "L'email est requis pour confirmer l'inscription."})
                if email:
                    send_mail(
                        "UNCHAIN School App",
                        f"Votre Etablissement a bien été inscrit avec succès.\n Voici le code de votre Etablissement : {code}.\n\nCordialement,\nL'administration de UNCHAIN School App",
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                    
                return Response({
                    "message": "Inscription réussie ! Un mail a été envoyé.",
                    "etablissement": serializer.data
                }, status=status.HTTP_201_CREATED)
                
                #print(f"Etablissement created successfully. Code: {code}")
                
                # return Response({"code": code, "message": "Etablissement created successfully."}, status=status.HTTP_201_CREATED)
        except SMTPRecipientsRefused:
            return Response({
                    "message": "L'adresse email est refusée ou inexistante. Inscription annulée.",
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Ici, 'e' contient la cause du fail
            error_message = str(e)
            # On peut même être plus précis sur le type d'erreur
            if "Authentication failed" in error_message:
                detail = "Le serveur de mail a refusé les identifiants (mot de passe d'application ?)"
            elif "Connection refused" in error_message:
                detail = "Impossible de contacter le serveur SMTP (Port bloqué ou mauvais hôte)"
            else:
                detail = f"Erreur technique : {error_message}"

            raise serializers.ValidationError({"email_error": detail})
        
        
            
            
            
                
    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                # 1. Génération d'un code unique
                # Génère un code type ETAB-7812
                suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                code = f"ETAB-{suffix}"
                
                # Vérification de l'unicité
                while Etablissement.objects.filter(code=code).exists():
                    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                    code = f"ETAB-{suffix}"
                
                # 2. Vérification du nom
                nom = self.request.data.get("nom")
                if Etablissement.objects.filter(nom__iexact=nom).exists():
                    raise serializers.ValidationError({"nom": "Un établissement portant ce nom existe déjà."})

                # 3. Sauvegarde
                serializer.save(code=code.upper())
                
                # 4. Envoi de l'email de confirmation avec le code
                """Utiliser serializer.validated_data (Recommandé)
                ex:nom_etab = serializer.validated_data.get('nom')
                C'est la méthode la plus propre car elle utilise les données déjà vérifiées et nettoyées par le Serializer.
                """
                
                email = self.request.data.get('email')
                if email:
                    send_mail(
                        "UNCHAIN School App",
                        f"Votre Etablissement a bien été inscrit avec succès.\n Voici le code de votre Etablissement : {code}.\n\nCordialement,\nL'administration de UNCHAIN School App",
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                    )
                
                #print(f"Etablissement created successfully. Code: {code}")
                
                # 4. Retourner le code et le message
                return Response({"codee": code, "message": "Etablissement djjdhjdhgj created successfully."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
        
def perform_create(self, serializer):
        # 1. Récupération des données nécessaires
        email = self.request.data.get("email")
        etab_id = self.request.data.get("idEtat")
        post_id = self.request.data.get("idPost")
        photo = self.request.FILES.get("photo")
        
        # Validation de base
        if not email:
            raise serializers.ValidationError({"email": "L'adresse email est obligatoire pour créer un compte personnel."})
        if not etab_id:
            raise serializers.ValidationError({"idEtat": "L'ID de l'établissement est requis."})
        
        try:
            with transaction.atomic():
                # 2. CRÉATION DU COMPTE UTILISATEUR (USER)
                # On vérifie si l'utilisateur existe déjà pour éviter les doublons
                if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
                    raise serializers.ValidationError({"email": "Un utilisateur avec cet email existe déjà."})

                # L'email sert d'identifiant (username) et d'email de contact
                # On génère un mot de passe temporaire ou on en demande un
                temp_password = "Stf@" + "".join(random.choices(string.digits, k=4))
                
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=temp_password
                )

                # 3. CRÉATION DE L'ENSEIGNANT (lié au User)
                staff = serializer.save(user=user)

                # 4. RATTACHEMENT À L'ÉTABLISSEMENT et du Poste (Table Occuoe)
                etablissement = Etablissement.objects.get(id_etab=etab_id)
                poste = Poste.objects.get(id_poste = post_id)
                
                # On crée le lien dans la table de liaison Occupe
                Occupe.objects.create(
                    staff=staff,
                    etablissement=etablissement,
                    poste = poste,
                    salaire = self.request.data.get("salaire") or 0,
                    date_debut = self.request.data.get("date_debut") or datetime.now().date()
                )

                # 5. GESTION DE LA PHOTO / DOCUMENTS
                if photo:
                    DocumentStaff.objects.create(
                        staff=staff,
                        titre="Photo de profil",
                        fichier=photo,
                        type_fichier="IMAGE"
                    )

                # 6. ENVOI DES IDENTIFIANTS (Log console pour le moment)
                print(f"Staff créé : {email} | MDP temporaire : {temp_password}")
                
                # C'est ici que tu pourrais appeler une fonction send_mail() 
                # pour envoyer ses accès au staff.

        except Etablissement.DoesNotExist:
            raise serializers.ValidationError({"idEtat": "Établissement introuvable."})
        except Poste.DoesNotExist:
            raise serializers.ValidationError({"idPoste": "Poste introuvable."})
        except Exception as e:
            raise serializers.ValidationError({"detail": str(e)})
        
# --------------------------------------------------create eleve -----------------------------------------------
try:
    if email_parent_1:
        validate_email(email_parent_1)
        listEmail.append(email_parent_1)
except ValidationError:
    return Response(
        {"message": "L'email du parent 1 n'est pas valide"},
        status=status.HTTP_400_BAD_REQUEST
    )

try:
    if email_parent_2:
        validate_email(email_parent_2)
        listEmail.append(email_parent_2)
except ValidationError:
    return Response(
        {"message": "L'email du parent 2 n'est pas valide"},
        status=status.HTTP_400_BAD_REQUEST
    )
    
# --------------------------------------------creat emploit du temps-----------------------------------------------------------
def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cours = self.request.data.get("cours")
            annee_scolaire = self.request.data.get("annee_scolaire")
            horaire = self.request.data.get("horaire")
            # prof = self.request.data.get("prof")
            classe = self.request.data.get("classe")
            etablissement = self.request.data.get("etablissement")
            
            #Mise en place des verifications de securitere
            # Récupérer le cours pour connaître le prof et la classe

            if Cour.objects.filter(id_etab=etablissement, id_cours=cours, annee_scolaire=annee_scolaire).exists():
                return Response({"message": "Ce cours (Classe + Matière) est déjà configuré pour cette classe pour cette année scolaire."}, status=status.HTTP_400_BAD_REQUEST)
            
            print(horaire)
            
            with transaction.atomic():
                for jour, heures in horaire.items():
                    debut = heures.get("debut")
                    fin = heures.get("fin")
                    
                    
                    # VERIFICATION : Le prof est-il déjà occupé ?
                    conflit_prof = EmploiDuTemps.objects.filter(
                        cour__enseignant=cours.enseignant,
                        jour=jour,
                        heure_debut__lt=fin, # Commence avant que le nouveau cours finisse
                        heure_fin__gt=debut   # Finit après que le nouveau cours commence
                    ).exists()

                    if conflit_prof:
                        return Response({"message": "`Cet enseignant a deja un cours sur ce crianneau de ${debut} a ${fin}.`"}, status=status.HTTP_400_BAD_REQUEST)
                    
                    emploi = EmploiDuTemps.objects.filter(jour=jour, heure_debut=debut, heure_fin=fin).exists()
                    if not emploi:
                        EmploiDuTemps.objects.create(
                            jour=jour,
                            heure_debut=debut,
                            heure_fin=fin,
                            etablissement=etablissement,
                            cour=cours,
                            classe=classe
                        )
                    else:
                        return Response({"message": "`Ce crenau est deja pris par le cours de ${emploi.cour.nom}`"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Emploi du temps configuré avec succès."}, status=status.HTTP_201_CREATED)  
        except Exception as e:
            print(e)
            return Response({"message": "Une erreur s'est produite lors de la configuration de l'emploi du temps. veillez ressayer."}, status=status.HTTP_400_BAD_REQUEST)


def calculer_taux_reussite(inscrits,etablissement_id, annee_id, periode_index, disponible_obj):
            # 1. Récupération optimisée des inscrits de la classe spécifique
            inscrits = inscrits.select_related('eleve', 'disponible__classe')

            classe_nom = disponible_obj.classe.nom
            stats = {'admis': 0, 'total': 0, 'taux': 0}

            for inscrit in inscrits:
                # 2. Récupération de toutes les évaluations de l'élève pour la période
                evals_eleve = Evaluation.objects.filter(
                    eleve=inscrit.eleve,
                    annee_scolaire_id=annee_id,
                    periode=periode_index
                ).select_related('cour__matiere')

                # Identifier les cours uniques via l'ensemble des évaluations récupérées
                cours_ids = set(evals_eleve.values_list('cour_id', flat=True))
                
                somme_moyennes_coeff = 0
                total_coefficients = 0

                for c_id in cours_ids:
                    # Filtrage en mémoire (plus rapide qu'une requête SQL par matière)
                    notes_matiere = [e for e in evals_eleve if e.cour_id == c_id]
                    
                    # Séparation par typeEval
                    interros = [n.note for n in notes_matiere if n.typeEval.upper() == 'INTERROGATION']
                    devoirs = [n.note for n in notes_matiere if n.typeEval.upper() == 'DEVOIR']
                    
                    # Calcul de la moyenne interro
                    moy_interro = float(sum(interros) / len(interros)) if interros else 0
                    # Somme des devoirs
                    som_devoir = float(sum(devoirs)) if devoirs else 0
                    
                    # Application de votre formule
                    moyenne_matiere = (moy_interro + som_devoir) / 3
                    
                    # Récupération du coefficient du cours
                    coeff = notes_matiere[0].cour.coefficient
                    
                    somme_moyennes_coeff += (moyenne_matiere * coeff)
                    total_coefficients += coeff

                # 3. Validation de la réussite de l'élève
                if total_coefficients > 0:
                    if (somme_moyennes_coeff / total_coefficients) >= 10:
                        stats['admis'] += 1
                
                stats['total'] += 1

            # 4. Calcul du pourcentage
            if stats['total'] > 0:
                stats['taux'] = (stats['admis'] / stats['total']) * 100

            return {classe_nom: stats}
        