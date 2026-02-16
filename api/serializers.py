from rest_framework import serializers
from .models import *

class AnneeScolaireSerializers(serializers.ModelSerializer):
    class Meta:
        model = AnneeScolaire
        fields = "__all__"
        read_only_fields = ["created_at"]
        
class EtablissementSerializers(serializers.ModelSerializer):
    class Meta:
        model = Etablissement
        fields = ["id_etab", "nom", "adresse", "code", "type", "is_active", "created_at"]
        read_only_fields = ["id_etab", "code", "created_at"]
        
class EnseignantSerializers(serializers.ModelSerializer):
    # On récupère l'email via la relation 'user' du modèle Eleve
    email = serializers.ReadOnlyField(source='user.email')
    username = serializers.ReadOnlyField(source='user.username')
    class Meta:
        model = Enseignant
        fields = ["id_ens", "nom", "prenom", "date", "genre", "tel1", "tel2", "email", "adresse", "username", "is_active", "created_at"]
        read_only_fields = ["id_ens", "created_at"]
        
class EleveSerializers(serializers.ModelSerializer):
    # On récupère l'email via la relation 'user' du modèle Eleve
    matricule = serializers.ReadOnlyField(source='user.username')
    class Meta:
        model = Eleve
        fields = ["id_eleve", "nom", "matricule", "prenom","genre", "date", "matricule", "nom_prenom_parent_1", "tel1", "nom_prenom_parent_2", "tel2",
                  "email_parent_1", "email_parent_2", "adresse", "is_active", "created_at"]
        read_only_fields = ["id_eleve", "created_at"]
        
class MatiereSerializers(serializers.ModelSerializer):
    class Meta:
        model = Matiere
        fields = ["id_matiere", "nom", "code", "created_at"]
        read_only_fields = ["created_at"]
        
class PosteSerializers(serializers.ModelSerializer):
    class Meta:
        model = Poste
        fields = ["id_poste", "nom", "code", "created_at"]
        read_only_fields = ["created_at"]
        
class NiveauEtudeSerializers(serializers.ModelSerializer):
    class Meta:
        model = NiveauEtude
        fields = "__all__"
        read_only_fields = ["created_at"]
        
class ClasseSerializers(serializers.ModelSerializer):
    # Ce champ sert à la LECTURE (GET) pour voir le nom du niveau
    niveau_details = NiveauEtudeSerializers(read_only=True)
    niveau = NiveauEtudeSerializers(read_only=True)
    
    # On laisse 'niveau' se gérer automatiquement pour l'ÉCRITURE (POST)
    # ou on le définit explicitement si nécessaire :
    # niveau = serializers.PrimaryKeyRelatedField(queryset=NiveauEtude.objects.all())

    class Meta:
        model = Classe
        # On inclut 'niveau' pour l'ID et 'niveau_details' pour l'affichage
        fields = ["id_classe", "nom", "code", "niveau", "niveau_details", "created_at"]
        read_only_fields = ["created_at"]
        
class StaffSerializers(serializers.ModelSerializer):
    # On récupère l'email via la relation 'user' du modèle Eleve
    email = serializers.ReadOnlyField(source='user.email')
    username = serializers.ReadOnlyField(source='user.username')
    class Meta:
        model = Staff
        fields = ["id_staff", "nom", "prenom", "date", "tel1", "tel2", "sexe", "email", "username", "adresse", "status", "is_active", "created_at"]
        read_only_fields = ["id_staff", "created_at"]

class DisponibleSerializers(serializers.ModelSerializer):
    etablissement = EtablissementSerializers(read_only = True)
    classe = ClasseSerializers(read_only = True)
    annee_scolaire = AnneeScolaireSerializers(read_only = True)
    class Meta:
        model = Disponible
        fields =  "__all__" #["id_disponible", "etablissement", "classe", "is_active", "created_at"]
        read_only_fields = ["id_disponible", "created_at"]
         
class CoursSerializers(serializers.ModelSerializer):
    enseignant = EnseignantSerializers(read_only = True) # 'source = 'enseignant'' facultatif
    matiere = MatiereSerializers(read_only = True)
    disponible = DisponibleSerializers(read_only = True)
    annee_scolaire = AnneeScolaireSerializers(read_only = True)
    class Meta:
        model = Cour
        fields = "__all__" #["id_cours", "nom", "enseignant", "matiere", "classe", "coefficient", "created_at"]
        read_only_fields = ["id_cours", "created_at"]
        
class EnseigneSerializers(serializers.ModelSerializer):
    etablissement = EtablissementSerializers(read_only = True)
    enseignant = EnseignantSerializers(read_only = True)
    annee_scolaire = AnneeScolaireSerializers(read_only = True)
    class Meta:
        model = Enseigne
        fields = "__all__" #["id_enseigne", "enseignant", "etablissement", "created_at"]
        read_only_fields = ["id_enseigne", "created_at"]
        
class ScolariteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scolarite
        fields = "__all__"
        read_only_fields = ['id', 'date_paiement']
        
