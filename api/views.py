from django.shortcuts import render
from rest_framework import generics, status, serializers
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, Q
from django.db import transaction # Importez le module de transaction
from django.db.models import Avg
from django.db.models.expressions import RawSQL
from .models import *
from .serializers import *
import random
import string
from django.db import transaction
from datetime import datetime

# Create your views here.
# ----------------------------------liste des requets start--------------------------

# ----------------------------------liste des requets end--------------------------
# -----------------------Etablissement start---------------------------------------
"""class EtablissementListCreateView(generics.ListCreateAPIView):
    queryset = Etablissement.objects.all()
    serializer_class = EtablissementSerializers"""
    
class EtablissementList(generics.ListAPIView):
    queryset = Etablissement.objects.all()
    serializer_class = EtablissementSerializers
    
class CreatEtablissement(generics.CreateAPIView):
    queryset = Etablissement.objects.all()
    serializer_class = EtablissementSerializers
    
    def perform_create(self, serializer):
        # 1. Génération d'un code unique
        if not code:
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
        
        print(f"Etablissement created successfully. Code: {code}")
        
        # 4. Retourner le code et le message
        # return Response({"code": code, "message": "Etablissement created successfully."}, status=status.HTTP_201_CREATED)

class OnEtablissement(generics.RetrieveAPIView):
    queryset = Etablissement.objects.all()
    serializer_class = EtablissementSerializers
    lookup_field = 'pk'
    
class EtablissementUpdate(generics.UpdateAPIView):
    queryset = Etablissement.objects.all()
    serializer_class = EtablissementSerializers
    lookup_field = 'pk'
    
    def perform_update(self, serializer):
        with transaction.atomic():
            # Sauvegarde de l'établissement
            etablissement = serializer.save()

            # Si le champ is_active est présent dans la mise à jour
            if 'is_active' in self.request.data:
                status_active = etablissement.is_active # True ou False
                
                # A. ÉLÈVES : On récupère les IDs via la table Inscrit
                eleves_ids = Inscrit.objects.filter(etablissement=etablissement).values_list('eleve', flat=True)
                Eleve.objects.filter(id_eleve__in=eleves_ids).update(is_active=status_active)
                # On synchronise leurs comptes de connexion
                User.objects.filter(eleve_profile__id_eleve__in=eleves_ids).update(is_active=status_active)

                # B. STAFF : On récupère les IDs via la table Occupe
                staff_ids = Occupe.objects.filter(etablissement=etablissement).values_list('staff_id', flat=True)
                Staff.objects.filter(id_staff__in=staff_ids).update(is_active=status_active)
                # On synchronise leurs comptes de connexion
                User.objects.filter(staff_profile__id_staff__in=staff_ids).update(is_active=status_active)

                # C. ENSEIGNANTS : On récupère les IDs via la table Enseigne
                ens_ids = Enseigne.objects.filter(etablissement=etablissement).values_list('enseignant_id', flat=True)
                Enseignant.objects.filter(id_ens__in=ens_ids).update(is_active=status_active)
                # On synchronise leurs comptes de connexion
                User.objects.filter(enseignant_profile__id_ens__in=ens_ids).update(is_active=status_active)

                print(f"Action sur {etablissement.nom} : {'Réactivation' if status_active else 'Suspension'} globale effectuée.")
    
class EtablissementDestroy(generics.DestroyAPIView):
    queryset = Etablissement.objects.all()
    serializer_class = EtablissementSerializers
    lookup_field = 'pk'
# -----------------------Etablissement end---------------------------------------
# -----------------------Enseignant start---------------------------------------
class EnseignantList(generics.ListAPIView):
    queryset = Enseignant.objects.all()
    serializer_class = EnseignantSerializers
    
class CreatEnseignant(generics.CreateAPIView):
    queryset = Enseignant.objects.all()
    serializer_class = EnseignantSerializers
    parser_classes = (MultiPartParser, FormParser)
    
    def perform_create(self, serializer):
        # 1. Récupération des données nécessaires
        email = self.request.data.get("email")
        etab_id = self.request.data.get("idEtat")
        photo = self.request.FILES.get("photo")
        
       # Validation de base
        if not email:
            raise serializers.ValidationError({"email": "L'adresse email est obligatoire pour créer un compte enseignant."})
        if not etab_id:
            raise serializers.ValidationError({"idEtat": "L'ID de l'établissement est requis."})
        
        try:
            with transaction.atomic():
                # 2. CRÉATION DU COMPTE UTILISATEUR (USER)
                # On vérifie si l'utilisateur existe déjà pour éviter les doublons
                if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
                    raise serializers.ValidationError({"email": "Un utilisateur avec cet email existe déjà."})

                # L'email sert d'identifiant (username) et l'email de contact
                # On génère un mot de passe temporaire ou on en demande un
                temp_password = "Ens@" + "".join(random.choices(string.digits, k=4))
                
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=temp_password
                )

                # 3. CRÉATION DE L'ENSEIGNANT (lié au User)
                enseignant = serializer.save(user=user)

                # 4. RATTACHEMENT À L'ÉTABLISSEMENT (Table Enseigne)
                etablissement = Etablissement.objects.get(id_etab=etab_id)
                
                # On crée le lien dans la table de liaison Enseigne
                Enseigne.objects.create(
                    enseignant=enseignant,
                    etablissement=etablissement
                )

                # 5. GESTION DE LA PHOTO / DOCUMENTS
                if photo:
                    DocumentEnseignant.objects.create(
                        enseignant=enseignant,
                        titre="Photo de profil",
                        fichier=photo,
                        type_fichier="IMAGE"
                    )

                # 6. ENVOI DES IDENTIFIANTS (Log console pour le moment)
                print(f"Enseignant créé : {email} | MDP temporaire : {temp_password}")
                
                # C'est ici que tu pourrais appeler une fonction send_mail() 
                # pour envoyer ses accès à l'enseignant.

        except Etablissement.DoesNotExist:
            raise serializers.ValidationError({"idEtat": "Établissement introuvable."})
        except Exception as e:
            raise serializers.ValidationError({"detail": str(e)})

