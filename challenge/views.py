from django.shortcuts import get_object_or_404, render

from .models import Archer, Epreuve
from .services import (
    classement_categorie,
    classement_clubs,
    classement_epreuve_categorie,
    vainqueur_categorie,
)


LABELS_AGE = dict(Archer.CATEGORIE_AGE_CHOICES)
LABELS_ARC = dict(Archer.TYPE_ARC_CHOICES)
LABELS_SEXE = dict(Archer.SEXE_CHOICES)


def accueil(request):
    epreuves = Epreuve.objects.all()
    return render(request, "challenge/accueil.html", {"epreuves": epreuves})


def reglement(request):
    return render(request, "challenge/reglement.html")


def classement_general(request):
    """
    Vue d'ensemble : pour chaque catégorie (Âge/Arme/Sexe) qui compte au moins
    un résultat, affiche le classement complet et désigne le vainqueur en
    appliquant la condition de compétitivité de l'Article 6.
    """
    blocs = []
    for age_code, age_label in Archer.CATEGORIE_AGE_CHOICES:
        for arc_code, arc_label in Archer.TYPE_ARC_CHOICES:
            for sexe_code, sexe_label in Archer.SEXE_CHOICES:
                lignes = classement_categorie(age_code, arc_code, sexe_code)
                lignes = [l for l in lignes if l.nb_participations > 0]
                if not lignes:
                    continue
                vainqueur = vainqueur_categorie(age_code, arc_code, sexe_code)
                blocs.append({
                    "titre": f"{age_label} — {arc_label} — {sexe_label}",
                    "lignes": lignes,
                    "vainqueur": vainqueur.archer if vainqueur else None,
                    "competitif": len(lignes) >= 2,
                })

    return render(request, "challenge/classement_general.html", {"blocs": blocs})


def detail_epreuve(request, epreuve_id):
    """
    Affiche, pour une épreuve donnée, le classement de chaque catégorie
    calculé automatiquement à partir des scores saisis (Article 5) : place et
    points sont recalculés en direct, il suffit d'avoir saisi les scores dans
    l'administration.
    """
    epreuve = get_object_or_404(Epreuve, pk=epreuve_id)

    blocs = []
    for age_code, age_label in Archer.CATEGORIE_AGE_CHOICES:
        for arc_code, arc_label in Archer.TYPE_ARC_CHOICES:
            for sexe_code, sexe_label in Archer.SEXE_CHOICES:
                lignes = classement_epreuve_categorie(epreuve, age_code, arc_code, sexe_code)
                if not lignes:
                    continue
                blocs.append({
                    "titre": f"{age_label} — {arc_label} — {sexe_label}",
                    "lignes": lignes,
                })

    return render(request, "challenge/detail_epreuve.html", {"epreuve": epreuve, "blocs": blocs})


def classement_club(request):
    lignes = classement_clubs()
    return render(request, "challenge/classement_clubs.html", {"lignes": lignes})
