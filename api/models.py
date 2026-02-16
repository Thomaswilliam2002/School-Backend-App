import os
from django.db import models
from django.core.validators import FileExtensionValidator
import uuid
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.
# 1. Fonction pour organiser les dossiers par ID d'élève
def upload_eleve_path(instance, filename):
    # Le dossier portera l'ID de l'élève : media/documents/eleves/<ID_ELEVE>/<NOM_FICHIER>
    # 1. On récupère l'id de l'élève
    eleve_nom = instance.eleve.nom
    eleve_prenom = instance.eleve.prenom
    
    #renomer le fichier pour eviter les doublons et etre pressantable
    #ecuprer l'extension
    ext = os.path.splitext(filename)[1] # peux etre remplacer par 'filename.split('.')[-1]'
    final_name = f"{instance.nom_fichier}{ext}" # pas besoint de metre '.' avent l'extension, la variable ext contien '.+extention
    
    # 2. On récupère l'id de l'établissement via la table Inscrit
    # On utilise .first() pour obtenir l'inscription active
    inscription = instance.eleve.inscrit_eleve.first() 
    annee_scolaire = inscription.annee_scolaire.nom
    classe = inscription.disponible.classe.code
    etab_nom = inscription.etablissement.nom if inscription else "sans_etablissement"
    return f'documents/{etab_nom}/eleves/{annee_scolaire}/{classe}/{eleve_nom} {eleve_prenom}/{final_name}'

def upload_enseignant_path(instance, filename):
    enseignant_nom = instance.enseignant.nom
    enseignant_prenom = instance.enseignant.prenom
    
    ext = os.path.splitext(filename)[1]
    final_name = f"{instance.nom_fichier}{ext}"
    
    enseigne = instance.enseignant.enseigne_enseignant.first()
    annee_scolaire = enseigne.annee_scolaire.nom
    
    etab_nom = enseigne.etablissement.nom if enseigne else "sans_etablissement"
    return f'documents/{etab_nom}/enseignants/{annee_scolaire}/{enseignant_nom} {enseignant_prenom}/{final_name}'

def upload_staff_path(instance, filename):
    staff_nom = instance.staff.nom
    staff_prenom = instance.staff.prenom
    
    ext = os.path.splitext(filename)[1]
    final_name = f"{instance.nom_fichier}{ext}"
    
    occupe = instance.staff.staff_occupations.first()
    annee_scolaire = occupe.annee_scolaire.nom
    
    etab_nom = occupe.etablissement.nom if occupe else "sans_etablissement"
    return f'documents/{etab_nom}/staffs/{annee_scolaire}/{staff_nom} {staff_prenom}/{final_name}'

def upload_etablissement_path(instance, filename):
    etab_id = instance.etablissement.id_etab
    return f'documents/{etab_id}/{filename}'

class User(AbstractUser):
    email = models.EmailField(unique=True)
    
class Etablissement(models.Model):
    TYPE_CHOICES = [
        ('PRIVE', 'Privé'),
        ('PUBLIC', 'Public'),
    ]
    id_etab = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=500)
    adresse = models.CharField(max_length=500)
    code = models.CharField(max_length=20, unique=True)  # sera utiliser au moment de la connexion d'un staff a sonr etablissement
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='PRIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True) # Pour suspendre une école
    
    class Meta:
        db_table = 'etablissements'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.nom}"
    
class AnneeScolaire(models.Model):
    id_annee = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE)
    nom = models.CharField(max_length=20) # Ex: "2023-2024"
    date_debut = models.DateField()
    date_fin = models.DateField()
    is_active = models.BooleanField(default=False) # L'année en cours
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'annees_escolaires'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.nom} - {self.etablissement.nom}"
    