class OnEnseignant(generics.RetrieveAPIView):
    queryset = Enseignant.objects.all()
    serializer_class = EnseignantSerializers
    lookup_field = 'pk'
    
class EnseignantUpdate(generics.UpdateAPIView):
    queryset = Enseignant.objects.all()
    serializer_class = EnseignantSerializers
    parser_classes = (MultiPartParser, FormParser)
    lookup_field = 'pk'
    
    def perform_update(self, serializer):
        with transaction.atomic():
            # On sauvegarde les modifications de l'enseignant
            enseignant = serializer.save()
            
            # 1. Mise à jour de l'email dans le compte User
            # Si l'email est envoyé dans la requête, on met à jour le User lié
            new_email = self.request.data.get("email")
            if new_email and enseignant.user:
                user = enseignant.user
                user.email = new_email
                user.username = new_email  # Puisque l'enseignant se connecte avec son email
                
            # Mise à jour de l'activation
            user.is_active = enseignant.is_active
            user.save()
                
            # 2. Gestion de la Photo
            photo = self.request.FILES.get("photo")
            if photo:
                doc_photo = DocumentEnseignant.objects.filter(enseignant=enseignant, titre="Photo de profil").first()
                if doc_photo:
                    doc_photo.fichier = photo
                    doc_photo.save()
                else:
                    DocumentEnseignant.objects.create(
                        enseignant=enseignant,
                        titre="Photo de profil",
                        fichier=photo,
                        type_fichier="IMAGE"
                    )
    
class EnseignantDestroy(generics.DestroyAPIView):
    queryset = Enseignant.objects.all()
    serializer_class = EnseignantSerializers
    lookup_field = 'pk'
# -----------------------Enseignant end---------------------------------------
# -----------------------Eleve start---------------------------------------
class EleveList(generics.ListAPIView):
    queryset = Eleve.objects.all()
    serializer_class = EleveSerializers
    
class CreatEleve(generics.CreateAPIView):
    parser_classes = (MultiPartParser, FormParser)
    queryset = Eleve.objects.all()
    serializer_class = EleveSerializers
    
    def perform_create(self, serializer):
        # On récupère les données supplémentaires envoyées dans la requête
        etab_id = self.request.data.get("idEtat")
        classe_id = self.request.data.get("classe")
        annee_scolaire = self.request.data.get("anneeScolaire")
        photo = self.request.FILES.get("photo")
        print(f"{etab_id} | {classe_id}")
        
        # Sécurité : Vérification avant de commencer la transaction
        if not etab_id or not classe_id:
            raise serializers.ValidationError({
                "error": "L'ID de l'établissement (idEtat) et de la classe sont requis."
            })
        
        try:
            # Utilisation de transaction.atomic pour garantir l'intégrité
            with transaction.atomic():
                # 1. GÉNÉRATION DU MATRICULE (Username)
                # Format: EL + Année + 4 caractères aléatoires (ex: EL2024X8P1)
                year = datetime.now().year
                suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                matricule = f"EL{year}{suffix}"
                
                
                # 2. CRÉATION DU COMPTE UTILISATEUR
                # Le matricule sert d'identifiant ET de mot de passe par défaut
                user = User.objects.create_user(
                    username=matricule,
                    # email=self.request.data.get('email_parent_1') or "",
                    password=matricule 
                )
                
                # 3. SAUVEGARDE DE L'ÉLÈVE (Lié à l'User)
                eleve = serializer.save(user=user)
                
                # 4. RÉCUPÉRATION DES INSTANCES ET INSCRIPTION
                etablissement = Etablissement.objects.get(id_etab=etab_id)
                classe = Classe.objects.get(id_classe=classe_id)

                Inscrit.objects.create(
                    eleve=eleve,
                    etablissement=etablissement,
                    classe=classe,
                    annee_scolaire = annee_scolaire
                )
                
                # 5. GESTION DE LA PHOTO
                # On le fait après l'inscription pour que upload_eleve_path 
                # puisse trouver l'établissement !
                if photo:
                    DocumentEleve.objects.create(
                        eleve=eleve,
                        titre="Photo de profil",
                        description=f"Photo de profil de {eleve.nom}",
                        fichier=photo,
                        type_fichier="IMAGE"
                    )
                    
                # Optionnel : Tu peux ajouter ici l'envoi d'un SMS ou Email au parent 
                # avec le matricule de l'enfant.
                    
                    
        except Etablissement.DoesNotExist:
            raise serializers.ValidationError({"idEtat": "L'établissement spécifié est introuvable."})
        except Classe.DoesNotExist:
            raise serializers.ValidationError({"classe": "La classe spécifiée est introuvable."})
        except Exception as e:
            raise serializers.ValidationError({"detail": str(e)})
            

class OnEleve(generics.RetrieveAPIView):
    queryset = Eleve.objects.all()
    serializer_class = EleveSerializers
    lookup_field = 'pk'
    
