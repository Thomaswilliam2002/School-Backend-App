from django.shortcuts import render
from rest_framework import generics, status, serializers
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, Q, FloatField, ExpressionWrapper, F
from django.db import transaction # Importez le module de transaction
from django.db.models import Avg
from django.db.models.expressions import RawSQL
from .models import *
from .serializers import *
import random
import string
from django.db import transaction
from datetime import datetime, date
from django.core.mail import send_mail
from django.conf import settings
from smtplib import SMTPRecipientsRefused, SMTPAuthenticationError
from django.contrib.auth import get_user_model, authenticate
from django.utils.crypto import get_random_string
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from itertools import groupby
import json
from collections import defaultdict

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
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print(self.request.data)
        User = get_user_model()
        
        def generate_code():
            while True:
                suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                code = f"ETAB-{suffix}"
                if not Etablissement.objects.filter(code=code).exists():
                    return code
        
        #print(self.request.data)
        email = self.request.data.get('email')
        if not email or email == "":
            return Response({"flag": "bad",
                                "message": "L'email est requis pour confirmer l'inscription."},
                                status=status.HTTP_400_BAD_REQUEST
                            )
            
        if User.objects.filter(email=email).exists():
            return Response({"flag": "bad",
                                "message": "Un compte existe déjà avec cet email. Choissez un autre email."},
                                status=status.HTTP_400_BAD_REQUEST
                            )
            
        #recuperation du poste
        poste = Poste.objects.filter(code="DIRECTION").first()
        if not poste:
            return Response({"flag": "bad",
                        "message": "Une erreur s'est produite (POSTE). Veuillez contacter l'administration ou le service technique de UNCHAIN"},
                        status=status.HTTP_400_BAD_REQUEST)
        try:
            # 1. Génération d'un code unique
            # Génère un code type ETAB-7812
            code = generate_code()
            
            with transaction.atomic():
                # 2. Sauvegarde; Transaction BD
                instance = serializer.save(code=code.upper())
                # Ajouter le staff(directeur) de l'etablisement; lui cree un compte par defaut et lui envoyer les infos de connexion
                
                # 2️⃣ Création du mot de passe par défaut
                raw_password = get_random_string(8)
                
                # 3️⃣ Création du compte utilisateur
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=raw_password
                )
                
                # 3️⃣ Création du staff (directeur)
                staff = Staff.objects.create(
                    user=user,
                    nom = f"Directeur {instance.nom}",
                    status="DIRECTEUR",
                )
                
                # 5️⃣ Lien staff ↔ établissement
                Occupe.objects.create(
                    staff=staff,
                    etablissement=instance,
                    poste=poste,
                    salaire=0,
                    date_debut = timezone.now().date(), #self.request.data.get('dateDebut'),
                    # annee_scolaire=annee,
                )
                
                # Envoi de l'email de confirmation
                transaction.on_commit(lambda: send_mail(
                    "UNCHAIN School App",
                    f"Votre Etablissement a bien été inscrit avec succès.\n Voici vos informations de connexion :\n\nNom d'utilisateur : {email}\nMot de passe : {raw_password}\nCode de l'Etablissement : {code}.\n\nCordialement,\nL'administration de UNCHAIN School App",
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                ))
                
            return Response({
                "message": "Inscription réussie ! Un mail a été envoyé.\nVeuillez consulter votre boite de reception.",
                "etablissement": serializer.data
            }, status=status.HTTP_201_CREATED)
                
        except SMTPRecipientsRefused:
            return Response({
                "flag": "bad",
                "message": "L'adresse email est refusée ou inexistante. Inscription annulée.",
            }, status=status.HTTP_400_BAD_REQUEST)
        #except SMTPAuthenticationError:
        except Exception as e:
            # Ici, 'e' contient la cause du fail
            error_message = str(e)
            print(e)
            # On peut même être plus précis sur le type d'erreur
            if "Authentication failed" in error_message:
                detail = "Le serveur de mail a refusé les identifiants (mot de passe d'application ?)"
            elif "Connection refused" in error_message:
                detail = "Impossible de contacter le serveur SMTP (Port bloqué ou mauvais hôte)"
            else:
                detail = f"Erreur technique : {error_message}"

            raise serializers.ValidationError({"email_error": detail})

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
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        User = get_user_model()
        
        email = self.request.data.get('email')
        if not email or email == "":
            return Response({"flag": "bad",
                                "message": "L'email est requis pour l'inscription. Veillez renseigner une adresse email."},
                                status=status.HTTP_400_BAD_REQUEST
                            )
            
        if User.objects.filter(email=email).exists():
            return Response({"flag": "bad",
                                "message": "Un compte existe déjà avec cet email. Choissez un autre email."},
                                status=status.HTTP_400_BAD_REQUEST
                            )
            
        # 1. Récupération des données nécessaires
        etab_id = self.request.data.get("idEtat")
        photo = self.request.FILES.get("photo")
        annee_scolaire = self.request.data.get("annee_scolaire")
        salaire = self.request.data.get("salaire")
        
        etablissement = Etablissement.objects.filter(id_etab=etab_id).first()
        if not etab_id:
            return Response({"flag": "bad",
                                "message": "Impossible d'effectuer l'inscription. L'ÉTABLISSEMENT n'existe pas. Reessayez. Si le problème persiste, contacter l'administrateur."},
                                status=status.HTTP_400_BAD_REQUEST
                            )
        
        annee = AnneeScolaire.objects.filter(nom=annee_scolaire, is_active=True, etablissement=etablissement).first()
        
        if salaire == 0:
            return Response({"flag": "bad",
                                "message": "Un salaire est requis pour l'inscription. Veuillez renseigner un salaire. Le salaire doit etre superieur a 0."},
                                status=status.HTTP_400_BAD_REQUEST
                            )
        
        if not annee:
            return Response({"flag": "bad",
                                "message": "Impossible d'effectuer l'inscription. L'ANNEE SCOLAIRE n'existe pas ou est invalide. Reessayez. Si le problème persiste, contacter l'administrateur."},
                                status=status.HTTP_400_BAD_REQUEST
                            )
        
        try:
            with transaction.atomic():
                # CRÉATION DE L'UTILISATEUR
                # L'email sert d'identifiant (username) et l'email de contact
                # On génère un mot de passe temporaire ou on en demande un
                temp_password = "Ens@" + "".join(random.choices(string.digits, k=4))
                
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=temp_password
                )

                # CRÉATION DE L'ENSEIGNANT (lié au User)
                enseignant = serializer.save(user=user)

                # RATTACHEMENT À L'ÉTABLISSEMENT (Table Enseigne)
                etablissement = Etablissement.objects.get(id_etab=etab_id)
                
                # On crée le lien dans la table de liaison Enseigne
                Enseigne.objects.create(
                    enseignant=enseignant,
                    etablissement=etablissement,
                    annee_scolaire= annee,
                    type = self.request.data.get("type"),
                    salaire = salaire,
                    periode = self.request.data.get("periode")
                )

                #GESTION DE LA PHOTO / DOCUMENTS
                if photo:
                    doc = DocumentEnseignant.objects.create(
                        enseignant=enseignant,
                        titre="Photo de profil",
                        nom_fichier= "photo_profil",
                        # fichier=photo,
                        type_fichier="IMAGE"
                    )
                    
                    doc.fichier = photo
                    doc.save()
                
            # C'est ici que tu pourrais appeler une fonction send_mail() 
            # pour envoyer ses accès à l'enseignant.
            send_mail(
                "UNCHAIN School App",
                f"Vous venez d'etre ajouté en tant qu'enseignant au sein de l'Etablissement {etablissement.nom}.\n Voici vos informations de connexion :\n\n email : {email}\n mot de passe : {temp_password}\n\nCordialement,\nL'administration de l'Etablissement.",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False
            )
                
            return Response({"message": "L'enseignant a bien été ajouter. Un email de confirmation vous a été envoyé."}, status=status.HTTP_201_CREATED)

        except Etablissement.DoesNotExist:
            raise serializers.ValidationError({"idEtat": "Établissement introuvable."})
        except Etablissement.DoesNotExist:
            raise serializers.ValidationError({"idEtat": "L'établissement spécifié est introuvable."})
        except Classe.DoesNotExist:
            raise serializers.ValidationError({"classe": "La classe spécifiée est introuvable."})
        except Exception as e:
            print(e)
            return Response({"message": "Une erreur s'est produite. Verifierez les données envoyées. Veuillez contacter l'administrateur si le problème persiste."}, status=status.HTTP_400_BAD_REQUEST)

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
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        def validate_optional_email(email, label, emails_list):
            if email:
                validate_email(email)
                emails_list.append(email)
            else:
                return Response(
                    {"message": "L'email du {label} n'est pas valide"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        def generate_matricule():
            year = datetime.now().year
            while True:
                suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                matricule = f"EL{year}{suffix}"
                if not Eleve.objects.filter(matricule=matricule).exists():
                    return matricule
                
        User = get_user_model()
        
        # On récupère les données supplémentaires envoyées dans la requête
        etab_id = self.request.data.get("idEtat")
        classe_id = self.request.data.get("classe")
        annee_scolaire_nom = self.request.data.get("anneeScolaire")
        photo = self.request.FILES.get("photo")
        
        # Sécurité : Vérification avant de commencer la transaction
        if not etab_id or not classe_id:
            return Response({"message": "Une erreur s'est produite. Verifierez les données envoyées. Veuillez contacter l'administrateur si le problème persiste."}, status=status.HTTP_400_BAD_REQUEST)
        
        #verifier que l'annee scolaire est correcte
        annee_scolaire = AnneeScolaire.objects.filter(nom=annee_scolaire_nom, etablissement_id=etab_id).first()
        if not annee_scolaire:
            return Response({"message": "L'annee scolaire n'existe pas.Une erreur s'est produite. Verifierez les données envoyées. Veuillez contacter l'administrateur si le problème persiste."}, status=status.HTTP_400_BAD_REQUEST)
        
        #veerifier si la classe est disponible
        dispo = Disponible.objects.filter(etablissement_id=etab_id, id_disponible=classe_id, annee_scolaire=annee_scolaire).first()
        if not dispo:
            return Response({"message": "La classe est indisponible. Veuillez contacter l'administrateur si le problème persiste."}, status=status.HTTP_400_BAD_REQUEST)
        
        etablissement = Etablissement.objects.filter(id_etab=etab_id).first()
        if not etablissement:
            return Response({"message": "L'etablissement n'existe pas. Veuillez contacter l'administrateur si le problème persiste."}, status=status.HTTP_400_BAD_REQUEST)
        
        #verification des emails des parents
        email_parent_1 = self.request.data.get('email_parent_1')
        email_parent_2 = self.request.data.get('email_parent_2')
        listEmail = []
        
        try:
            validate_optional_email(email_parent_1, "parent 1", listEmail)
            validate_optional_email(email_parent_2, "parent 2", listEmail)
        except ValidationError as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            
            # 1. GÉNÉRATION DU MATRICULE (Username)
            # Format: EL + Année + 4 caractères aléatoires (ex: EL2024X8P1)
            matricule = generate_matricule()
                    
            # Utilisation de transaction.atomic pour garantir l'intégrité
            with transaction.atomic():
                # 2. CRÉATION DU COMPTE UTILISATEUR
                # Le matricule sert d'identifiant ET de mot de passe par défaut
                user = User.objects.create_user(
                    username=matricule,
                    email = email_parent_1 or email_parent_2 or "",
                    password=matricule 
                )
                
                # 3. SAUVEGARDE DE L'ÉLÈVE (Lié à l'User)
                print("saver")
                eleve = serializer.save(matricule=matricule.upper(), user=user)
                print("save")
                
                
                # 4.1 Création de l'inscription de l'eleve
                Inscrit.objects.create(
                    eleve=eleve,
                    etablissement_id= etab_id,
                    disponible = dispo,
                    annee_scolaire = annee_scolaire
                )
                
                # 5. GESTION DE LA PHOTO
                # On le fait après l'inscription pour que upload_eleve_path 
                # puisse trouver l'établissement !
                if photo:
                    doc = DocumentEleve.objects.create(
                        eleve=eleve,
                        titre="Photo de profil",
                        description=f"Photo de profil de {eleve.nom}",
                        nom_fichier="photo_profil",
                        # fichier=photo,
                        type_fichier="IMAGE"
                    )
                    
                    doc.fichier = photo
                    doc.save()
                    
                # print(listEmail)
                # Optionnel : Tu peux ajouter ici l'envoi d'un SMS ou Email au parent 
                # avec le matricule de l'enfant.
                # Envoi de l'email de confirmation
                transaction.on_commit(lambda: send_mail(
                    "UNCHAIN School App",
                    f"Votre Elève a bien été inscrit avec succès.\n Voici vos informations de connexion :\n\nMatricule : {matricule}\nCode de l'Etablissement : {etablissement.code}.\n\nCordialement,\nL'administration de UNCHAIN School App",
                    settings.DEFAULT_FROM_EMAIL,
                    listEmail,
                    fail_silently=False
                ))
                
            return Response({"message": "L'élève a bien été ajouter."}, status=status.HTTP_201_CREATED)
                    
                    
        except Etablissement.DoesNotExist:
            raise serializers.ValidationError({"idEtat": "L'établissement spécifié est introuvable."})
        except Classe.DoesNotExist:
            raise serializers.ValidationError({"classe": "La classe spécifiée est introuvable."})
        except Exception as e:
            print(e)
            return Response({"message": "Une erreur s'est produite. Verifierez les données envoyées. Veuillez contacter l'administrateur si le problème persiste."}, status=status.HTTP_400_BAD_REQUEST)
            

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
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        nom = self.request.data.get("nom")
        code = self.request.data.get("code")

        # Vérification d'unicité globale
        if Matiere.objects.filter(nom__iexact=nom).exists():
            return Response({"message": "Cette matière existe déjà dans le catalogue."}, status=status.HTTP_400_BAD_REQUEST)
        
        if code and Matiere.objects.filter(code__iexact=code).exists():
            return Response({"message": "Ce code matière est déjà utilisé."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not nom or not code or nom == "" or code == "":
            return Response({"message": "Les champs 'Nom' et 'Code' sont obligatoires."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        return Response({"message": "La matière a bien été ajoutée."}, status=status.HTTP_201_CREATED)

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
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # print(self.request.data)
        
        User = get_user_model()
        
        email = self.request.data.get('email')
        code = self.request.data.get('code')
        mdp = self.request.data.get('mdp')
        photo = self.request.FILES.get("photo")
        poste = self.request.data.get("poste")
            
        try:
            with transaction.atomic():
                # 2. CRÉATION DU COMPTE UTILISATEUR (USER)
                # On vérifie si l'utilisateur existe déjà pour éviter les doublons
                if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
                    return Response({"flag": "bad",
                                "message": "Un compte existe déjà avec cet email. Choissez un autre email."},
                                status=status.HTTP_400_BAD_REQUEST
                            )

                # L'email sert d'identifiant (username) et d'email de contact
                # On génère un mot de passe temporaire ou on en demande un
                # temp_password = "Stf@" + "".join(random.choices(string.digits, k=4))
                
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=mdp
                )
                
                #recuperation du poste
                poste = Poste.objects.filter(id_poste=poste).first()
                if not poste:
                    raise serializers.ValidationError({"poste": "Le poste n'existe pas"})

                # RATTACHEMENT À L'ÉTABLISSEMENT
                etablissement = Etablissement.objects.get(code=code)
                if not etablissement:
                    return Response({"flag": "bad",
                                "message": "Code d'etablissement incorrect. Veillez verifier le code et essayer de nouveau."},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                
                # 3. CRÉATION DU STAFF (lié au User)
                staff = serializer.save(user=user, status=poste.code)

                # On crée le lien dans la table de liaison Occupe
                Occupe.objects.create(
                    staff=staff,
                    etablissement=etablissement,
                    poste = poste,
                    salaire = 0,
                    date_debut = self.request.data.get("dateDebut") or datetime.now().date()
                )

                # 5. GESTION DE LA PHOTO / DOCUMENTS
                if photo:
                    doc = DocumentStaff.objects.create(
                        staff=staff,
                        titre="Photo de profil",
                        nom_fichier="photo_profil",
                        # fichier=photo,
                        type_fichier="IMAGE"
                    )
                    
                    doc.fichier = photo
                    doc.save()
                    
            send_mail(
                "UNCHAIN School App",
                f"Felicitations ! Vous etes inscrit avec succès.\nConnectez-vous et profitez de l'application.\nCordialement,\nL'administration de UNCHAIN School App",
                settings.DEFAULT_FROM_EMAIL,
                [email],
            )
                    
            return Response({
                "message": "Inscription réussie ! Un mail a été envoyé.\nVeuillez consulter votre boite de reception.",
                "etablissement": serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except SMTPRecipientsRefused:
            return Response({
                "flag": "bad",
                "message": "L'adresse email est refusée ou inexistante. Inscription annulée.",
            }, status=status.HTTP_400_BAD_REQUEST)
        except Etablissement.DoesNotExist:
            raise serializers.ValidationError({"idEtat": "Établissement introuvable."})
        except Poste.DoesNotExist:
            raise serializers.ValidationError({"idPoste": "Poste introuvable."})
        except Exception as e:
            # Ici, 'e' contient la cause du fail
            error_message = str(e)
            print(error_message)
            # On peut même être plus précis sur le type d'erreur
            if "Authentication failed" in error_message:
                detail = "Le serveur de mail a refusé les identifiants (mot de passe d'application ?)"
            elif "Connection refused" in error_message:
                detail = "Impossible de contacter le serveur SMTP (Port bloqué ou mauvais hôte)"
            else:
                detail = f"Erreur technique : {error_message}"

            raise serializers.ValidationError({"email_error": detail})

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
# -----------------------niveau start---------------------------------------
class NiveauEtudeList(generics.ListAPIView):
    queryset = NiveauEtude.objects.all()
    serializer_class = NiveauEtudeSerializers
    
class CreatNiveauEtude(generics.CreateAPIView):
    queryset = NiveauEtude.objects.all()
    serializer_class = NiveauEtudeSerializers
    
    def perform_create(self, serializer):
        nom = self.request.data.get("nom")
        # Vérification globale pour le catalogue
        if NiveauEtude.objects.filter(nom=nom).exists():
            raise serializers.ValidationError({"nom": "Ce niveau d'enseignement existe déjà dans le catalogue central."})
        
        serializer.save()
# -----------------------Classe start---------------------------------------
class ClasseList(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        # 1. Récupérer toutes les classes
        all_classes = Classe.objects.all()
        
        # 2. Utiliser un dictionnaire par défaut pour regrouper
        # defaultdict(list) crée automatiquement une liste vide pour chaque nouvelle clé
        classes_regroupees = defaultdict(list)
        
        for classe in all_classes:
            # On utilise le sérialiseur pour avoir les données propres de chaque classe
            serializer = ClasseSerializers(classe)
            
            # On récupère le nom du niveau (ex: "6ème")
            # Assurez-vous que votre modèle Classe a un champ 'niveau_etude'
            niveau = classe.niveau.nom if classe.niveau else "???"
            
            classes_regroupees[niveau].append(serializer.data)
            
        return Response({"message": "Liste des classes recuperer avec success", "data": classes_regroupees})
    
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

class ClasseDisponibleEtablissement(APIView):
    def post(self, request):
        try:
            # 1. Récupérer toutes les classes
            classes_json = request.data.get('classes_details')
            classes_list = json.loads(classes_json)
            etab_id = request.data.get('etablissement')
            annee_scolaire = request.data.get('annee_scolaire')
            annee = AnneeScolaire.objects.filter(nom=annee_scolaire).first()
            etablissement = Etablissement.objects.filter(id_etab=etab_id).first()
            
            for item in classes_list:
                nom_du_niveau = item.get('niveau')
                id_classe = item.get('id_classe')
                montant = item.get('scolarite')
                
                #vrifier si montant inferieur ou egal a 0
                if float(montant) <= 0:
                    return Response({"message": f"La scolarité de la Classe {item.get('nom_classe')} doit etre superieur a 0."}, status=status.HTTP_400_BAD_REQUEST)
                
                #verification de doublon
                d = Disponible.objects.filter(classe=id_classe, annee_scolaire=annee, etablissement=etablissement).first()
                
                if d: # or d.classe.niveau.nom == nom_du_niveau 
                    return Response({"message": f"La Classe {item.get("nom_classe")} est deja disponible."}, status=status.HTTP_400_BAD_REQUEST)
                
                classe = Classe.objects.filter(id_classe=id_classe).first()
                if not classe:
                    return Response({"message": f"Classe {id_classe} introuvable."}, status=status.HTTP_404_NOT_FOUND)
            
                # print(f"Traitement de la classe {id_classe} (Niveau: {nom_du_niveau}) avec scolarité: {montant}")
                
                Disponible.objects.create(
                    classe=classe,
                    scolarite=montant,
                    annee_scolaire=annee,
                    etablissement=etablissement
                )

            return Response({"message": "Classe(s) disponible(s) enregistrée(s) avec succès."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            return Response({"message": "Une erreur s'est produite lors de l'enregistrement de(s) classe(s) disponibles."}, status=status.HTTP_400_BAD_REQUEST)    
        
class ListeClasseDisponibleEtablissement(APIView):
    def get(self, request, id_etab):
        etablissement = Etablissement.objects.filter(id_etab=id_etab).first()
        dispo = Disponible.objects.filter(etablissement=etablissement).all()
        serializer = DisponibleSerializers(dispo, many=True)
        
        return Response({"message": "Liste des classes disponibles recuperer avec success", "data": serializer.data})
    
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
    
# class ClasseDelete(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Classe.objects.all()
#     serializer_class = ClasseSerializers
#     # On indique à DRF d'utiliser cet ID dans l'URL pour trouver l'objet
#     lookup_field = 'id_classe' 

#     def partial_update(self, request, *args, **kwargs):
#         # 1. Récupérer l'objet que l'on souhaite modifier
#         instance = self.get_object()
        
#         # 2. Si vous voulez modifier un modèle lié (ex: Disponible)
#         # Supposons que 'disponible_id' soit passé dans les données ou l'URL
#         try:
#             # On met à jour le champ is_active de l'objet trouvé
#             instance.is_active = False 
#             instance.save()
            
#             # Si vous devez aussi mettre à jour un autre modèle 'Disponible' :
#             # Disponible.objects.filter(id=instance.disponible_id).update(is_active=False)

#             # 3. Retourner la réponse avec le serializer
#             serializer = self.get_serializer(instance, data=request.data, partial=True)
#             serializer.is_valid(raise_exception=True)
#             self.perform_update(serializer)

#             return Response({
#                 "message": "Classe désactivée avec succès",
#                 "data": serializer.data
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
# -----------------------Classe end---------------------------------------
# -----------------------Cour start---------------------------------------
class CourList(generics.ListAPIView):
    queryset = Cour.objects.select_related('enseignant', 'matiere', 'disponible').all()
    serializer_class = CoursSerializers
    
class CreatCour(generics.CreateAPIView):
    queryset = Cour.objects.select_related('enseignant', 'matiere', 'disponible').all()
    serializer_class = CoursSerializers
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            print("ok")
            print(self.request.data)
            etab_id = self.request.data.get("etablissement")
            classe_id = self.request.data.get("classe")
            matiere_id = self.request.data.get("matiere")
            ens_id = self.request.data.get("enseignant")
            annee_scolaire = self.request.data.get("annee_scolaire") # On récupère l'année
            nom = self.request.data.get("nom")
            coef = self.request.data.get("coefficient")
            print(classe_id)

            # 1. Vérification : L'enseignant doit être lié à cet établissement (via Enseigne)
            if not Enseigne.objects.filter(enseignant_id=ens_id, etablissement_id=etab_id).exists():
                return Response({"message": "Cet enseignant n'est pas répertorié dans cet établissement."}, status=status.HTTP_400_BAD_REQUEST)
            
            enseignant = Enseignant.objects.get(id_ens=ens_id)
            
            #si il n'existe pas la matiere
            if not Matiere.objects.filter(id_matiere=matiere_id).exists():
                return Response({"message": "Cette matière n'existe pas ou n'est pas configurée. Veuillez la configurer avant de poursuivre ou contacter l'administrateur."}, status=status.HTTP_400_BAD_REQUEST)
            
            #si il n'existe pas la classe
            if not Disponible.objects.filter(id_disponible=classe_id).exists():
                return Response({"message": "Cette classe n'existe pas ou n'est pas configurée. Veuillez la configurer avant de poursuivre ou contacter l'administrateur."}, status=status.HTTP_400_BAD_REQUEST)

            annee = AnneeScolaire.objects.filter(nom=annee_scolaire).first()
            if not annee:
                return Response({"message": "Cette année scolaire n'existe pas ou n'est pas configurée. Veuillez la configurer avant de poursuivre ou contacter l'administrateur."}, status=status.HTTP_400_BAD_REQUEST)

            # 2. Éviter les doublons : Une classe ne peut pas avoir deux fois la même matière
            if Cour.objects.filter(etablissement=etab_id, disponible_id=classe_id, matiere_id=matiere_id, annee_scolaire=annee.id_annee).exists():
                return Response({"message": "Ce cours (Classe + Matière) est déjà configuré pour cette classe pour cette année scolaire."}, status=status.HTTP_400_BAD_REQUEST)
            
            if not nom or not coef or nom == "" or int(coef) <= 0:
                return Response({"message": "Les champs 'Nom' et 'Coefficient' sont obligatoires. Avec coefficient > 0"}, status=status.HTTP_400_BAD_REQUEST)
                
            Cour.objects.create(
                enseignant_id=ens_id,
                disponible_id=classe_id,
                matiere_id=matiere_id,
                etablissement_id=etab_id,
                annee_scolaire=annee,
                nom=nom,
                coefficient=coef
            )

            
            return Response({"message": "Le cours a bien été ajouté."}, status=status.HTTP_201_CREATED) #self.get_serializer(cour_obj).data
            
        except Exception as e:
            print(e)
            return Response({"message": "Une erreur s'est produite lors de la création du cours."}, status=status.HTTP_400_BAD_REQUEST)

class OnCour(generics.RetrieveAPIView):
    queryset = Cour.objects.select_related('enseignant', 'matiere', 'disponible').all()
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
    queryset = Cour.objects.select_related('enseignant', 'matiere', 'disponible').all()
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
    queryset = Inscrit.objects.select_related('etablissement', 'eleve', 'disponible').all()
    serializer_class = InscritSerializers
    
class CreatInscrit(generics.CreateAPIView):
    queryset = Inscrit.objects.select_related('etablissement', 'eleve', 'disponible').all()
    serializer_class = InscritSerializers

class OnInscrit(generics.RetrieveAPIView):
    queryset = Inscrit.objects.select_related('etablissement', 'eleve', 'disponible').all()
    serializer_class = InscritSerializers
    lookup_field = 'pk'
    
class InscritUpdate(generics.UpdateAPIView):
    queryset = Inscrit.objects.select_related('etablissement', 'eleve', 'disponible').all()
    serializer_class = InscritSerializers
    lookup_field = 'pk'
    
class InscritDestroy(generics.DestroyAPIView):
    queryset = Inscrit.objects.select_related('etablissement', 'eleve', 'disponible').all()
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

    def create(self, request,id_etab, *args, **kwargs):
        etab = Etablissement.objects.filter(id_etab=id_etab).first()
        if not etab:
            return Response({"message": "Etablissement introuvable."}, status=status.HTTP_404_NOT_FOUND)
        
        cours = Cour.objects.filter(etablissement=etab, is_active=True, id_cours = self.request.data.get("cours")).first()
        
        if not cours:
            return Response({"message": "Cours introuvable. Verifier les iformations fournies et Ressayez."}, status=status.HTTP_404_NOT_FOUND) 
        
        notes = self.request.data.get("notes")
        
        # Si notes arrive sous forme de chaîne de caractères "{}", on le transforme en dict
        if isinstance(notes, str):
            try:
                notes = json.loads(notes)
            except json.JSONDecodeError:
                return Response({"message": "Le format des notes est invalide."}, status=status.HTTP_400_BAD_REQUEST)
            
        # récupérer l'année scolaire
        annee_nom = request.data.get("annee_scolaire")
        annee = AnneeScolaire.objects.filter(nom=annee_nom).first()
        if not annee:
            return Response({"message": "Année scolaire introuvable."}, status=404)
            
        try:
            with transaction.atomic():
                for id, note in notes.items():
                    Evaluation.objects.create(
                        etablissement=etab,
                        cour=cours,
                        eleve_id=id,
                        periode=self.request.data.get("periode"),
                        note=note,
                        typeEval = self.request.data.get("typeEval"),
                        date_evaluation = self.request.data.get("date_evaluation"),
                        date_remise = self.request.data.get("date_remise"),
                        date_enregisttrement = timezone.now().date(),
                        annee_scolaire = annee
                    )
                    
                return Response({"message": "Evaluations ajouter avec succès."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        
        
    
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
            if not Inscrit.objects.filter(id_eleve=eleve_id, disponible=cour_obj.disponible).exists():
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
    
    def create(self, request, *args, **kwargs):
        # serializer = self.get_serializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        
        cours_id = request.data.get("cours")
        dispo_id = request.data.get("disponible")
        etablissement_id = request.data.get("etablissement")
        annee_scolaire = request.data.get("annee_scolaire")
        horaire = request.data.get("horaire")

        # 🔹 Récupération des objets
        cours = Cour.objects.get(pk=cours_id) # tu peut aussi faire Cour.objects.get(id_cours=cours_id) ; pk signfie primary key,la clef primaire du model
        if not cours:
            return Response({"message": "Ce cours n'existe pas."}, status=status.HTTP_404_NOT_FOUND)
        
        classe_dispo = Disponible.objects.get(pid_disponible=dispo_id)
        if not classe_dispo:
            return Response({"message": "Cette classe n'existe pas."}, status=status.HTTP_404_NOT_FOUND)
        etablissement = Etablissement.objects.get(pk=etablissement_id)
        if not etablissement:
            return Response({"message": "Cet établissement n'existe pas."}, status=status.HTTP_404_NOT_FOUND)
        annee_scolaire = AnneeScolaire.objects.filter(nom=annee_scolaire, etablissement=etablissement).first()
        if not annee_scolaire:
            return Response({"message": "Cette année scolaire n'existe pas."}, status=status.HTTP_404_NOT_FOUND)

        # 🔒 Vérification doublon cours/classe/année
        if EmploiDuTemps.objects.filter(
            cour=cours,
            disponible=classe_dispo,
            annee_scolaire=annee_scolaire
        ).exists():
            return Response(
                {"message": "Ce cours est déjà programmé pour cette classe cette année."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Si horaire arrive sous forme de chaîne de caractères "{}", on le transforme en dict
        if isinstance(horaire, str):
            try:
                horaire = json.loads(horaire)
            except json.JSONDecodeError:
                return Response({"message": "Le format de l'horaire est invalide."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                for jour, heures in horaire.items():
                    debut = datetime.strptime(heures.get("debut"), "%H:%M").time()
                    fin = datetime.strptime(heures.get("fin"), "%H:%M").time()

                    # ⛔ Conflit enseignant
                    conflit_prof = EmploiDuTemps.objects.filter(
                        cour__enseignant=cours.enseignant,
                        jour=jour,
                        heure_debut__lt=fin,
                        heure_fin__gt=debut
                    ).first()

                    if conflit_prof:
                        return Response(
                            {"message": f"L’enseignant est déjà occupé le {jour} de {conflit_prof.heure_debut} à {conflit_prof.heure_fin}."},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # ⛔ Conflit créneau classe
                    conflit_classe = EmploiDuTemps.objects.filter(
                        disponible=classe_dispo,
                        jour=jour,
                        heure_debut__lt=fin,
                        heure_fin__gt=debut
                    ).first()

                    if conflit_classe:
                        return Response(
                            {"message": f"Créneau déjà pris par {conflit_classe.cour.nom} le {jour}."},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # ✅ Création
                    EmploiDuTemps.objects.create(
                        jour=jour,
                        heure_debut=debut,
                        heure_fin=fin,
                        etablissement=etablissement,
                        cour=cours,
                        disponible=classe_dispo,
                        annee_scolaire=annee_scolaire
                    )

            return Response(
                {"message": "Emploi du temps configuré avec succès."},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            print(e)
            return Response(
                {"message": "Erreur lors de la configuration de l'emploi du temps."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
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
            models.Q(cour__disponible=cour.disponible)
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
#=============================================== LOGIN STAFF =================================================
class LoginStaff(APIView):
    def post(self, request):
        email = request.data.get('email')
        mdp = request.data.get('mdp')
        code = request.data.get('code')

        # 1. Vérification des champs
        if not email or not mdp or not code:
            return Response({
                "flag": "bad",
                "message": "Veuillez fournir un email, un code et un mot de passe."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Vérification de l'unicité du code
        etablissement = Etablissement.objects.filter(code=code).first()
        if not etablissement: # Si l'Etablissement n'existe pas, on renvoie une erreur Etablissement.objects.filter(code=code).exists():
            return Response({
                "flag": "bad",
                "message": "Le code de l'Etablissement est incorrect."
            }, status=status.HTTP_400_BAD_REQUEST)
        serializerEtab = EtablissementSerializers(etablissement)
            
        # On récupère l'utilisateur par son email
        user = User.objects.filter(email=email).first()
        
        if not user:
            return Response({
                "flag": "bad",
                "message": "Email incorrect ou utilisateur inexistant."
            }, status=status.HTTP_404_NOT_FOUND)
            
        # 2. Vérifier si le compte est actif
        if not user.is_active:
            return Response({
                "flag": "bad",
                "message": "Ce compte est désactivé. Veuillez contacter l'administration."
            }, status=status.HTTP_403_FORBIDDEN)
            
        # Verification de l'email du staff dans la table Staff
        if not Staff.objects.filter(user__email=email).exists():
            return Response({
                "flag": "bad",
                "message": "Email incorrect ou utilisateur inexistant."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not user.check_password(mdp):
            return Response({
                "flag": "bad",
                "message": "Mot de passe incorrect."
            }, status=status.HTTP_401_UNAUTHORIZED)

        # 2. Authentification via Django
        # Note: on utilise 'username=email' car vous avez créé l'user avec l'email comme identifiant
        user = authenticate(username=email, password=mdp)

        if user is not None:
            try:
                # 3. Récupérer les infos du Staff lié à cet User
                refresh = RefreshToken.for_user(user)
                
                staff = Staff.objects.get(user=user)
                
                # Récupérer son poste actuel via la table Occupe
                occupation = staff.staff_occupations.first()
                poste_nom = occupation.poste.nom if occupation else "Non poste défini"
                etab_nom = occupation.etablissement.nom if occupation else "Aucun établissement"

                return Response({
                    "flag": "good",
                    "message": f"Bienvenue, {staff.nom} !",
                    'refresh': str(refresh), # Le jeton de renouvellement
                    'access': str(refresh.access_token), # LE JETON POUR LE WEBSOCKET 🚀
                    "data": {
                        "id_staff": staff.id_staff,
                        "nom": staff.nom,
                        "prenom": staff.prenom,
                        "poste": poste_nom,
                        "etablissement": serializerEtab.data,
                        "etablissement_id": etablissement.id_etab,
                        
                        "email": user.email
                    }
                }, status=status.HTTP_200_OK)

            except Staff.DoesNotExist:
                return Response({
                    "flag": "bad",
                    "message": "Utilisateur trouvé, mais aucun profil Staff associé."
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # 4. Échec de l'authentification
            return Response({
                "flag": "bad",
                "message": "Email ou mot de passe incorrect."
            }, status=status.HTTP_401_UNAUTHORIZED)

#========================== LISTE DES ELEVES PAR ETABLISSEMENT =================================================
class ListeEtablissementEleve(APIView):
    def get(self, request, id_etab, annee_scolaire):
        etablissement = Etablissement.objects.filter(id_etab=id_etab).first()
        if not etablissement:
            return Response({"flag": "bad", "message": "Etablissement introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        annee_s = AnneeScolaire.objects.filter(nom=annee_scolaire, etablissement=etablissement).first()
        if not annee_s:
            return Response({"flag": "bad", "message": "Annee scolaire introuvable. Reenseignez !\n. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        inscriptions = Inscrit.objects.filter(etablissement=etablissement, annee_scolaire=annee_s, is_active=True).select_related('eleve', 'disponible').prefetch_related("scolarites").all()
        eleves_data = InscritSerializers(inscriptions, many=True).data
        # eleves_data = EleveSerializers([ins.eleve for ins in inscriptions], many=True).data  #(inscriptions, many=True).data
        
        return Response({"flag": "good", "data": eleves_data}, status=status.HTTP_200_OK)
    
#========================== LISTE DES ELEVES D'UNE CLASSE D'UN ETABLISSEMENT =================================================
class ListeEleveEtablissementEleve(APIView):
    def get(self, request, id_etab, annee_scolaire, id_disponible):
        etablissement = Etablissement.objects.filter(id_etab=id_etab).first()
        if not etablissement:
            return Response({"flag": "bad", "message": "Etablissement introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        annee_s = AnneeScolaire.objects.filter(nom=annee_scolaire, etablissement=etablissement).first()
        if not annee_s:
            return Response({"flag": "bad", "message": "Annee scolaire introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        classe_dispo = Disponible.objects.filter(id_disponible=id_disponible).first()
        if not classe_dispo:
            return Response({"flag": "bad", "message": "Classe introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        try:
            inscriptions = Inscrit.objects.filter(etablissement=etablissement, annee_scolaire=annee_s, disponible=classe_dispo, is_active=True).select_related('eleve', 'disponible').prefetch_related("scolarites").all()
            eleves_data = InscritSerializers(inscriptions, many=True).data
            # eleves_data = EleveSerializers([ins.eleve for ins in inscriptions], many=True).data  #(inscriptions, many=True).data
            
            return Response({"flag": "good", "data": eleves_data}, status=status.HTTP_200_OK)
        except:
            return Response({"flag": "bad", "message": "Impossible de trouver la liste des eleves. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
    
#========================== EMPLOIT DU TEMPS D'UNE CLASSE D'UN ETABLISSEMENT =================================================
class EmploiDuTempsClasseEtablissement(APIView):
    def get(self, request, id_etab, annee_scolaire, id_disponible):
        etablissement = Etablissement.objects.filter(id_etab=id_etab).first()
        if not etablissement:
            return Response({"flag": "bad", "message": "Etablissement introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        annee_s = AnneeScolaire.objects.filter(nom=annee_scolaire, etablissement=etablissement).first()
        if not annee_s:
            return Response({"flag": "bad", "message": "Annee scolaire introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        classe_dispo = Disponible.objects.filter(id_disponible=id_disponible).first()
        if not classe_dispo:
            return Response({"flag": "bad", "message": "Classe introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            emplois = EmploiDuTemps.objects.filter(etablissement=etablissement, annee_scolaire=annee_s, disponible=classe_dispo, is_active=True).all()
            emplois_data = EmploiDuTempsSerializers(emplois, many=True).data
            
            #transformation des donnee
            planning = defaultdict(dict)
            
            for e in emplois_data:
                matiere = e["cour"]["matiere"]["code"]
                jour = e["jour"]
                heure = f'{e["heure_debut"][:5]} - {e["heure_fin"][:5]}'

                planning[matiere][jour] = heure
            
            return Response({"flag": "good", "data": planning}, status=status.HTTP_200_OK)
        except:
            return Response({"flag": "bad", "message": "Impossible de trouver l'emploi du temps. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
    
#========================== LISTE DES ENSEIGNANTS PAR ETABLISSEMENT =================================================
class ListeEtablissementEnseignant(APIView):
    def get(self, request, id_etab, annee_scolaire):
        etablissement = Etablissement.objects.filter(id_etab=id_etab).first()
        if not etablissement:
            return Response({"flag": "bad", "message": "Etablissement introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        annee_s = AnneeScolaire.objects.filter(nom=annee_scolaire, etablissement=etablissement).first()
        if not annee_s:
            return Response({"flag": "bad", "message": "Annee scolaire introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        enseignants = Enseigne.objects.filter(etablissement=etablissement, annee_scolaire=annee_s, is_active=True).all()
        enseignants_data = EnseigneSerializers(enseignants, many=True).data
        
        return Response({"flag": "good", "data": enseignants_data}, status=status.HTTP_200_OK)
    
#========================== LISTE DES CLASSES PAR ETABLISSEMENT =================================================
class ListeEtablissementClasse(APIView):
    def get(self, request, id_etab):
        etablissement = Etablissement.objects.filter(id_etab=id_etab).first()
        if not etablissement:
            return Response({"flag": "bad", "message": "Etablissement introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        classes = Disponible.objects.filter(etablissement=etablissement, is_active=True).all()
        classes_data = DisponibleSerializers(classes, many=True).data
        
        return Response({"flag": "good", "data": classes_data}, status=status.HTTP_200_OK)
    
#========================== LISTE DES COURS PAR ETABLISSEMENT =================================================
class ListeEtablissementCours(APIView):
    def get(self, request, id_etab, annee_scolaire):
        etablissement = Etablissement.objects.filter(id_etab=id_etab).first()
        if not etablissement:
            return Response({"flag": "bad", "message": "Etablissement introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        annee_s = AnneeScolaire.objects.filter(nom=annee_scolaire, etablissement=etablissement).first()
        if not annee_s:
            return Response({"flag": "bad", "message": "Annee scolaire introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        cours = Cour.objects.filter(etablissement=etablissement, annee_scolaire=annee_s, is_active=True).all()
        cours_data = CoursSerializers(cours, many=True).data
        
        return Response({"flag": "good", "data": cours_data}, status=status.HTTP_200_OK)
    
#========================== LISTE DES COURS D'UNE CLASSE D'UN ETABLISSEMENT =================================================
class ListeEtablissementClasseCours(APIView):
    def get(self, request, id_etab, annee_scolaire, id_disponible):
        etablissement = Etablissement.objects.filter(id_etab=id_etab).first()
        if not etablissement:
            return Response({"flag": "bad", "message": "Etablissement introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        annee_s = AnneeScolaire.objects.filter(nom=annee_scolaire, etablissement=etablissement).first()
        if not annee_s:
            return Response({"flag": "bad", "message": "Annee scolaire introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        cours = Cour.objects.filter(etablissement=etablissement, annee_scolaire=annee_s, disponible=id_disponible, is_active=True).all()
        cours_data = CoursSerializers(cours, many=True).data
        
        return Response({"flag": "good", "data": cours_data}, status=status.HTTP_200_OK)
    
#========================== STATISTIQUES EU INFOS D'UNE CLASSE D'UN ETABLISSEMENT =================================================
class EtablissementClasseStatistiquesEtInfos(APIView):
    def get(self, request, id_etab, annee_scolaire, id_disponible):
        # 1. Vérifications de base
        etablissement = Etablissement.objects.filter(id_etab=id_etab).first()
        if not etablissement:
            return Response({"flag": "bad", "message": "Etablissement introuvable."}, status=status.HTTP_404_NOT_FOUND)
        
        annee_s = AnneeScolaire.objects.filter(nom=annee_scolaire, etablissement=etablissement).first()
        if not annee_s:
            return Response({"flag": "bad", "message": "Annee scolaire introuvable."}, status=status.HTTP_404_NOT_FOUND)
        
        classe_dispo = Disponible.objects.filter(etablissement=etablissement, annee_scolaire=annee_s, is_active=True,id_disponible=id_disponible).first()
        if not classe_dispo:
            return Response({"flag": "bad", "message": "Classe introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        # 3. Calcul des statistiques sur le QuerySet (Avant sérialisation)
        # On filtre les inscriptions actives pour cette classe
        inscrits_qs = Inscrit.objects.filter(
            etablissement=etablissement, 
            annee_scolaire=annee_s, 
            disponible=classe_dispo, 
            is_active=True
        )

        # On effectue les calculs directement en base de données pour la performance
        effectif = inscrits_qs.count()
        # Accès au genre via la relation ForeignKey 'eleve' définie dans le modèle Inscrit
        effectif_fille = inscrits_qs.filter(eleve__genre='F').count()
        effectif_garcon = inscrits_qs.filter(eleve__genre='M').count()
        
        # 4. Préparation des données supplémentaires si besoin
        # Si vous voulez aussi renvoyer la liste des élèves :
        # eleves_data = InscritSerializers(inscrits_qs, many=True).data

        return Response({
            "flag": "good", 
            "data": {
                "effectif": effectif, 
                "effectif_fille": effectif_fille, 
                "effectif_garcon": effectif_garcon,
                "scolarite": classe_dispo.scolarite # Ajout de l'info scolarite du modèle Disponible
            }
        }, status=status.HTTP_200_OK)
        
#========================== LISTE DES EMPLOIT DU TEMPS D'UN ETABLISSEMENT =================================================
# class ListeEtablissementEmploi(APIView):
#     def get(self, request, id_etab, annee_scolaire):
        
#         etablissement = Etablissement.objects.filter(id_etab=id_etab).first()
#         if not etablissement:
#             return Response({"flag": "bad", "message": "Etablissement introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
#         annee_s = AnneeScolaire.objects.filter(nom=annee_scolaire).first()
#         if not annee_s:
#             return Response({"flag": "bad", "message": "Annee scolaire introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
#         # 1. Récupération des données (Tri par classe obligatoire pour groupby)
#         # On utilise select_related pour optimiser la requête si 'classe' est une ForeignKey
#         emplois = EmploiDuTemps.objects.filter(etablissement=etablissement, annee_scolaire=annee_s, is_active=True).order_by('classe')
#         # 2. Sérialisation initiale (liste plate)
#         emploi_data = EmploiDuTempsSerializers(emplois, many=True).data
#         # print(emploi_data)
        
#         # 3. Regroupement par classe
#         # On suppose que votre sérialiseur renvoie un champ 'classe_nom' ou 'classe' (chaîne de caractères)
#         resultat_groupe = []
        
#         # 'key' doit être le nom du champ dans votre Serializer (ex: 'classe' ou 'classe_detail')
#         for classe_nom, groupe in groupby(emploi_data, lambda x: x['classe_nom']):
#             resultat_groupe.append({
#                 "nom_classe": classe_nom,
#                 "total_cours": len(list(groupe_copy := list(groupe))), # On compte les éléments
#                 "horaires": groupe_copy # On met la liste des emplois correspondants
#             })
        
#         return Response({"flag": "good", "data": resultat_groupe}, status=status.HTTP_200_OK)

# -----------------------ANNEE SCOLAIRE------------------------------------------------------
class AnneeScolaireList(generics.ListAPIView):
    queryset = AnneeScolaire.objects.all()
    serializer_class = AnneeScolaireSerializers
    
class AnneeScolaireCreat(generics.CreateAPIView):
    queryset = AnneeScolaire.objects.all()
    serializer_class = AnneeScolaireSerializers

class OnAnneeScolaire(generics.RetrieveAPIView):
    queryset = AnneeScolaire.objects.all()
    serializer_class = AnneeScolaireSerializers
    lookup_field = 'pk'
    
class AnneeScolaireUpdate(generics.UpdateAPIView):
    queryset = AnneeScolaire.objects.all()
    serializer_class = AnneeScolaireSerializers
    lookup_field = 'pk'
    
class AnneeScolaireDestroy(generics.DestroyAPIView):
    queryset = AnneeScolaire.objects.all()
    serializer_class = AnneeScolaireSerializers
    lookup_field = 'pk'
    
#======================================LISTE DES ANNEES SCOLAIRES D'UN ETABLISSEMENT================================================
class ListeEtablissementAnneeScolaire(APIView):
    def get(self, request, id_etab):
        
        etablissement = Etablissement.objects.filter(id_etab=id_etab).first()
        if not etablissement:
            return Response({"flag": "bad", "message": "Etablissement introuvable. Reessayez !\nVeuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        # 1. Récupération des données (Tri par classe obligatoire pour groupby)
        # On utilise select_related pour optimiser la requête si 'classe' est une ForeignKey
        annees = AnneeScolaire.objects.filter(etablissement=etablissement).order_by('-date_debut')
        # 2. Sérialisation initiale (liste plate)
        annee_data = AnneeScolaireSerializers(annees, many=True).data
        # print(annee_data)
        
        return Response({"flag": "good", "data": annee_data}, status=status.HTTP_200_OK)
    
#======================================AJOUTER UNE ANNEES SCOLAIRES D'UN ETABLISSEMENT================================================
class AjouterAnneeScolaire(APIView):
    def post (self, request, id_etab):
        try:
            etablissement = Etablissement.objects.filter(id_etab=id_etab).first()
            if not etablissement:
                return Response({"flag": "bad", "message": "Etablissement introuvable. Reessayez !\nVeuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = AnneeScolaireSerializers(data=request.data)
            serializer.is_valid(raise_exception=True)

            date_debut = serializer.validated_data["date_debut"]
            date_fin = serializer.validated_data["date_fin"]
            
            mois = (
                (date_fin.year - date_debut.year) * 12
                + (date_fin.month - date_debut.month)
            )
            
            if date_debut >= date_fin:
                return Response({"flag": "bad", "message": "La date de debut doit être inférieure à la date de fin."}, status=status.HTTP_404_NOT_FOUND)
            
            if mois < 8:
                return Response({"flag": "bad", "message": "Une année scolaire doit durer au minimum 8 mois."}, status=status.HTTP_404_NOT_FOUND)
            
            serializer.save(etablissement=etablissement)
            
            return Response({
                "flag": "success",
                "message": "Année scolaire créée avec succès.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            return Response({"flag": "bad", "message": "Une erreur est survenue. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
# ----------------------- ANNEE SCOLAIRE END------------------------------------------------------

#======================================STATISTIQUE ET DASHBOARD D'UN ETABLISSEMENT================================================
class Statistique(APIView):
    def get(self, request, id_etab, annee_scolaire):
        
        def calculer_taux_reussite(etablissement_id, annee_id, periode_index):
            # 1. On récupère tous les élèves inscrits
            inscrits = Inscrit.objects.filter(
                etablissement_id=etablissement_id,
                annee_scolaire_id=annee_id,
                is_active=True
            ).select_related('disponible__classe', 'eleve')

            resultats_classes = {}

            for inscrit in inscrits:
                classe_nom = inscrit.disponible.classe.nom
                if classe_nom not in resultats_classes:
                    resultats_classes[classe_nom] = {'admis': 0, 'total': 0}

                # 2. On récupère toutes les évaluations de cet élève pour la période
                # Le champ 'periode' dans Evaluation est un entier (1, 2, etc.)
                evals_eleve = Evaluation.objects.filter(
                    eleve=inscrit.eleve,
                    annee_scolaire_id=annee_id,
                    periode=periode_index
                ).select_related('cour__matiere')

                # Identifier les matières uniques évaluées
                id_cours_suivis = evals_eleve.values_list('cour', flat=True).distinct()
                
                somme_moyennes_coeff = 0
                total_coefficients = 0

                for cour_id in id_cours_suivis:
                    evals_matiere = evals_eleve.filter(cour_id=cour_id)
                    
                    # Calcul selon le typeEval
                    interros = evals_matiere.filter(typeEval__iexact='INTERROGATION').aggregate(Avg('note'))['note__avg'] or 0
                    devoirs = evals_matiere.filter(typeEval__iexact='DEVOIR').aggregate(Sum('note'))['note__sum'] or 0
                    
                    # Formule demandée : (Interro + Devoir) / 3
                    moyenne_matiere = (float(interros) + (float(devoirs))) / 3
                    
                    # Récupération du coefficient depuis le modèle Cour
                    coeff = evals_matiere.first().cour.coefficient
                    
                    somme_moyennes_coeff += (moyenne_matiere * coeff)
                    total_coefficients += coeff

                # 3. Calcul de la moyenne générale de l'élève
                if total_coefficients > 0:
                    moyenne_generale = somme_moyennes_coeff / total_coefficients
                    if moyenne_generale >= 10:
                        resultats_classes[classe_nom]['admis'] += 1
                
                resultats_classes[classe_nom]['total'] += 1

            # 4. Calcul du pourcentage final par classe
            for classe, data in resultats_classes.items():
                data['taux'] = (data['admis'] / data['total'] * 100) if data['total'] > 0 else 0

            return resultats_classes
        
        etablissement = Etablissement.objects.filter(id_etab=id_etab).first()
        if not etablissement:
            return Response({"flag": "bad", "message": "Etablissement introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        annee_s = AnneeScolaire.objects.filter(nom=annee_scolaire, etablissement=etablissement).first()
        if not annee_s:
            return Response({"flag": "bad", "message": "Annee scolaire introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            inscriptions = Inscrit.objects.filter(
                etablissement=etablissement,
                annee_scolaire=annee_s,
                is_active=True
            )
            #recuperer la liste des enseignants de l'etablissement pour cette annee scolaire
            enseignants = Enseigne.objects.filter(
                etablissement=etablissement,
                annee_scolaire=annee_s,
                is_active=True
            ).aggregate(
                total_ens = Count('enseignant', distinct=True),
                nombre_homme = Count('enseignant', filter=Q(enseignant__genre__iexact='Homme')),
                nombre_femme = Count('enseignant', filter=Q(enseignant__genre__iexact='Femme')),
                salaire_total = Sum('salaire')
            )
            
            """recuperer la liste des eleve par classes d'un l'etablissement pour une annee scolaire
                Récupération de tous les inscrits filtrés
            """
            inscriptionsEleves = inscriptions.values('disponible__classe__nom').annotate(
                total_eleves=Count('eleve'), # Nombre total d'inscrits
                nombre_garcons=Count('eleve', filter=Q(eleve__genre__iexact='M')), # Nombre de garcons
                nombre_filles=Count('eleve', filter=Q(eleve__genre__iexact='F'))
            ).order_by('disponible__classe__nom')
            
            #Total attendu (Somme des frais de chaque élève inscrit dans l'etablissement pour cette annee scolaire)
            total_attendu = inscriptions.aggregate(total=Sum('frais_scolarite'))['total'] or 0
            
            # Total encaissé (Somme des frais de chaque élève inscrit dans l'etablissement pour cette annee scolaire)
            total_encaisse = Scolarite.objects.filter(
                inscrit__annee_scolaire=annee_s
            ).aggregate(total=Sum('montant'))['total'] or 0
            
            #Calcul du pourcentage de paiement du total attendu par le total encaissé pour cette annee scolaire pour l'etablissement
            taux = (total_encaisse / total_attendu) * 100 if total_attendu > 0 else 0
            
            #Taux de réussite par classe par trimestre ou semestre selon de type de l'etablissement
            #recuperer le nombre de semestre/trimestre
            nb_periode = Evaluation.objects.filter(
                etablissement=etablissement,
                annee_scolaire=annee_s
            ).aggregate(
                total_periode = Count('periode', distinct=True)
            )['total_periode'] or 0
            
            #Calculer les stats pour chaque période trouvée
            stats_par_periode = []

            for p in range(1, nb_periode + 1):
                # Appeler ta fonction de calcul du taux de réussite pour la période 'p'
                resultats_p = calculer_taux_reussite(etablissement, annee_s, p)
                stats_par_periode.append({
                    'periode': p,
                    'data': resultats_p
                })
                
            #recuperer la liste des eleves d'un etablissement,effectif total, nombre de fille et garcons
            elevesEtab = inscriptions.aggregate(
                total_eleves=Count('id_inscrit'),
                nombre_garcons=Count('eleve__genre', filter=Q(eleve__genre__iexact='M')),
                nombre_filles=Count('eleve__genre', filter=Q(eleve__genre__iexact='F'))
            )
            
            # Répartition par tranche d’âge des eleves d'un etablissement
            # On définit l'année de référence (aujourd'hui)
            current_year = date.today().year

            stats_age = inscriptions.annotate(
                # Calcul approximatif de l'âge : Année actuelle - Année de naissance
                age=current_year - F('eleve__date__year')
            ).aggregate(
                moins_de_10=Count('id_inscrit', filter=Q(age__lt=10)),
                entre_10_et_14=Count('id_inscrit', filter=Q(age__gte=10, age__lte=14)),
                entre_15_et_18=Count('id_inscrit', filter=Q(age__gte=15, age__lte=18)),
                plus_de_18=Count('id_inscrit', filter=Q(age__gt=18)),
                age_inconnu=Count('id_inscrit', filter=Q(eleve__date__isnull=True))
            )
            
        except Exception as e:
            print(e)
            return Response({"flag": "bad", "message": "Une erreur est survenue. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        
#======================================STATISTIQUE ET DASHBOARD D'UNE CLASSE D'UN ETABLISSEMENT================================================
class StatistiqueClasse(APIView):
    def get(self, request, id_etab, annee_scolaire, id_disponible):
        
        def recap_eleves(inscrits,evaluations, periods):
            # Rendu final
            rendu = {}
            
            # OPTIMISATION : On récupère tout d'un coup avant les boucles
            # On transforme le QuerySet en liste pour travailler en mémoire vive
            # Récupération de toutes les évaluations de l'élève pour la période
            toutes_les_evals = list(evaluations.select_related('cour__matiere'))
            
            for p in periods:
                # Initialiser la période si elle n'existe pas
                if p not in rendu:
                    rendu[p] = {}
                #nom pour reuperer les statistique admis, total et taux
                nom = f"stats{p}"
                if nom not in rendu[p]:
                    rendu[p][nom] = {'admis': 0, 'total': 0, 'taux': 0}
                    
                for inscrit in inscrits:
                    # On incrémente le total pour chaque élève traité
                    rendu[p][nom]['total'] += 1
                    
                    # Filtrer d'abord les notes de CET élève pour CETTE période
                    notes_eleve = [e for e in toutes_les_evals if e.eleve_id == inscrit.eleve_id and e.periode == p]

                    # Identifier les cours uniques via l'ensemble des évaluations récupérées
                    # Utiliser set pour éviter les doublons de cours
                    #Prendre uniquement les cours de CET élève
                    cours_ids = set(e.cour_id for e in notes_eleve)
                    
                    somme_moyennes_coeff = 0
                    total_coefficients = 0
                    
                    for c_id in cours_ids:
                        # Filtrage en mémoire (plus rapide qu'une requête SQL par matière)
                        #Chercher dans notes_eleve (et pas cours_ids)
                        notes_matiere = [e for e in notes_eleve if e.cour_id == c_id]
                        
                        if not notes_matiere:
                            continue
                        
                        # Accès aux infos de base (matière et nom élève)
                        matiere_nom = notes_matiere[0].cour.matiere.nom
                        eleve_nom_complet = f"{inscrit.eleve.nom} {inscrit.eleve.prenom}"
                        coeff = notes_matiere[0].cour.coefficient
                        
                        # Initialisation sécurisée des niveaux du dictionnaire
                        if matiere_nom not in rendu[p]:
                            rendu[p][matiere_nom] = {}
                        if eleve_nom_complet not in rendu[p][matiere_nom]:
                            rendu[p][matiere_nom][eleve_nom_complet] = []
                        

                        # Séparation par typeEval
                        interros = [float(n.note) for n in notes_matiere if n.typeEval.upper() == 'INTERROGATION']
                        devoirs = [float(n.note) for n in notes_matiere if n.typeEval.upper() == 'DEVOIR']
                        
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
                        
                        # Ajout des notes au dictionnaire
                        rendu[p][matiere_nom][eleve_nom_complet].append({
                            'interro':{
                                "note": interros,
                                "moyenne": moy_interro
                            },
                            'devoir':{
                                "note": devoirs,
                                "somme": som_devoir
                            },
                            'moyenne': moyenne_matiere,
                            'moyenneCoeff': moyenne_matiere * coeff,
                            'coeff': coeff
                        })
                        
                    # Validation de la réussite de l'élève pour la periode
                    if total_coefficients > 0:
                        if (somme_moyennes_coeff / total_coefficients) >= 10:
                            rendu[p][nom]['admis'] += 1
                            
                # CALCUL DU TAUX (Une fois que tous les élèves de la période sont passés)
                total_p = rendu[p][nom]['total']
                if total_p > 0:
                    admis_p = rendu[p][nom]['admis']
                    rendu[p][nom]['taux'] = (admis_p / total_p) * 100
                    
            return rendu
        
        etablissement = Etablissement.objects.filter(id_etab=id_etab).first()
        if not etablissement:
            return Response({"flag": "bad", "message": "Etablissement introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        annee_s = AnneeScolaire.objects.filter(nom=annee_scolaire, etablissement=etablissement).first()
        if not annee_s:
            return Response({"flag": "bad", "message": "Annee scolaire introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        disponible = Disponible.objects.filter(id=id_disponible).first()
        if not disponible:
            return Response({"flag": "bad", "message": "Classe introuvable. Veuillez contacter l'administration ou le service technique de UNCHAIN"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            inscriptions = Inscrit.objects.filter(
                etablissement=etablissement,
                disponible=id_disponible,
                annee_scolaire=annee_s, 
                is_active=True
            )
            
            evaluations = Evaluation.objects.filter(
                etablissement=etablissement,
                annee_scolaire=annee_s,
                cour__disponible=id_disponible
            )
            # 1. Total attendu (Somme des frais de chaque élève inscrit dans la classe pour cette annee scolaire)
            total_attendu = inscriptions.aggregate(total=Sum('frais_scolarite'))['total'] or 0
            
            # 2. Total encaissé (Somme des frais de chaque élève inscrit dans la classe pour cette annee scolaire)
            total_encaisse = Scolarite.objects.filter(
                inscrit__annee_scolaire=annee_s,
                Inscrit__disponible=id_disponible
            ).aggregate(total=Sum('montant'))['total'] or 0
            
            # 3. Calcul du pourcentage de paiement du total attendu par le total encaissé pour cette annee scolaire pour la classe
            taux = (total_encaisse / total_attendu) * 100 if total_attendu > 0 else 0
            
            # Répartition par tranche d’âge des eleves d'une classe
            # On définit l'année de référence (aujourd'hui)
            current_year = date.today().year

            stats_age = inscriptions.annotate(
                # Calcul approximatif de l'âge : Année actuelle - Année de naissance
                age=current_year - F('eleve__date__year')
            ).aggregate(
                moins_de_10=Count('id_inscrit', filter=Q(age__lt=10)),
                entre_10_et_14=Count('id_inscrit', filter=Q(age__gte=10, age__lte=14)),
                entre_15_et_18=Count('id_inscrit', filter=Q(age__gte=15, age__lte=18)),
                plus_de_18=Count('id_inscrit', filter=Q(age__gt=18)),
                age_inconnu=Count('id_inscrit', filter=Q(eleve__date__isnull=True))
            )

            #Taux de réussite par classe par trimestre ou semestre d'uneclasse selon de type de l'etablissement
            #recuperer le nombre de semestre/trimestre
            periodes = evaluations.filter(periode__gt=0).values('periode', flat=True).distinct().order_by('periode')
     
            #Calculer les stats pour chaque période trouvée
            stats_par_periode = recap_eleves(inscriptions, evaluations, periodes)
                
        except Exception as e:
            print(f"Une erreur s'est produite lors de la tentative de calcul des statistiques : {e}")
            return Response({"flag": "bad", "message": "Une erreur s'est produite lors de la tentative de calcul des statistiques"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)