class Enseignant(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enseignant_profile', null=True, blank=True)
    id_ens = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=50,null= True, blank=True)
    prenom = models.CharField(max_length=100,null= True, blank=True)
    genre = models.CharField(max_length=15,null= True, blank=True)
    date = models.DateField(null= True, blank=True)
    tel1 = models.CharField(max_length=20,null= True, blank=True)
    tel2 = models.CharField(max_length=20,null= True, blank=True)
    adresse = models.CharField(max_length=500,null= True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        db_table = 'enseignants'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.nom}"

class Eleve(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='eleve_profile', null=True, blank=True)
    matricule = models.CharField(max_length=20,null= True, blank=True)
    id_eleve = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=50,null= True, blank=True)
    prenom = models.CharField(max_length=100,null= True, blank=True)
    genre = models.CharField(max_length=15,null= True, blank=True)
    date = models.DateField(null= True, blank=True)
    nom_prenom_parent_1 = models.CharField(max_length=200,null= True, blank=True)
    tel1 = models.CharField(max_length=20,null= True, blank=True)
    nom_prenom_parent_2 = models.CharField(max_length=200,null= True, blank=True)
    tel2 = models.CharField(max_length=20,null= True, blank=True)
    email_parent_1 = models.EmailField(null= True, blank=True)
    email_parent_2 = models.EmailField(null= True, blank=True)
    adresse = models.CharField(max_length=500,null= True, blank=True)
    # photo = models.FileField(upload_to='documents/photos/eleve/photo', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        db_table = 'eleves'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.nom}"

class Matiere(models.Model):
    id_matiere = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'matieres'
        ordering = ['-created_at']
        
    def __str__(self):
        
        return f"{self.nom}"
    
class Poste(models.Model):
    id_poste = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'postes'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.nom}"
    
class Staff(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff'
    )
    id_staff = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=50,null= True, blank=True)
    prenom = models.CharField(max_length=100,null= True, blank=True)
    date = models.DateField(null= True, blank=True)
    sexe = models.CharField(max_length=15,null= True, blank=True)
    tel1 = models.CharField(max_length=20,null= True, blank=True)
    tel2 = models.CharField(max_length=20,null= True, blank=True)
    # email = models.EmailField(null= True, blank=True)
    adresse = models.CharField(max_length=500,null= True, blank=True)
    # photo = models.ImageField(upload_to='photos/', null= True, blank=True)
    #post = models.ForeignKey(Poste, on_delete=models.CASCADE, related_name='staff_poste')#models.CharField(max_length=50,null= True, blank=True)
    status = models.CharField(max_length=20,null= True, blank=True)
    # status = models.CharField(
    #     max_length=30,
    #     choices=[
    #         ('ADMIN', 'Administrateur'),
    #         ('DIRECTION', 'Direction'),
    #         ('SECRETAIRE', 'Secrétaire'),
    #         ('COMPTABLE', 'Comptable'),
    #         ('SURVEILLANT', 'Surveillant'),
    #         ('CENSEUR', 'Censeur'),
    #     ]
    # )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True) # Le staff travaille-t-il encore ici ?
    class Meta:
        db_table = 'staffs'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.nom}"
    
class NiveauEtude(models.Model):
    id_niveau = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'niveaux'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.nom}"

    
class Classe(models.Model):
    id_classe = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    niveau = models.ForeignKey(NiveauEtude, on_delete=models.CASCADE, related_name='classe_niveau', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'classes'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.nom}"
    
class Cour(models.Model):
    id_cours = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=250)
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE, related_name='cour_enseignant')
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='cour_etablissement')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='cour_matiere')
    disponible = models.ForeignKey('Disponible', on_delete=models.CASCADE, related_name='cour_disponible')
    coefficient = models.PositiveIntegerField()
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='cour_annee_scolaire')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'cours'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.id_cours}"

class Disponible(models.Model):
    id_disponible = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='disponible_etablissement')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='disponible_classe')
    scolarite = models.DecimalField(max_digits=12, decimal_places=2)
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'disponibles'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.id_disponible}"
    