class EleveUpdate(generics.UpdateAPIView):
    queryset = Eleve.objects.all()
    serializer_class = EleveSerializers
    parser_classes = (MultiPartParser, FormParser)
    lookup_field = 'pk'
    
    def perform_update(self, serializer):
        with transaction.atomic():
            # 1. Sauvegarde des données de base de l'élève
            eleve = serializer.save()
            
            # 2. Synchronisation avec le compte User (Statut actif)
            if eleve.user:
                user = eleve.user
                eleve.user.is_active = eleve.is_active
                mdp = self.request.data.get("password")
                if mdp and mdp != "":
                    user.password = mdp
                user.save()

            # 3. Gestion de la Photo
            photo = self.request.FILES.get("photo")
            if photo:
                # On cherche si une photo de profil existe déjà
                doc_photo = DocumentEleve.objects.filter(eleve=eleve, titre="Photo de profil").first()
                if doc_photo:
                    # On remplace le fichier existant
                    doc_photo.fichier = photo
                    doc_photo.save()
                else:
                    # On crée une nouvelle entrée si elle n'existait pas
                    DocumentEleve.objects.create(
                        eleve=eleve,
                        titre="Photo de profil",
                        fichier=photo,
                        type_fichier="IMAGE"
                    )
    
class EleveDestroy(generics.DestroyAPIView):
    queryset = Eleve.objects.all()
    serializer_class = EleveSerializers
    lookup_field = 'pk'
# -----------------------Eleve end---------------------------------------
# -----------------------Matiere start---------------------------------------
class MatiereList(generics.ListAPIView):
    queryset = Matiere.objects.all()
    serializer_class = MatiereSerializers
    
class CreatMatiere(generics.CreateAPIView):
    queryset = Matiere.objects.all()
    serializer_class = MatiereSerializers
    
    def perform_create(self, serializer):
        nom = self.request.data.get("nom")
        code = self.request.data.get("code")

        # Vérification d'unicité globale
        if Matiere.objects.filter(nom__iexact=nom).exists():
            raise serializers.ValidationError({"nom": "Cette matière existe déjà dans le catalogue."})
        
        if code and Matiere.objects.filter(code__iexact=code).exists():
            raise serializers.ValidationError({"code": "Ce code matière est déjà utilisé."})
        
        serializer.save()

class OnMatiere(generics.RetrieveAPIView):
    queryset = Matiere.objects.all()
    serializer_class = MatiereSerializers
    lookup_field = 'pk'
    
class MatiereUpdate(generics.UpdateAPIView):
    queryset = Matiere.objects.all()
    serializer_class = MatiereSerializers
    lookup_field = 'pk'
    
class MatiereDestroy(generics.DestroyAPIView):
    queryset = Matiere.objects.all()
    serializer_class = MatiereSerializers
    lookup_field = 'pk'
# -----------------------Matiere end---------------------------------------
# -----------------------Poste start---------------------------------------
class PosteList(generics.ListAPIView):
    queryset = Poste.objects.all()
    serializer_class = PosteSerializers
    
class CreatPoste(generics.CreateAPIView):
    queryset = Poste.objects.all()
    serializer_class = PosteSerializers
    
    def perform_create(self, serializer):
        nom = self.request.data.get("nom")
        code = self.request.data.get("code")

        # Unicité du nom et du code dans le catalogue SaaS
        if Poste.objects.filter(nom__iexact=nom).exists():
            raise serializers.ValidationError({"nom": "Ce poste existe déjà dans le référentiel."})
        
        if code and Poste.objects.filter(code__iexact=code).exists():
            raise serializers.ValidationError({"code": "Ce code de poste est déjà attribué."})
        
        serializer.save()

class OnPoste(generics.RetrieveAPIView):
    queryset = Poste.objects.all()
    serializer_class = PosteSerializers
    lookup_field = 'pk'
    
class PosteUpdate(generics.UpdateAPIView):
    queryset = Poste.objects.all()
    serializer_class = PosteSerializers
    lookup_field = 'pk'
    
class PosteDestroy(generics.DestroyAPIView):
    queryset = Poste.objects.all()
    serializer_class = PosteSerializers
    lookup_field = 'pk'
# -----------------------Poste end---------------------------------------
# -----------------------Staff start---------------------------------------
class StaffList(generics.ListAPIView):
    queryset = Staff.objects.select_related('poste').all()
    serializer_class = StaffSerializers
    