class InscritSerializers(serializers.ModelSerializer):
    #etablissement_datail = EtablissementSerializers(source = "etablissement", read_only = True)
    etablissement = EtablissementSerializers(read_only = True) #, "etablissement_datail"
    #eleve_datail = EleveSerializers(source = "eleve", read_only = True) #, "eleve_datail"
    eleve = EleveSerializers(read_only = True) #✅tu veux utiliser ca(ce format) pour le detail de l'eleve au lieux de eleve_datail. tu peux aussi te passer de 'source = "eleve"'
    disponible = DisponibleSerializers(read_only = True)
    scolarites = ScolariteSerializer(many=True, read_only=True) #(meny = True) paermet de recuperer plusieurs scolarites
    class Meta:
        model = Inscrit
        fields = "__all__" #["id_inscrit", "etablissement", "disponible", "eleve", "scolarites", "is_active", "created_at"]
        read_only_fields = ["created_at"]
        
class PresenceSerializers(serializers.ModelSerializer):
    cour_datail = CoursSerializers(source = "cours",read_only = True)
    class Meta:
        model = Presence
        fields = list([f.name for f in Presence._meta.fields]) + ["cour_datail"]
        read_only_fields = ["created_at"]
        
class EvaluationSerializers(serializers.ModelSerializer):
    eleve = EleveSerializers(read_only = True)
    cour = CoursSerializers(read_only = True)
    class Meta:
        model = Evaluation
        fields = "__all__"
        read_only_fields = ["created_at"]

class DepenseSerializers(serializers.ModelSerializer):
    etablissement_datail = EtablissementSerializers(source = "etablissement", read_only = True)
    class Meta:
        model = Depense
        fields = list([f.name for f in Depense._meta.fields]) + ["etablissement_datail"]
        read_only_fields = ["created_at"]
        
class OccupeSerializers(serializers.ModelSerializer):
    etablissement = EtablissementSerializers(source = "etablissement", read_only = True)
    staff = StaffSerializers(source = "staff", read_only = True)
    poste = PosteSerializers(source = "poste", read_only = True)
    class Meta:
        model = Occupe
        fields = "__all__" # list([f.name for f in Occupe._meta.fields])
        read_only_fields = ["created_at"]
        
class DocumentEleveSerializers(serializers.ModelSerializer):
    eleve = EleveSerializers(source = "eleve", read_only = True)
    class Meta:
        model = DocumentEleve
        fields = "__all__" #list([f.name for f in DocumentEleve._meta.fields])
        #fields = "__all__"
        read_only_fields = ["created_at"]
        
class DocumentEnseignantSerializers(serializers.ModelSerializer):
    enseignant_datail = EnseignantSerializers(source = 'enseignant',read_only = True)
    class Meta:
        model = DocumentEnseignant
        fields = list([f.name for f in DocumentEnseignant._meta.fields]) + ["enseignant_datail"]
        read_only_fields = ["created_at"]
        
class DocumentStaffSerializers(serializers.ModelSerializer):
    staff_detail = StaffSerializers(source = "staff", read_only = True)
    class Meta:
        model = DocumentStaff
        fields = list([f.name for f in DocumentStaff._meta.fields]) + ["staff_detail"]
        read_only_fields = ["created_at"]
        
class DocumentEtablissementSerializers(serializers.ModelSerializer):
    etablissement_datail = EtablissementSerializers(source = "etablissement", read_only = True)
    class Meta:
        model = DocumentEtablissement
        fields = list([f.name for f in DocumentEtablissement._meta.fields]) + ["etablissement_datail"]
        read_only_fields = ["created_at"]
        
class BibliothequeSerializers(serializers.ModelSerializer):
    class Meta:
        model = Bibliotheque
        fields = "__all__"
        read_only_fields = ["created_at"]
        
# class MessageSerializers(serializers.ModelSerializer):
#     class Meta:
#         model = Message
#         fields = "__all__"
#         read_only_fields = ["created_at"]
        
class MessageSerializers(serializers.ModelSerializer):
    # On affiche les noms pour éviter au front de faire des requêtes d'ID
    expediteur_nom = serializers.ReadOnlyField(source='expediteur.get_full_name')
    eleve_nom_complet = serializers.SerializerMethodField()
    # eleve_nom = serializers.ReadOnlyField(source='eleve.nom')
    # eleve_prenom = serializers.ReadOnlyField(source='eleve.prenom')
    
    class Meta:
        model = Message
        fields = [
            'id_msg', 'etablissement', 'expediteur', 'expediteur_nom',
            'eleve', 'eleve_nom_complet', 'objet', 'contenu',
            'lu', 'date_lecture', 'piece_jointe', 'date', 'heure', 
            'created_at'
        ]
        read_only_fields = ['id_msg', 'created_at', 'date_lecture']
        
class EmploiDuTempsSerializers(serializers.ModelSerializer):
    # Ce champ permet d'afficher "Lundi" au lieu de "LUN" dans les réponses GET
    # jour_display = serializers.CharField(source='get_jour_display', read_only=True)
    etablissement = EtablissementSerializers(read_only = True)
    cour = CoursSerializers(read_only = True)
    disponible = DisponibleSerializers(read_only = True)
    annee_scolaire = AnneeScolaireSerializers(read_only = True)

    class Meta:
        model = EmploiDuTemps
        fields = "__all__"
        read_only_fields = ["created_at"]
        
class AnneeScolaireSerializers(serializers.ModelSerializer):
    etablissement = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = AnneeScolaire
        fields = "__all__"
        read_only_fields = ["created_at"]
        