class Enseigne(models.Model):
    id_enseigne = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='enseigne_etablissement')
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE, related_name='enseigne_enseignant')
    type = models.CharField(max_length=50,null= True, blank=True)
    periode = models.CharField(max_length=50,null= True, blank=True)
    salaire = models.DecimalField(max_digits=12, decimal_places=2)
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='enseigne_annee_scolaire')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'enseignes'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.id_enseigne}"
    
class Inscrit(models.Model):
    id_inscrit = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='inscrit_etablissement')
    disponible = models.ForeignKey(Disponible, on_delete=models.CASCADE, related_name='inscrit_disponible')
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='inscrit_eleve')
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'inscrits'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.id_inscrit}"
    
class Presence(models.Model):
    id_presence = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='presence_etablissement')
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='presence_eleve')
    cour = models.ForeignKey(Cour, on_delete=models.CASCADE, related_name='presence_cour')
    date = models.DateField(null= True, blank=True)
    status = models.CharField(max_length=15,null= True, blank=True, default='PRESENT')
    commentaire = models.TextField(null=True, blank=True) # Pour le motif du retard/absence
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'presences'
        ordering = ['-created_at']
        unique_together = ('eleve', 'cour', 'date')
        
    def __str__(self):
        return f"{self.eleve} - {self.cour} - {self.date} ({self.status})" #f"{self.id_presence}"
    
class Evaluation(models.Model):
    id_eval = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='evaluation_etablissement')
    typeEval = models.CharField(max_length=100)
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='evaluation_eleve')
    cour = models.ForeignKey(Cour, on_delete=models.CASCADE, related_name='evaluation_cour')
    date_evaluation  = models.DateField(null= True, blank=True)
    date_remise = models.DateField(null= True, blank=True)
    date_enregisttrement = models.DateField(null= True, blank=True)
    note = models.DecimalField(max_digits=5, decimal_places=2,null= True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(20)])
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.SET_NULL, null=True, blank=True)
    periode = models.PositiveSmallIntegerField(help_text="1 pour Trim1/Sem1, 2 pour Trim2/Sem2, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'evaluations'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.id_eval}"
  
class Depense(models.Model):
    id_depense = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='depense_etablissement')
    titre = models.CharField(max_length=255) # Ex: "Achat de craies"
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date_depense = models.DateField()
    # Catégorie peut être un simple CharField ou un modèle à part
    categorie = models.CharField(max_length=100) 
    
    description = models.TextField(null=True, blank=True)
    justificatif = models.FileField(upload_to='depenses/justificatifs/', null=True, blank=True)
    
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Pour savoir quel membre du staff a fait la saisie
    enregistre_par = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'depenses'
        ordering = ['-date_depense']
        
    def __str__(self):
        return f"{self.titre} - {self.montant}"
    
class Occupe(models.Model):
    id_occupe = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='staff_occupations')
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='staff_etablissement')
    poste = models.ForeignKey(Poste, on_delete=models.CASCADE)
    salaire = models.DecimalField(max_digits=10, decimal_places=2)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    # annee_scolaire = models.CharField(max_length=10, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'occupes'
        ordering = ['-created_at']
        # Un staff ne peut avoir qu'un seul poste actif par établissement
        unique_together = ('staff', 'etablissement')
        
    def __str__(self):
        return f"{self.id_occupe}"
        
class DocumentEleve(models.Model):
    id_doc = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='documents_eleve')
    titre = models.CharField(max_length=200) # ex: "Certificat Médical", "Photo de profil"
    description = models.TextField(null=True, blank=True)
    nom_fichier = models.CharField(max_length=255, null=True, blank=True)
    # FileField accepte TOUT. On peut restreindre les extensions si besoin.
    # fichier = models.FileField(
    #     upload_to='pieces_jointes/%Y/%m/%d/', 
    #     validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'png', 'mp4', 'mp3', 'docx'])]
    # )
    fichier = models.FileField(upload_to=upload_eleve_path, max_length=700)
    
    type_fichier = models.CharField(null=True, max_length=20) # 'IMAGE', 'PDF', 'VIDEO', etc.
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'documentEleves'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.id_doc}"
    