class CreatStaff(generics.CreateAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializers
    parser_classes = (MultiPartParser, FormParser) # Pour gérer l'upload de photo

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

class OnStaff(generics.RetrieveAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializers
    lookup_field = 'pk'
    
class StaffUpdate(generics.UpdateAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializers
    parser_classes = (MultiPartParser, FormParser)
    lookup_field = 'pk'
    
    def perform_update(self, serializer):
        with transaction.atomic():
            # On sauvegarde les modifications de l'enseignant
            staff = serializer.save()
            
            # 1. Mise à jour de l'email dans le compte User
            # Si l'email est envoyé dans la requête, on met à jour le User lié
            new_email = self.request.data.get("email")
            if new_email and staff.user:
                user = staff.user
                user.email = new_email
                user.username = new_email  # Puisque le staff se connecte avec son email
                
            user.is_active = staff.is_active
            user.save()
            
            # 2. Mise à jour de la table de liaison 'Occupe' (Salaire, Poste, etc.)
            # On récupère l'occupation actuelle du staff
            occupe = Occupe.objects.filter(staff=staff).first()
            if occupe:
                if "idPost" in self.request.data:
                    occupe.poste_id = self.request.data.get("idPost")
                if "salaire" in self.request.data:
                    occupe.salaire = self.request.data.get("salaire")
                if "idEtat" in self.request.data:
                    occupe.etablissement_id = self.request.data.get("idEtat")
                occupe.save()
                
            # 3. Gestion de la Photo
            photo = self.request.FILES.get("photo")
            if photo:
                doc_photo = DocumentStaff.objects.filter(staff=staff, titre="Photo de profil").first()
                if doc_photo:
                    doc_photo.fichier = photo
                    doc_photo.save()
                else:
                    DocumentStaff.objects.create(
                        staff=staff,
                        titre="Photo de profil",
                        fichier=photo,
                        type_fichier="IMAGE"
                    )
    
class StaffDestroy(generics.DestroyAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializers
    lookup_field = 'pk'
# -----------------------Staff end---------------------------------------
# -----------------------Classe start---------------------------------------
class ClasseList(generics.ListAPIView):
    queryset = Classe.objects.all()
    serializer_class = ClasseSerializers
    
class CreatClasse(generics.CreateAPIView):
    queryset = Classe.objects.all()
    serializer_class = ClasseSerializers
    
    def perform_create(self, serializer):
        nom = self.request.data.get("nom")
        code = self.request.data.get("code")

        # Vérification globale pour le catalogue
        if Classe.objects.filter(nom__iexact=nom).exists():
            raise serializers.ValidationError({"nom": "Cette classe existe déjà dans le catalogue central."})
        
        if code and Classe.objects.filter(code__iexact=code).exists():
            raise serializers.ValidationError({"code": "Ce code de classe est déjà utilisé."})
        
        serializer.save()

class OnClasse(generics.RetrieveAPIView):
    queryset = Classe.objects.all()
    serializer_class = ClasseSerializers
    lookup_field = 'pk'
    
class ClasseUpdate(generics.UpdateAPIView):
    queryset = Classe.objects.all()
    serializer_class = ClasseSerializers
    lookup_field = 'pk'
    
class ClasseDestroy(generics.DestroyAPIView):
    queryset = Classe.objects.all()
    serializer_class = ClasseSerializers
    lookup_field = 'pk'
# -----------------------Classe end---------------------------------------
# -----------------------Cour start---------------------------------------
class CourList(generics.ListAPIView):
    queryset = Cour.objects.select_related('enseignant', 'matiere', 'classe').all()
    serializer_class = CoursSerializers
    
class CreatCour(generics.CreateAPIView):
    queryset = Cour.objects.select_related('enseignant', 'matiere', 'classe').all()
    serializer_class = CoursSerializers
    
    @transaction.atomic
    def perform_create(self, serializer):
        data = self.request.data
        etab_id = self.request.data.get("etablissement")
        classe_id = self.request.data.get("classe")
        matiere_id = self.request.data.get("matiere")
        ens_id = self.request.data.get("enseignant")
        annee_id = data.get("annee_scolaire") # On récupère l'année

        # 1. Vérification : L'enseignant doit être lié à cet établissement (via Enseigne)
        if not Enseigne.objects.filter(enseignant_id=ens_id, etablissement_id=etab_id).exists():
            raise serializers.ValidationError({
                "enseignant": "Cet enseignant n'est pas répertorié dans cet établissement."
            })

        # 2. Éviter les doublons : Une classe ne peut pas avoir deux fois la même matière
        if Cour.objects.filter(id_etab=etab_id, classe_id=classe_id, matiere_id=matiere_id, id_annee=annee_id).exists():
            raise serializers.ValidationError({
                "detail": "Ce cours (Classe + Matière) est déjà configuré dans cet établissement pour cette année scolaire."
            })
            
        # 3. Sauvegarde du Cour
        cour_obj = serializer.save()

        # 4. Ajout automatique de l'Emploi du temps
        horaires = data.get("horaires", [])
        for h in horaires:
            h_debut = h.get("heure_debut")
            h_fin = h.get("heure_fin")
            jour = h.get("jour")
            
            # --- LA LOGIQUE DE CONFLIT CORRIGÉE ---
            # Un conflit existe si (Nouveau_Début < Ancien_Fin) ET (Nouveau_Fin > Ancien_Début)
            conflit_base = EmploiDuTemps.objects.filter(
                jour=jour,
                heure_debut__lt=h_fin, 
                heure_fin__gt=h_debut
            )

            # Test Prof
            if conflit_base.filter(cour__enseignant_id=ens_id).exists():
                raise serializers.ValidationError({"detail": f"L'enseignant est déjà occupé le {jour} de {h_debut} à {h_fin}"})

            # Test Classe
            if conflit_base.filter(cour__classe_id=classe_id).exists():
                raise serializers.ValidationError({"detail": f"La classe est déjà occupée le {jour} de {h_debut} à {h_fin}"})

            # 5. Création via Serializer pour valider les formats de champs
            h_serializer = EmploiDuTempsSerializers(data={
                "cour": cour_obj.id_cours,
                "etablissement": etab_id,
                "jour": jour,
                "heure_debut": h_debut,
                "heure_fin": h_fin,
            })
            
            if h_serializer.is_valid():
                h_serializer.save()
            else:
                raise serializers.ValidationError(h_serializer.errors)
            

class OnCour(generics.RetrieveAPIView):
    queryset = Cour.objects.select_related('enseignant', 'matiere', 'classe').all()
    serializer_class = CoursSerializers
    lookup_field = 'pk'
    
class CourUpdate(generics.UpdateAPIView):
    queryset = Cour.objects.select_related('enseignant', 'matiere', 'classe').all()
    serializer_class = CoursSerializers
    lookup_field = 'pk'
    
    def perform_update(self, serializer):
        # 1. On récupère l'instance actuelle du cours avant modification
        cour = self.get_object()
        
        # 2. On récupère les nouvelles données (si elles sont fournies)
        # Si elles ne sont pas dans request.data, on garde les valeurs actuelles du cours
        etab_id = self.request.data.get("etablissement", cour.etablissement_id)
        # Utilisation possible de request.data.get("enseignant"):
        # new_ens_id = self.request.data.get("enseignant")
        # ens_id = new_ens_id if new_ens_id is not None else cour.enseignant_id
        ens_id = self.request.data.get("enseignant", cour.enseignant_id)
        classe_id = self.request.data.get("classe", cour.classe_id)
        matiere_id = self.request.data.get("matiere", cour.matiere_id)

        with transaction.atomic():
            # VERIFICATION A : L'enseignant doit appartenir à l'établissement
            if ens_id:
                if not Enseigne.objects.filter(enseignant_id=ens_id, etablissement_id=etab_id).exists():
                    raise serializers.ValidationError({
                        "enseignant": "Ce nouvel enseignant n'est pas répertorié dans cet établissement."
                    })

            # VERIFICATION B : Unicité (Seulement si on change la classe ou la matière)
            # On vérifie qu'un autre cours ne possède pas déjà ce combo (Classe + Matière + Etab)
            check_duplicate = Cour.objects.filter(
                etablissement_id=etab_id, 
                classe_id=classe_id, 
                matiere_id=matiere_id
            ).exclude(id_cours=cour.id_cours) # On exclut le cours actuel de la recherche

            if check_duplicate.exists():
                raise serializers.ValidationError({
                    "detail": "Une autre fiche de cours existe déjà pour ce combo Classe/Matière dans cet établissement."
                })

            # Si tout est OK, on sauvegarde
            serializer.save()
    
class CourDestroy(generics.DestroyAPIView):
    queryset = Cour.objects.select_related('enseignant', 'matiere', 'classe').all()
    serializer_class = CoursSerializers
    lookup_field = 'pk'
# -----------------------Cour end---------------------------------------
# -----------------------Disponible start---------------------------------------
class DisponibleList(generics.ListAPIView):
    queryset = Disponible.objects.select_related('etablissement', 'classe').all()
    serializer_class = DisponibleSerializers
    
class CreatDisponible(generics.CreateAPIView):
    queryset = Disponible.objects.select_related('etablissement', 'classe').all()
    serializer_class = DisponibleSerializers
    
    def perform_create(self, serializer):
        etab_id = self.request.data.get("etablissement")
        classe_id = self.request.data.get("classe")

        # Vérification : Est-ce que cette classe est déjà activée pour cette école ?
        if Disponible.objects.filter(etablissement_id=etab_id, classe_id=classe_id).exists():
            raise serializers.ValidationError({
                "detail": "Cette classe fait déjà partie des classes disponibles pour cet établissement."
            })
        
        serializer.save()

class OnDisponible(generics.RetrieveAPIView):
    queryset = Disponible.objects.select_related('etablissement', 'classe').all()
    serializer_class = DisponibleSerializers
    lookup_field = 'pk'
    
class DisponibleUpdate(generics.UpdateAPIView):
    queryset = Disponible.objects.select_related('etablissement', 'classe').all()
    serializer_class = DisponibleSerializers
    lookup_field = 'pk'
    
class DisponibleDestroy(generics.DestroyAPIView):
    queryset = Disponible.objects.select_related('etablissement', 'classe').all()
    serializer_class = DisponibleSerializers
    lookup_field = 'pk'
# -----------------------Disponible end---------------------------------------
# -----------------------Enseigne start TABLE INTERMEDIAIRE ENSEIGNANT ET ECOLE---------------------------------------
class EnseigneList(generics.ListAPIView):
    queryset = Enseigne.objects.select_related('etablissement', 'enseignant').all()
    serializer_class = EnseigneSerializers
    
class CreatEnseigne(generics.CreateAPIView):
    queryset = Enseigne.objects.select_related('etablissement', 'enseignant').all()
    serializer_class = EnseigneSerializers

class OnEnseigne(generics.RetrieveAPIView):
    queryset = Enseigne.objects.select_related('etablissement', 'enseignant').all()
    serializer_class = EnseigneSerializers
    lookup_field = 'pk'
    
class EnseigneUpdate(generics.UpdateAPIView):
    queryset = Enseigne.objects.select_related('etablissement', 'enseignant').all()
    serializer_class = EnseigneSerializers
    lookup_field = 'pk'
    
class EnseigneDestroy(generics.DestroyAPIView):
    queryset = Enseigne.objects.select_related('etablissement', 'enseignant').all()
    serializer_class = EnseigneSerializers
    lookup_field = 'pk'
# -----------------------Enseigne end TABLE INTERMEDIAIRE ENSEIGNANT ET ECOLE---------------------------------------
# -----------------------Inscrit start TABLE INTERMEDIAIRE ELEVE ET ECOLE---------------------------------------
class InscritList(generics.ListAPIView):
    queryset = Inscrit.objects.select_related('etablissement', 'eleve', 'classe').all()
    serializer_class = InscritSerializers
    
class CreatInscrit(generics.CreateAPIView):
    queryset = Inscrit.objects.select_related('etablissement', 'eleve', 'classe').all()
    serializer_class = InscritSerializers

class OnInscrit(generics.RetrieveAPIView):
    queryset = Inscrit.objects.select_related('etablissement', 'eleve', 'classe').all()
    serializer_class = InscritSerializers
    lookup_field = 'pk'
    
class InscritUpdate(generics.UpdateAPIView):
    queryset = Inscrit.objects.select_related('etablissement', 'eleve', 'classe').all()
    serializer_class = InscritSerializers
    lookup_field = 'pk'
    
class InscritDestroy(generics.DestroyAPIView):
    queryset = Inscrit.objects.select_related('etablissement', 'eleve', 'classe').all()
    serializer_class = InscritSerializers
    lookup_field = 'pk'
# -----------------------Inscrit end TABLE INTERMEDIAIRE ELEVE ET ECOLE---------------------------------------
#========================== PRESENCE =================================================
class PresenceListCreateView(generics.ListCreateAPIView):
    queryset = Presence.objects.all()
    serializer_class = PresenceSerializers
    
class CreatPresence(generics.CreateAPIView):
    queryset = Presence.objects.all()
    serializer_class = PresenceSerializers

    def perform_create(self, serializer):
        eleve_id = self.request.data.get("eleve")
        cour_id = self.request.data.get("cour")
        date_presence = self.request.data.get("date")

        # 1. Vérification : L'élève est-il bien inscrit dans la classe de ce cours ?
        # (Sécurité pour éviter de marquer présent un élève d'une autre classe)
        cour_obj = Cour.objects.get(id_cours=cour_id)
        if not Inscrit.objects.filter(eleve=eleve_id, classe=cour_obj.classe).exists():
            raise serializers.ValidationError({
                "eleve": "Cet élève n'appartient pas à la classe de ce cours."
            })

        # 2. Gestion de la mise à jour automatique : 
        # Si on renvoie une présence pour le même jour/élève/cours, on écrase l'ancienne
        existing = Presence.objects.filter(eleve=eleve_id, cour=cour_id, date=date_presence).first()
        if existing:
            serializer.instance = existing # On dit à DRF de mettre à jour au lieu de créer
        
        serializer.save()
 
class PresenceUpdate(generics.UpdateAPIView):
    queryset = Presence.objects.all()
    serializer_class = PresenceSerializers
    lookup_field = 'pk'

    def perform_update(self, serializer):
        presence_actuelle = self.get_object()
        
        # On récupère les nouvelles données ou on garde les anciennes
        nouveau_status = self.request.data.get("status", presence_actuelle.status)
        nouveau_commentaire = self.request.data.get("commentaire", presence_actuelle.commentaire)
        
        # Sécurité : On peut empêcher la modification d'une présence 
        # si elle date de plus de 48h (selon la politique de l'école)
        if presence_actuelle.date < datetime.date.today() - datetime.timedelta(days=2):
            # Optionnel : décommenter si tu veux verrouiller l'historique
            raise serializers.ValidationError({"detail": "Impossible de modifier une présence de plus de 48h."})
            #pass

        # Sauvegarde
        serializer.save(
            status=nouveau_status,
            commentaire=nouveau_commentaire
        )   
class PresenceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Presence.objects.all()
    serializer_class = PresenceSerializers
    lookup_field = 'pk'
    
class PresenceDestroy(generics.DestroyAPIView):
    queryset = Presence.objects.all()
    serializer_class = PresenceSerializers
    lookup_field = 'pk'

#========================== INTERROGATION =================================================
# class InterrogationListCreateView(generics.ListCreateAPIView):
#     queryset = Interrogation.objects.all()
#     serializer_class = InterrogationSerializers
    
# class InterrogationDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Interrogation.objects.all()
#     serializer_class = InterrogationSerializers
#     lookup_field = 'pk'
    
#========================== DEPENSE =================================================
class DepenseListCreateView(generics.ListCreateAPIView):
    queryset = Depense.objects.all()
    serializer_class = DepenseSerializers
    
class CreatDepense(generics.CreateAPIView):
    queryset = Depense.objects.all()
    serializer_class = DepenseSerializers
    parser_classes = (MultiPartParser, FormParser) # Pour le fichier justificatif

    def perform_create(self, serializer):
        montant = self.request.data.get("montant")
        
        # Validation du montant
        if float(montant) <= 0:
            raise serializers.ValidationError({"montant": "Le montant doit être supérieur à zéro."})
        
        # On peut imaginer récupérer automatiquement l'établissement du Staff connecté
        # (Cette logique sera affinée avec la LoginView)
        serializer.save()
    
class DepenseUpdate(generics.UpdateAPIView):
    queryset = Depense.objects.all()
    serializer_class = DepenseSerializers
    lookup_field = 'pk'
    parser_classes = (MultiPartParser, FormParser)

    def perform_update(self, serializer):
        depense = self.get_object()
        
        # Sécurité : Empêcher la modification si la dépense est trop ancienne
        # (Ex: Plus de 30 jours)
        import datetime
        if depense.date_depense < datetime.date.today() - datetime.timedelta(days=30):
             raise serializers.ValidationError({
                 "detail": "Cette dépense est verrouillée car elle date de plus de 30 jours."
             })

        serializer.save()
        
class DepenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Depense.objects.all()
    serializer_class = DepenseSerializers
    lookup_field = 'pk'
    
class DepenseDestroy(generics.DestroyAPIView):
    queryset = Depense.objects.all()
    serializer_class = DepenseSerializers
    lookup_field = 'pk'
#========================== EVALUATION =================================================
class EvaluationListCreateView(generics.ListCreateAPIView):
    queryset = Evaluation.objects.all()
    serializer_class = EvaluationSerializers
    
class CreatEvaluation(generics.CreateAPIView):
    queryset = Evaluation.objects.all()
    serializer_class = EvaluationSerializers

    def perform_create(self, serializer):
        eleve_id = self.request.data.get("eleve")
        cour_id = self.request.data.get("cour")
        etab_id = self.request.data.get("etablissement")
        
        etab = Etablissement.objects.get(id_etab=etab_id)
        periode = int(self.request.data.get("periode", 0))

        # Validation logique selon le type d'établissement
        if etab.type == 'PUBLIC' and periode > 2:
            raise serializers.ValidationError({
                "periode": "Un établissement public ne peut pas avoir plus de 2 semestres."
            })
        
        if etab.type == 'PRIVE' and periode > 3:
            raise serializers.ValidationError({
                "periode": "Un établissement privé ne peut pas avoir plus de 3 trimestres."
            })

        # 1. Vérification de cohérence : Le cours doit appartenir à cet établissement
        try:
            cour_obj = Cour.objects.get(id_cours=cour_id, id_etab=etab_id)
        except Cour.DoesNotExist:
            raise serializers.ValidationError({"cour": "Ce cours n'existe pas dans cet établissement."})

        # 2. Vérification de l'élève : Est-il bien dans la classe de ce cours ?
        if not Inscrit.objects.filter(id_eleve=eleve_id, classe=cour_obj.classe, id_etab=etab_id).exists():
            raise serializers.ValidationError({"eleve": "Cet élève n'est pas inscrit dans la classe correspondant à ce cours."})

        serializer.save()
    
class OnEvaluation(generics.RetrieveAPIView):
    queryset = Evaluation.objects.all()
    serializer_class = EvaluationSerializers
    lookup_field = 'pk'
    
class EvaluationUpdate(generics.UpdateAPIView):
    queryset = Evaluation.objects.all()
    serializer_class = EvaluationSerializers
    lookup_field = 'pk'

    def perform_update(self, serializer):
        evaluation = self.get_object()
        etab = evaluation.etablissement
        
        # On récupère la période envoyée ou celle existante
        periode = int(self.request.data.get("periode", evaluation.periode))
        
        # Validation logique selon le type d'établissement
        if etab.type == 'PUBLIC' and periode > 2:
            raise serializers.ValidationError({
                "periode": "Un établissement public ne peut pas avoir plus de 2 semestres."
            })
        
        if etab.type == 'PRIVE' and periode > 3:
            raise serializers.ValidationError({
                "periode": "Un établissement privé ne peut pas avoir plus de 3 trimestres."
            })
        
        # On s'assure que si on change l'élève ou le cours, la cohérence est maintenue
        eleve_id = self.request.data.get("eleve", evaluation.eleve)
        cour_id = self.request.data.get("cour", evaluation.cour)
        
        if eleve_id != evaluation.eleve or cour_id != evaluation.cour:
            cour_obj = Cour.objects.get(id_cours=cour_id)
            if not Inscrit.objects.filter(id_eleve=eleve_id, classe=cour_obj.classe).exists():
                raise serializers.ValidationError({"detail": "Incohérence entre l'élève et la classe du cours."})

        serializer.save()
    
class EvaluationDestroy(generics.DestroyAPIView):
    queryset = Evaluation.objects.all()
    serializer_class = EvaluationSerializers
    lookup_field = 'pk'
    
#========================== EMPLOI DU TEMPS =================================================
class EmploiDuTempsListCreateView(generics.ListCreateAPIView):
    queryset = EmploiDuTemps.objects.all()
    serializer_class = EmploiDuTempsSerializers
class CreatEmploiDuTemps(generics.CreateAPIView):
    queryset = EmploiDuTemps.objects.all()
    serializer_class = EmploiDuTempsSerializers

    def perform_create(self, serializer):
        cour_id = self.request.data.get("cour")
        jour = self.request.data.get("jour")
        h_debut = self.request.data.get("heure_debut")
        h_fin = self.request.data.get("heure_fin")
        
        # Récupérer le cours pour connaître le prof et la classe
        nouveau_cour = Cour.objects.get(id_cours=cour_id)
        prof = nouveau_cour.enseignant
        classe = nouveau_cour.classe

        # VERIFICATION : Le prof est-il déjà occupé ?
        conflit_prof = EmploiDuTemps.objects.filter(
            cour__enseignant=prof,
            jour=jour,
            heure_debut__lt=h_fin, # Commence avant que le nouveau cours finisse
            heure_fin__gt=h_debut   # Finit après que le nouveau cours commence
        ).exists()

        if conflit_prof:
            raise serializers.ValidationError({"detail": "Cet enseignant a déjà un cours sur ce créneau."})

        # VERIFICATION : La classe est-elle déjà occupée ?
        conflit_classe = EmploiDuTemps.objects.filter(
            cour__classe=classe,
            jour=jour,
            heure_debut__lt=h_fin,
            heure_fin__gt=h_debut
        ).exists()

        if conflit_classe:
            raise serializers.ValidationError({"detail": "Cette classe a déjà un autre cours prévu à cette heure."})

        serializer.save(etablissement=nouveau_cour.etablissement)

class OnEmploiDuTemps(generics.RetrieveAPIView):
    queryset = EmploiDuTemps.objects.all()
    serializer_class = EmploiDuTempsSerializers
    lookup_field = 'pk'
    
class EmploiDuTempsUpdate(generics.UpdateAPIView):
    queryset = EmploiDuTemps.objects.all()
    serializer_class = EmploiDuTempsSerializers
    lookup_field = 'pk'

    def perform_update(self, serializer):
        instance = self.get_object()
        
        # On récupère les nouvelles données ou on garde les anciennes
        jour = self.request.data.get("jour", instance.jour)
        h_debut = self.request.data.get("heure_debut", instance.heure_debut)
        h_fin = self.request.data.get("heure_fin", instance.heure_fin)
        
        # On récupère le cours (lié à l'enseignant et à la classe)
        cour = instance.cour 

        # Vérification des conflits en EXCLUANT l'ID actuel (.exclude(pk=instance.pk))
        conflit = EmploiDuTemps.objects.filter(
            jour=jour,
            heure_debut__lt=h_fin,
            heure_fin__gt=h_debut
        ).exclude(pk=instance.pk).filter(
            models.Q(cour__enseignant=cour.enseignant) | 
            models.Q(cour__classe=cour.classe)
        ).exists()

        if conflit:
            raise serializers.ValidationError({
                "detail": "Modification impossible : conflit d'horaire pour l'enseignant ou la classe."
            })

        serializer.save()

class EmploiDuTempsDestroy(generics.DestroyAPIView):
    queryset = EmploiDuTemps.objects.all()
    serializer_class = EmploiDuTempsSerializers
    lookup_field = 'pk'
    
#========================== DASHBOARD ELEVE =================================================
class EleveDashboardView(APIView):
    def get(self, request, id_eleve):
        # On récupère l'année envoyée par le frontend (ex: via query params ?annee=UUID)
        id_annee = request.query_params.get('annee')
        
        try:
            # Récupération de l'inscription pour l'année choisie
            inscription = Inscrit.objects.select_related(
                'eleve', 'etablissement', 'classe', 'annee_scolaire'
            ).get(eleve=id_eleve, annee_scolaire=id_annee)
        except Inscrit.DoesNotExist:
            return Response({"error": "Aucune donnée pour cette année scolaire."}, status=404)
        
        # Raccourcis
        classe = inscription.classe
        annee = inscription.annee_scolaire
        etab = inscription.etablissement
        
        # --- 1. PROFIL COMPLET ---
        # On envoie les objets sérialisés (ou leurs dictionnaires)
        profil = {
            # "eleve": inscription.eleve,
            # "etablissement": etab,
            # "classe": classe,
            # "annee_scolaire": annee,
            "eleve": EleveSerializers(inscription.eleve).data,
            "etablissement": EtablissementSerializers(etab).data,
            "classe": ClasseSerializers(classe).data,
            "annee_scolaire": AnneeScolaireSerializers(annee).data,
        }
        
        # --- 2. EMPLOI DU TEMPS COMPLET ---
        # On récupère tous les créneaux de la classe pour cette année
        emploi_du_temps = EmploiDuTemps.objects.filter(
            cour__classe=classe, 
            cour__annee_scolaire=annee
        ).select_related('cour__matiere').order_by('jour', 'heure_debut')
        
        # --- 3. LOGIQUE DES EVALUATIONS (Le gros morceau) ---
        resultats = []
        cours_de_la_classe = Cour.objects.filter(classe=classe, annee_scolaire=annee).select_related('matiere', 'enseignant')

        for cours in cours_de_la_classe:
            # On regroupe par période (Trimestre 1, 2, 3 ou Semestre 1, 2)
            evals_par_periode = []
            
            # On suppose que le modèle Evaluation a un champ 'periode' (ex: 'T1', 'S1')
            # On récupère les périodes où l'élève a au moins une note
            periodes = Evaluation.objects.filter(cour=cours, eleve=id_eleve).values_list('periode', flat=True).distinct()

            somme_moyennes_periodes = 0
            count_periodes = 0

            for periode in periodes:
                # Recuperer tout le note de l'eleve pour ce cours et cette periode
                #recuperer les note de typeEval = INTERRO
                interros = Evaluation.objects.filter(
                    eleve=id_eleve, cour=cours, periode=periode, typeEval='INTERRO'
                )
                
                #recuperer les note de typeEval = DEVOIR
                devoirs = Evaluation.objects.filter(
                    eleve=id_eleve, cour=cours, periode=periode, typeEval='DEVOIR'
                )
                
                # Moyenne Interrogations
                moy_interro = interros.aggregate(Avg('note'))['note__avg'] or 0

                # Moyenne Devoirs
                moy_devoir =devoirs.aggregate(Avg('note'))['note__avg'] or 0

                # Moyenne de la période pour ce cours (Ex: (Interro + Devoir) / 2)
                moyenne_periode = (moy_interro + moy_devoir * 2) / 2 if (moy_interro and moy_devoir) else (moy_interro or moy_devoir)

                evals_par_periode.append({
                    "interros": EvaluationSerializers(interros, many=True).data,
                    "devoirs": EvaluationSerializers(devoirs, many=True).data,
                    "periode": periode,
                    "moyenne_interro": round(moy_interro, 2),
                    "moyenne_devoir": round(moy_devoir, 2),
                    "moyenne_periode": round(moyenne_periode, 2)
                })
                somme_moyennes_periodes += moyenne_periode
                count_periodes += 1

            # Calcul final pour le cours avec Coefficient
            moyenne_finale_cours = somme_moyennes_periodes / count_periodes if count_periodes > 0 else 0
            
            resultats.append({
                "cours": CoursSerializers(cours).data,
                "evaluations_details": evals_par_periode,
                "moyenne_du_cours": round(moyenne_finale_cours, 2), #moyenne en fonctionne des periodes (ex: T1, T2, T3; S1, S2)
                "points_coefficientes": round(moyenne_finale_cours * cours.matiere.coefficient, 2)
            })

        data = {
            "profil": profil,
            "emploi_du_temps": EmploiDuTempsSerializers(emploi_du_temps, many=True).data,
            "resultats_scolaires": resultats
        }
        
        return Response(data, status=status.HTTP_200_OK)

#========================== DASHBOARD ENSEIGNANT =================================================
        
