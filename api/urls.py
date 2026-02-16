from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    # -----------------------Etablissement start---------------------------------------
    path('etablissements/', views.EtablissementList.as_view()),
    path('etablissement/create/', views.CreatEtablissement.as_view()),
    path('etablissement/<uuid:pk>/', views.OnEtablissement.as_view()),
    path('etablissement/<uuid:pk>/update/', views.EtablissementUpdate.as_view()),
    path('etablissement/<uuid:pk>/destroy/', views.EtablissementDestroy.as_view()),
    # path('etablissement/<uuid:pk_etab>/dashboard/', views.EtablissementDashboardView.as_view()),
    # -----------------------Etablissement end---------------------------------------
    # -----------------------Enseignant start---------------------------------------
    path('enseignants/', views.EnseignantList.as_view()),
    path('enseignant/create/', views.CreatEnseignant.as_view()),
    path('enseignant/<uuid:pk>/', views.OnEnseignant.as_view()),
    path('enseignant/<uuid:pk>/update/', views.EnseignantUpdate.as_view()),
    path('enseignant/<uuid:pk>/destroy/', views.EnseignantDestroy.as_view()),
    path('enseignantsDisponible/<uuid:id_etab>/<annee_scolaire>/', views.ListeEtablissementEnseignant.as_view()),
    # path('enseignant/<uuid:pk_ens>/<uuid:pk_etab>/dashboard/', views.EnseignantDashboardView.as_view()),
    # -----------------------Enseignant end---------------------------------------
    # -----------------------Eleve start---------------------------------------
    path('eleves/', views.EleveList.as_view()),
    path('eleve/create/', views.CreatEleve.as_view()),
    path('eleve/<uuid:pk>/', views.OnEleve.as_view()),
    path('eleve/<uuid:pk>/update/', views.EleveUpdate.as_view()),
    path('eleve/<uuid:pk>/destroy/', views.EleveDestroy.as_view()),
    path('eleve/<uuid:pk>/dashboard/', views.EleveDashboardView.as_view()), 
    path('etablissementClasseStatistiquesEtInfos/<uuid:id_etab>/<annee_scolaire>/<uuid:id_disponible>/', views.EtablissementClasseStatistiquesEtInfos.as_view()),
    # -----------------------Eleve end---------------------------------------
    # -----------------------Matiere start---------------------------------------
    path('matieres/', views.MatiereList.as_view()),
    path('matiere/create/', views.CreatMatiere.as_view()),
    path('matiere/<uuid:pk>/', views.OnMatiere.as_view()),
    path('matiere/<uuid:pk>/update/', views.MatiereUpdate.as_view()),
    path('matiere/<uuid:pk>/destroy/', views.MatiereDestroy.as_view()),
    # -----------------------Matiere end---------------------------------------
    # -----------------------Poste start---------------------------------------
    path('postes/', views.PosteList.as_view()),
    path('poste/create/', views.CreatPoste.as_view()),
    path('poste/<uuid:pk>/', views.OnPoste.as_view()),
    path('poste/<uuid:pk>/update/', views.PosteUpdate.as_view()),
    path('poste/<uuid:pk>/destroy/', views.PosteDestroy.as_view()),
    # -----------------------Post end---------------------------------------
    # -----------------------Staff start---------------------------------------
    path('staffs/', views.StaffList.as_view()),
    path('staff/create/', views.CreatStaff.as_view()),
    path('staff/<uuid:pk>/', views.OnStaff.as_view()),
    path('staff/<uuid:pk>/update/', views.StaffUpdate.as_view()),
    path('staff/<uuid:pk>/destroy/', views.StaffDestroy.as_view()),
    path('loginStaff/', views.LoginStaff.as_view()),
    # -----------------------Staff end---------------------------------------
    # -----------------------Classe start---------------------------------------
    path('classes/', views.ClasseList.as_view()),
    path('classe/create/', views.CreatClasse.as_view()),
    path('classe/<uuid:pk>/', views.OnClasse.as_view()),
    path('classe/<uuid:pk>/update/', views.ClasseUpdate.as_view()),
    path('classe/<uuid:pk>/destroy/', views.ClasseDestroy.as_view()),
    path('classesDisponible/<uuid:id_etab>/', views.ListeEtablissementClasse.as_view()),
    path('classeDisponibleEtablissement/', views.ClasseDisponibleEtablissement.as_view()),
    path('listeClasseDisponibleEtablissement/<uuid:id_etab>/', views.ListeClasseDisponibleEtablissement.as_view()),
    # -----------------------Classe end---------------------------------------
    # -----------------------Cour start---------------------------------------
    path('cours/', views.CourList.as_view()),
    path('cour/create/', views.CreatCour.as_view()),
    path('cour/<uuid:pk>/', views.OnCour.as_view()),
    path('cour/<uuid:pk>/update/', views.CourUpdate.as_view()),
    path('cour/<uuid:pk>/destroy/', views.CourDestroy.as_view()),
    path('coursClasseEtablissement/<uuid:id_etab>/<annee_scolaire>/', views.ListeEtablissementCours.as_view()),
    path('listeEtablissementClasseCours/<uuid:id_etab>/<annee_scolaire>/<uuid:id_disponible>/', views.ListeEtablissementClasseCours.as_view()),
    # -----------------------Cour end---------------------------------------
    # -----------------------NiveauEtude start---------------------------------------
    path('niveauEtudes/', views.NiveauEtudeList.as_view()),
    path('niveauEtude/create/', views.CreatNiveauEtude.as_view()),
    # path('niveauEtude/<uuid:pk>/', views.OnNiveauEtude.as_view()),
    # path('niveauEtude/<uuid:pk>/update/', views.NiveauEtudeUpdate.as_view()),
    # path('niveauEtude/<uuid:pk>/destroy/', views.NiveauEtudeDestroy.as_view()),
    # -----------------------Disponible start---------------------------------------
    path('disponibles/', views.DisponibleList.as_view()),
    path('disponible/create/', views.CreatDisponible.as_view()),
    path('disponible/<uuid:pk>/', views.OnDisponible.as_view()),
    path('disponible/<uuid:pk>/update/', views.DisponibleUpdate.as_view()),
    path('disponible/destroy/<uuid:pk>/', views.DisponibleDestroy.as_view()),
    # -----------------------Disponible end---------------------------------------
    # -----------------------Enseigne start---------------------------------------
    path('enseignes/', views.EnseigneList.as_view()),
    path('enseigne/create/', views.CreatEnseigne.as_view()),
    path('enseigne/<uuid:pk>/', views.OnEnseigne.as_view()),
    path('enseigne/<uuid:pk>/update/', views.EnseigneUpdate.as_view()),
    path('enseigne/<uuid:pk>/destroy/', views.EnseigneDestroy.as_view()),
    # -----------------------Enseigne end---------------------------------------
    # -----------------------Inscrit start---------------------------------------
    path('inscrits/', views.InscritList.as_view()),
    path('inscrit/create/', views.CreatInscrit.as_view()),
    path('inscrit/<uuid:pk>/', views.OnInscrit.as_view()),
    path('inscrit/<uuid:pk>/update/', views.InscritUpdate.as_view()),
    path('inscrit/<uuid:pk>/destroy/', views.InscritDestroy.as_view()),
    # -----------------------Inscrit end---------------------------------------
    #=============================PRESENCE=====================================
    path('presence/', views.PresenceListCreateView.as_view()),
    path('presence/<uuid:pk>/', views.PresenceDetailView.as_view()),
    #=============================INTERROGATION=====================================
    # path('interrogation/', views.InterrogationListCreateView.as_view()),
    # path('interrogation/<uuid:pk>/', views.InterrogationDetailView.as_view()),
    #=============================DEPENCE=====================================
    path('depence/', views.DepenseListCreateView.as_view()),
    path('depence/<uuid:pk>/', views.DepenseDetailView.as_view()),
    #=============================DEVOIR=====================================
    # path('devoir/', views.DevoirListCreateView.as_view()),
    # path('devoir/<uuid:pk>/', views.DevoirDetailView.as_view()),
    #============================= AUTRE URL=====================================
    path('etablissementEleves/<uuid:id_etab>/<str:annee_scolaire>/', views.ListeEtablissementEleve.as_view()),
    path('listeEleveEtablissementEleve/<uuid:id_etab>/<str:annee_scolaire>/<uuid:id_disponible>/', views.ListeEleveEtablissementEleve.as_view()),
    path('creatEmploitDuTemps/', views.CreatEmploiDuTemps.as_view()),
    # path('emploiDuTempsEtablissement/<uuid:id_etab>/<str:annee_scolaire>/', views.ListeEtablissementEmploi.as_view()),
    path('emploiDuTempsClasseEtablissement/<uuid:id_etab>/<str:annee_scolaire>/<uuid:id_disponible>/', views.EmploiDuTempsClasseEtablissement.as_view()),
    path('creatEvaluation/<uuid:id_etab>/', views.CreatEvaluation.as_view()),
    # -----------------------Annee start ---------------------------------------
    path('annees/', views.AnneeScolaireList.as_view()),
    path('annee/create/', views.AnneeScolaireCreat.as_view()),
    path('annee/<uuid:pk>/', views.OnAnneeScolaire.as_view()),
    path('annee/<uuid:pk>/update/', views.AnneeScolaireUpdate.as_view()),
    path('annee/<uuid:pk>/destroy/', views.AnneeScolaireDestroy.as_view()),
    path('listeEtablissementAnneeScolaire/<uuid:id_etab>/', views.ListeEtablissementAnneeScolaire.as_view()),
    path('ajouterAnneeScolaire/<uuid:id_etab>/', views.AjouterAnneeScolaire.as_view())
]
