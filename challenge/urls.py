from django.urls import path

from . import views

app_name = "challenge"

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("reglement/", views.reglement, name="reglement"),
    path("classement/", views.classement_general, name="classement_general"),
    path("epreuve/<int:epreuve_id>/", views.detail_epreuve, name="detail_epreuve"),
    path("classement-clubs/", views.classement_club, name="classement_clubs"),
]
