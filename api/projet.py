# ------------------------------------------------------models.py---------------------------------------------------
from django.db import models
import uuid
# Create your models here.

class Etablissement(models.Model):
    id_etab = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=500)
    adresse = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'etablissements'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.nom}"
    
class Enseignant(models.Model):
    id_ens = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=50,null= True, blank=True)
    prenom = models.CharField(max_length=100,null= True, blank=True)
    date = models.DateField(null= True, blank=True)
    tel1 = models.CharField(max_length=20,null= True, blank=True)
    tel2 = models.CharField(max_length=20,null= True, blank=True)
    email = models.EmailField(null= True, blank=True)
    adresse = models.CharField(max_length=500,null= True, blank=True)
    # photo = models.ImageField(upload_to='photos/', null= True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'enseignants'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.nom}"

class Eleve(models.Model):
    id_eleve = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=50,null= True, blank=True)
    prenom = models.CharField(max_length=100,null= True, blank=True)
    date = models.DateField(null= True, blank=True)
    nom_prenom_parent_1 = models.CharField(max_length=200,null= True, blank=True)
    tel1 = models.CharField(max_length=20,null= True, blank=True)
    nom_prenom_parent_2 = models.CharField(max_length=200,null= True, blank=True)
    tel2 = models.CharField(max_length=20,null= True, blank=True)
    email_parent_1 = models.EmailField(null= True, blank=True)
    email_parent_2 = models.EmailField(null= True, blank=True)
    adresse = models.CharField(max_length=500,null= True, blank=True)
    # photo = models.ImageField(upload_to='photos/', null= True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'eleves'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.nom}"

class Matiere(models.Model):
    id_matiere = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'matieres'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.nom}"
    
class Staff(models.Model):
    id_staff = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=50,null= True, blank=True)
    prenom = models.CharField(max_length=100,null= True, blank=True)
    date = models.DateField(null= True, blank=True)
    tel1 = models.CharField(max_length=20,null= True, blank=True)
    tel2 = models.CharField(max_length=20,null= True, blank=True)
    email = models.EmailField(null= True, blank=True)
    adresse = models.CharField(max_length=500,null= True, blank=True)
    # photo = models.ImageField(upload_to='photos/', null= True, blank=True)
    post = models.CharField(max_length=50,null= True, blank=True)
    status = models.CharField(max_length=20,null= True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'staffs'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.nom}"

class Poste(models.Model):
    id_poste = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'postes'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.nom}"
    
class Classe(models.Model):
    id_classe = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    nom = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'classes'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.nom}"
    
class Cour(models.Model):
    id_cours = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE, related_name='cour_enseignant')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='cour_matiere')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='cour_classe')
    coefficient = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cours'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.id_cours}"

class Disponible(models.Model):
    id_disponible = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='disponible_etablissement')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='disponible_classe')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'Disponibles'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.id_disponible}"
    
class Enseigne(models.Model):
    id_enseigne = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='enseigne_etablissement')
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE, related_name='enseigne_enseignant')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'enseignes'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.id_enseigne}"
    
class Inscrit(models.Model):
    id_inscrit = models.UUIDField(primary_key=True, default= uuid.uuid4, editable= False)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='inscrit_etablissement')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='inscrit_classe')
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='inscrit_eleve')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inscrits'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.id_inscrit}"
    
# ----------------------------------------------------------------serializers.py---------------------------------
from rest_framework import serializers
from .models import Etablissement, Enseignant, Eleve, Matiere, Poste, Classe, Staff, Inscrit, Enseigne, Cour, Disponible

class EtablissementSerializers(serializers.ModelSerializer):
    class Meta:
        model = Etablissement
        fields = ["id_etab", "nom", "adresse", "created_at"]
        read_only_fields = ["id_etab", "created_at"]
        
class EnseignantSerializers(serializers.ModelSerializer):
    class Meta:
        model = Enseignant
        fields = ["id_ens", "nom", "prenom", "date", "tel1", "tel2", "email", "adresse", "created_at"]
        read_only_fields = ["id_ens", "created_at"]
        