class DocumentEnseignant(models.Model):
    id_doc = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE, related_name='documents_enseignant')
    titre = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    nom_fichier = models.CharField(max_length=255, null=True, blank=True)
    fichier = models.FileField(upload_to=upload_enseignant_path, max_length=700)
    type_fichier = models.CharField(max_length=20) # 'IMAGE', 'PDF', 'VIDEO', etc.
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(null=True, default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'documentEnseignants'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.id_doc}"
    
class DocumentStaff(models.Model):
    id_doc = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='documents_staff')
    titre = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    nom_fichier = models.CharField(max_length=255, null=True, blank=True)
    fichier = models.FileField(upload_to=upload_staff_path, max_length=700)
    type_fichier = models.CharField(null=True, max_length=20) # 'IMAGE', 'PDF', 'VIDEO', etc.
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'documentStaffs'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.id_doc}"
    
class DocumentEtablissement(models.Model):
    id_doc = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='documents_etablissement')
    titre = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    nom_fichier = models.CharField(max_length=255, null=True, blank=True)
    fichier = models.FileField(upload_to=upload_etablissement_path, max_length=700)
    type_fichier = models.CharField(null=True, max_length=20) # 'IMAGE', 'PDF', 'VIDEO', etc.
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'documentEtablissements'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.id_doc}"
    
class Bibliotheque(models.Model):
    id_doc = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titre = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    nom_fichier = models.CharField(max_length=255, null=True, blank=True)
    fichier = models.FileField(upload_to='documents/photos/eleve/photo/')
    type_fichier = models.CharField(null=True, max_length=20) # 'IMAGE', 'PDF', 'VIDEO', etc.
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'bibliotheque'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.id_doc}"
    
class Message(models.Model):
    id_msg = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='Message_etablissement')
    
    # Qui envoie ? (Staff ou Enseignant via leur compte User)
    expediteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages_envoyes', null=True)
    
    # Qui reçoit ?
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='messages_recus_eleve')
    
    objet = models.CharField(max_length=300)
    contenu = models.TextField()
    
    # Gestion de la lecture
    lu = models.BooleanField(default=False)
    date_lecture = models.DateTimeField(null=True, blank=True)
    
    # Pièce jointe éventuelle (pour un bulletin ou une convocation)
    piece_jointe = models.FileField(upload_to='messages/attachments/', null=True, blank=True)
    
    # Date et heure de l'envoi
    date = models.DateField(null= True, blank=True)
    heure = models.TimeField(null= True, blank=True)
    
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.SET_NULL, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'messages'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.id_msg}"
    
class EmploiDuTemps(models.Model):
    id_emploi = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE)
    cour = models.ForeignKey(Cour, on_delete=models.CASCADE, related_name='horaires_cour')
    # classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='horaires_classe')
    disponible  = models.ForeignKey(Disponible, on_delete=models.CASCADE, related_name='horaires_disponible')
    jour = models.CharField(max_length=20, null=True, blank=True)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.SET_NULL, null=True, blank=True)
    #salle = models.CharField(max_length=100, null=True, blank=True) # Optionnel
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'emplois_du_temps'
        ordering = ['jour', 'heure_debut']
        # Empêche d'avoir le même prof ou la même salle occupé au même moment (Logique complexe à gérer en vue)

    def __str__(self):
        return f"{self.cour} - {self.jour} ({self.heure_debut}-{self.heure_fin})"
    
class Scolarite(models.Model):
    inscrit = models.ForeignKey(
        Inscrit,
        on_delete=models.CASCADE,
        related_name='scolarites',
    )
    tranche = models.CharField(max_length=50)  # ex: "1ère tranche"
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateField(auto_now_add=True)
    reference = models.CharField(max_length=100, null=True, blank=True)
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'scolarites'
        ordering = ['-date_paiement']

    def __str__(self):
        return f"{self.inscrit} - {self.tranche} ({self.montant})"
    