class EleveSerializers(serializers.ModelSerializer):
    class Meta:
        model = Eleve
        fields = ["id_eleve", "nom", "prenom", "date", "nom_prenom_parent_1", "tel1", "nom_prenom_parent_2", "tel2",
                  "email_parent_1", "email_parent_2", "adresse", "created_at"]
        read_only_fields = ["id_eleve", "created_at"]
        
class MatiereSerializers(serializers.ModelSerializer):
    class Meta:
        model = Matiere
        fields = ["id_matiere", "nom", "created_at"]
        read_only_fields = ["id_matiere", "created_at"]
        
class PosteSerializers(serializers.ModelSerializer):
    class Meta:
        model = Poste
        fields = ["id_poste", "nom", "created_at"]
        read_only_fields = ["id_poste", "created_at"]
        
class ClasseSerializers(serializers.ModelSerializer):
    class Meta:
        model = Classe
        fields = ["id_classe", "nom", "created_at"]
        read_only_fields = ["id_classe", "created_at"]
        
class StaffSerializers(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ["id_staff", "nom", "prenom", "date", "tel1", "tel2", "email", "adresse", "poste", "status", "created_at"]
        read_only_fields = ["id_staff", "created_at"]
        
class CoursSerializers(serializers.ModelSerializer):
    enseignant = EnseignantSerializers(read_only = True)
    enseignant_id = serializers.PrimaryKeyRelatedField(queryset= Enseignant.objects.all(), pk_field = serializers.UUIDField(), write_only = True)
    matiere = MatiereSerializers(read_only = True)
    matiere_id = serializers.PrimaryKeyRelatedField(queryset= Matiere.objects.all(), pk_field = serializers.UUIDField(), write_only = True)
    classe = ClasseSerializers(read_only = True)
    classe_id = serializers.PrimaryKeyRelatedField(queryset= Classe.objects.all(), pk_field = serializers.UUIDField(), write_only = True)
    class Meta:
        model = Cour
        fields = ["id_cours", "enseignant", "enseignant_id", "matiere", "matiere_id", "classe", "classe_id", "created_at"]
        read_only_fields = ["id_cours", "created_at"]
        
class DisponibleSerializers(serializers.ModelSerializer):
    etablissement = EtablissementSerializers(read_only = True)
    etablissement_id = serializers.PrimaryKeyRelatedField(queryset= Etablissement.objects.all(), pk_field = serializers.UUIDField(), write_only = True)
    classe = ClasseSerializers(read_only = True)
    classe_id = serializers.PrimaryKeyRelatedField(queryset= Classe.objects.all(), pk_field = serializers.UUIDField(), write_only = True)
    class Meta:
        model = Disponible
        fields = ["id_disponible", "etablissement", "etablissement_id", "classe", "classe_id", "created_at"]
        read_only_fields = ["id_disponible", "created_at"]
        
class EnseigneSerializers(serializers.ModelSerializer):
    etablissement = EtablissementSerializers(read_only = True)
    etablissement_id = serializers.PrimaryKeyRelatedField(queryset= Etablissement.objects.all(), pk_field = serializers.UUIDField(), write_only = True)
    enseignant = EnseignantSerializers(read_only = True)
    enseignant_id = serializers.PrimaryKeyRelatedField(queryset= Enseignant.objects.all(), pk_field = serializers.UUIDField(), write_only = True)
    class Meta:
        model = Enseigne
        fields = ["id_enseigne", "enseignant", "enseignant_id", "etablissement", "etablissement_id", "created_at"]
        read_only_fields = ["id_enseigne", "created_at"]
        
class InscritSerializers(serializers.ModelSerializer):
    etablissement = EtablissementSerializers(read_only = True)
    etablissement_id = serializers.PrimaryKeyRelatedField(queryset= Etablissement.objects.all(), pk_field = serializers.UUIDField(), write_only = True)
    eleve = EleveSerializers(read_only = True)
    eleve_id = serializers.PrimaryKeyRelatedField(queryset= Etablissement.objects.all(), pk_field = serializers.UUIDField(), write_only = True)
    classe = ClasseSerializers(read_only = True)
    classe_id = serializers.PrimaryKeyRelatedField(queryset= Classe.objects.all(), pk_field = serializers.UUIDField(), write_only = True)
    class Meta:
        model = Inscrit
        fields = ["id_inscrit", "etablissement", "etablissement_id", "classe", "classe_id", "eleve", "eleve_id", "created_at"]
        read_only_fields = ["id_inscrit", "created_at"]
        
# -----------------------------------------------views.py-----------------------------------------------------------------
from django.shortcuts import render
from rest_framework import generics
from .models import Etablissement, Enseignant, Eleve, Matiere, Poste, Classe, Staff, Inscrit, Enseigne, Cour, Disponible
from .serializers import EtablissementSerializers, EnseignantSerializers, EleveSerializers, MatiereSerializers, PosteSerializers, StaffSerializers, ClasseSerializers, CoursSerializers, DisponibleSerializers, EnseigneSerializers, InscritSerializers

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

class OnEtablissement(generics.RetrieveAPIView):
    queryset = Etablissement.objects.all()
    serializer_class = EtablissementSerializers
    lookup_field = 'pk'
    
class EtablissementUpdate(generics.UpdateAPIView):
    queryset = Etablissement.objects.all()
    serializer_class = EtablissementSerializers
    lookup_field = 'pk'
    
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

class OnEnseignant(generics.RetrieveAPIView):
    queryset = Enseignant.objects.all()
    serializer_class = EnseignantSerializers
    lookup_field = 'pk'
    
class EnseignantUpdate(generics.UpdateAPIView):
    queryset = Enseignant.objects.all()
    serializer_class = EnseignantSerializers
    lookup_field = 'pk'
    
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
    queryset = Eleve.objects.all()
    serializer_class = EleveSerializers

class OnEleve(generics.RetrieveAPIView):
    queryset = Eleve.objects.all()
    serializer_class = EleveSerializers
    lookup_field = 'pk'
    
class EleveUpdate(generics.UpdateAPIView):
    queryset = Eleve.objects.all()
    serializer_class = EleveSerializers
    lookup_field = 'pk'
    
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

class OnMatiere(generics.RetrieveAPIView):
    queryset = Matiere.objects.all()
    serializer_class = MatiereSerializers
    lookup_field = 'pk'
    
class MatiereUpdate(generics.UpdateAPIView):
    queryset = Eleve.objects.all()
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
    queryset = Staff.objects.all()
    serializer_class = StaffSerializers
    
class CreatStaff(generics.CreateAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializers

class OnStaff(generics.RetrieveAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializers
    lookup_field = 'pk'
    
class StaffUpdate(generics.UpdateAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializers
    lookup_field = 'pk'
    
class StaffDestroy(generics.DestroyAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializers
    lookup_field = 'pk'
# -----------------------Staff end---------------------------------------
# -----------------------Classe start---------------------------------------
class ClasseList(generics.ListAPIView):
    queryset = Staff.objects.all()
    serializer_class = ClasseSerializers
    
class CreatClasse(generics.CreateAPIView):
    queryset = Classe.objects.all()
    serializer_class = ClasseSerializers

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

class OnCour(generics.RetrieveAPIView):
    queryset = Cour.objects.select_related('enseignant', 'matiere', 'classe').all()
    serializer_class = CoursSerializers
    lookup_field = 'pk'
    
class CourUpdate(generics.UpdateAPIView):
    queryset = Cour.objects.select_related('enseignant', 'matiere', 'classe').all()
    serializer_class = CoursSerializers
    lookup_field = 'pk'
    
class CourDestroy(generics.DestroyAPIView):
    queryset = Cour.objects.select_related('enseignant', 'matiere', 'classe').all()
    serializer_class = CoursSerializers
    lookup_field = 'pk'
# -----------------------Cour end---------------------------------------
# -----------------------Disponible start---------------------------------------
class DisponibleList(generics.ListAPIView):
    queryset = Disponible.objects.select_related('etablissement' 'classe').all()
    serializer_class = DisponibleSerializers
    
class CreatDisponible(generics.CreateAPIView):
    queryset = Disponible.objects.select_related('etablissement' 'classe').all()
    serializer_class = DisponibleSerializers

class OnDisponible(generics.RetrieveAPIView):
    queryset = Disponible.objects.select_related('etablissement' 'classe').all()
    serializer_class = DisponibleSerializers
    lookup_field = 'pk'
    
class DisponibleUpdate(generics.UpdateAPIView):
    queryset = Disponible.objects.select_related('etablissement' 'classe').all()
    serializer_class = DisponibleSerializers
    lookup_field = 'pk'
    
class DisponibleDestroy(generics.DestroyAPIView):
    queryset = Disponible.objects.select_related('etablissement' 'classe').all()
    serializer_class = DisponibleSerializers
    lookup_field = 'pk'
# -----------------------Disponible end---------------------------------------
# -----------------------Enseigne start---------------------------------------
class EnseigneList(generics.ListAPIView):
    queryset = Enseigne.objects.select_related('etablissement' 'enseignant').all()
    serializer_class = EnseigneSerializers
    
class CreatEnseigne(generics.CreateAPIView):
    queryset = Enseigne.objects.select_related('etablissement' 'enseignant').all()
    serializer_class = EnseigneSerializers

class OnEnseigne(generics.RetrieveAPIView):
    queryset = Enseigne.objects.select_related('etablissement' 'enseignant').all()
    serializer_class = EnseigneSerializers
    lookup_field = 'pk'
    
class EnseigneUpdate(generics.UpdateAPIView):
    queryset = Enseigne.objects.select_related('etablissement' 'enseignant').all()
    serializer_class = EnseigneSerializers
    lookup_field = 'pk'
    
class EnseigneDestroy(generics.DestroyAPIView):
    queryset = Enseigne.objects.select_related('etablissement' 'enseignant').all()
    serializer_class = EnseigneSerializers
    lookup_field = 'pk'
# -----------------------Enseigne end---------------------------------------
# -----------------------Inscrit start---------------------------------------
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
# -----------------------Inscrit end---------------------------------------
# --------------------------------------------------------urls.py-----------------------------------------------
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    # -----------------------Etablissement start---------------------------------------
    path('etablissements/', views.EtablissementList.as_view()),
    path('etablissement/create/', views.CreatEtablissement.as_view()),
    path('etablissement/<pk>/', views.OnEtablissement.as_view()),
    path('etablissement/<pk>/update/', views.EtablissementUpdate.as_view()),
    path('etablissement/<pk>/destroy/', views.EtablissementDestroy.as_view()),
    # -----------------------Etablissement end---------------------------------------
    # -----------------------Enseignant start---------------------------------------
    path('enseignants/', views.EnseignantList.as_view()),
    path('enseignant/create/', views.CreatEnseignant.as_view()),
    path('enseignant/<pk>/', views.OnEnseignant.as_view()),
    path('enseignant/<pk>/update/', views.EnseignantUpdate.as_view()),
    path('enseignant/<pk>/destroy/', views.EnseignantDestroy.as_view()),
    # -----------------------Enseignant end---------------------------------------
    # -----------------------Eleve start---------------------------------------
    path('eleves/', views.EleveList.as_view()),
    path('eleve/create/', views.CreatEleve.as_view()),
    path('eleve/<pk>/', views.OnEleve.as_view()),
    path('eleve/<pk>/update/', views.EleveUpdate.as_view()),
    path('eleve/<pk>/destroy/', views.EleveDestroy.as_view()),
    # -----------------------Eleve end---------------------------------------
    # -----------------------Matiere start---------------------------------------
    path('matieres/', views.MatiereList.as_view()),
    path('matiere/create/', views.CreatMatiere.as_view()),
    path('matiere/<pk>/', views.OnMatiere.as_view()),
    path('matiere/<pk>/update/', views.MatiereUpdate.as_view()),
    path('matiere/<pk>/destroy/', views.MatiereDestroy.as_view()),
    # -----------------------Matiere end---------------------------------------
    # -----------------------Poste start---------------------------------------
    path('postes/', views.PosteList.as_view()),
    path('poste/create/', views.CreatPoste.as_view()),
    path('poste/<pk>/', views.OnPoste.as_view()),
    path('poste/<pk>/update/', views.PosteUpdate.as_view()),
    path('poste/<pk>/destroy/', views.PosteDestroy.as_view()),
    # -----------------------Post end---------------------------------------
    # -----------------------Staff start---------------------------------------
    path('staffs/', views.StaffList.as_view()),
    path('staff/create/', views.CreatStaff.as_view()),
    path('staff/<pk>/', views.OnStaff.as_view()),
    path('staff/<pk>/update/', views.StaffUpdate.as_view()),
    path('staff/<pk>/destroy/', views.StaffDestroy.as_view()),
    # -----------------------Staff end---------------------------------------
    # -----------------------Classe start---------------------------------------
    path('classes/', views.ClasseList.as_view()),
    path('classe/create/', views.CreatClasse.as_view()),
    path('classe/<pk>/', views.OnClasse.as_view()),
    path('classe/<pk>/update/', views.ClasseUpdate.as_view()),
    path('classe/<pk>/destroy/', views.ClasseDestroy.as_view()),
    # -----------------------Classe end---------------------------------------
    # -----------------------Cour start---------------------------------------
    path('cours/', views.CourList.as_view()),
    path('cour/create/', views.CreatCour.as_view()),
    path('cour/<pk>/', views.OnCour.as_view()),
    path('cour/<pk>/update/', views.CourUpdate.as_view()),
    path('cour/<pk>/destroy/', views.CourDestroy.as_view()),
    # -----------------------Cour end---------------------------------------
    # -----------------------Disponible start---------------------------------------
    path('disponibles/', views.DisponibleList.as_view()),
    path('disponible/create/', views.CreatDisponible.as_view()),
    path('disponible/<pk>/', views.OnDisponible.as_view()),
    path('disponible/<pk>/update/', views.DisponibleUpdate.as_view()),
    path('disponible/<pk>/destroy/', views.DisponibleDestroy.as_view()),
    # -----------------------Disponible end---------------------------------------
    # -----------------------Enseigne start---------------------------------------
    path('enseignes/', views.EnseigneList.as_view()),
    path('enseigne/create/', views.CreatEnseigne.as_view()),
    path('enseigne/<pk>/', views.OnEnseigne.as_view()),
    path('enseigne/<pk>/update/', views.EnseigneUpdate.as_view()),
    path('enseigne/<pk>/destroy/', views.EnseigneDestroy.as_view()),
    # -----------------------Enseigne end---------------------------------------
    # -----------------------Inscrit start---------------------------------------
    path('inscrits/', views.InscritList.as_view()),
    path('inscrit/create/', views.CreatInscrit.as_view()),
    path('inscrit/<pk>/', views.OnInscrit.as_view()),
    path('inscrit/<pk>/update/', views.InscritUpdate.as_view()),
    path('inscrit/<pk>/destroy/', views.InscritDestroy.as_view()),
    # -----------------------Inscrit end---------------------------------------

]
# -------------------------------------------settings.py--------------------------------------------------------
# -*- coding: utf-8 -*-
"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 5.2.8.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ja-$@f=q_hb(1802970mhg-qy!k^+3j+c%^_)xye=!c&f)ynty'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

MEDIA_URS = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'api.apps.ApiConfig',
    'rest_framework'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': BASE_DIR / 'db.sqlite3',
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'school',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST' : '127.0.0.1',
        'PORT' : '3307',
        'OPTIONS' : {
            'init_command': "SET sql_mode = 'STRICT_TRANS_TABLES'"
        }
    }
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': 'MyBd',          # nom de ta base PostgreSQL
    #     'USER': 'postgres',           # ton utilisateur PostgreSQL
    #     'PASSWORD': 'root',  # ton mot de passe PostgreSQL
    #     'HOST': 'localhost',
    #     'PORT': '5432',
    # }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
