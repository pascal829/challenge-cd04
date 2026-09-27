"""
Logique métier du Challenge Jeunes Inter-Départemental (04/05).

Implémente les Articles 5 à 9 du règlement :
- Attribution des points par épreuve (Article 5)
- Classement général et condition de compétitivité (Article 6)
- Règles de départage en cas d'égalité (Article 7)
- Classement des clubs : points de performance + bonus de participation (Article 9)
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from .models import Archer, Club, Epreuve, Resultat


# ---------------------------------------------------------------------------
# Classement individuel par catégorie (Âge / Arme / Sexe)
# ---------------------------------------------------------------------------

@dataclass
class LigneClassementArcher:
    archer: Archer
    total_points: int = 0
    nb_victoires: int = 0
    nb_participations: int = 0

    @property
    def cle_tri(self):
        """
        Clé de tri pour départager les ex-æquo au classement général (Article 7) :
        1) le plus de points,
        2) le plus de victoires (places de 1er),
        3) le plus de participations,
        4) le plus jeune (âge civil à la dernière épreuve du challenge).
        Le tri Python étant croissant, on inverse les 3 premiers critères,
        et on utilise l'âge (en jours, plus petit = plus jeune = mieux classé).
        """
        derniere_epreuve = Epreuve.objects.order_by("-date").first()
        reference = derniere_epreuve.date if derniere_epreuve else date.today()
        age_jours = (reference - self.archer.date_naissance).days
        return (-self.total_points, -self.nb_victoires, -self.nb_participations, age_jours)


def classement_epreuve_categorie(
    epreuve: Epreuve, categorie_age: str, type_arc: str, sexe: str
) -> list[dict]:
    """
    Calcule automatiquement, à partir des SCORES saisis, le classement d'une
    catégorie (Âge / Arme / Sexe) pour une épreuve donnée (Article 5).

    Les archers sont triés par score décroissant. En cas d'égalité de score,
    les archers concernés reçoivent la même place ("classement sauté" : si
    deux archers sont ex-æquo à la 2e place, l'archer suivant est classé 4e),
    ce qui leur attribue bien les mêmes points, conformément à l'Article 5.

    Retourne une liste de dicts : {"archer", "score", "place", "points"},
    triée du meilleur score au moins bon.
    """
    resultats = list(
        Resultat.objects.filter(
            epreuve=epreuve,
            archer__categorie_age=categorie_age,
            archer__type_arc=type_arc,
            archer__sexe=sexe,
            archer__licence_a_jour=True,
        ).select_related("archer").order_by("-score", "archer__nom")
    )

    lignes = []
    dernier_score = None
    place_courante = 0
    for rang, res in enumerate(resultats, start=1):
        if res.score != dernier_score:
            place_courante = rang
            dernier_score = res.score
        lignes.append({
            "archer": res.archer,
            "score": res.score,
            "place": place_courante,
            "points": Resultat.points_pour_place(place_courante),
        })
    return lignes


def classement_categorie(categorie_age: str, type_arc: str, sexe: str) -> list[LigneClassementArcher]:
    """
    Classement général d'une catégorie (Âge / Arme / Sexe), toutes épreuves confondues.
    Les places et points de chaque épreuve sont recalculés à partir des scores
    (voir `classement_epreuve_categorie`), puis cumulés. Retourne les archers
    triés du meilleur au moins bon, en appliquant les critères de départage de
    l'Article 7.
    """
    archers = Archer.objects.filter(
        categorie_age=categorie_age, type_arc=type_arc, sexe=sexe, licence_a_jour=True
    )

    lignes = {archer.id: LigneClassementArcher(archer=archer) for archer in archers}

    for epreuve in Epreuve.objects.all():
        for ligne_ep in classement_epreuve_categorie(epreuve, categorie_age, type_arc, sexe):
            ligne = lignes.get(ligne_ep["archer"].id)
            if ligne is None:
                continue
            ligne.total_points += ligne_ep["points"]
            ligne.nb_participations += 1
            if ligne_ep["place"] == 1:
                ligne.nb_victoires += 1

    return sorted(lignes.values(), key=lambda l: l.cle_tri)


def vainqueur_categorie(categorie_age: str, type_arc: str, sexe: str) -> LigneClassementArcher | None:
    """
    Détermine le vainqueur d'une catégorie, en appliquant l'Article 6 :
    - être 1er de sa catégorie,
    - condition de compétitivité : au moins 2 archers ayant participé à au moins
      une épreuve dans cette catégorie sur l'ensemble du challenge.
    Retourne None si aucun vainqueur ne peut être désigné (catégorie non compétitive
    ou vide).
    """
    classement = classement_categorie(categorie_age, type_arc, sexe)
    archers_ayant_participe = [l for l in classement if l.nb_participations > 0]

    if len(archers_ayant_participe) < 2:
        return None  # Article 6 : un archer seul dans sa catégorie ne peut pas gagner

    return archers_ayant_participe[0]


def toutes_les_categories() -> list[tuple[str, str, str]]:
    """Génère les 16 combinaisons possibles Âge (4) x Arme (2) x Sexe (2)."""
    categories = []
    for age, _ in Archer.CATEGORIE_AGE_CHOICES:
        for arc, _ in Archer.TYPE_ARC_CHOICES:
            for sexe, _ in Archer.SEXE_CHOICES:
                categories.append((age, arc, sexe))
    return categories


def classement_general_complet() -> dict[tuple[str, str, str], list[LigneClassementArcher]]:
    """Classement pour chacune des catégories existantes (Article 3)."""
    return {cat: classement_categorie(*cat) for cat in toutes_les_categories()}


# ---------------------------------------------------------------------------
# Classement des clubs (Article 9)
# ---------------------------------------------------------------------------

POINTS_PERFORMANCE_CLUB = {1: 50, 2: 30, 3: 10}


def _palier_bonus_participation(pourcentage: float) -> int:
    """Grille de bonus de participation du club (Article 9.2)."""
    if pourcentage >= 50:
        return 80
    if pourcentage >= 25:
        return 50
    if pourcentage >= 10:
        return 25
    return 10


def points_performance_club_pour_epreuve(epreuve: Epreuve) -> dict[int, int]:
    """
    Points de performance gagnés par chaque club sur une épreuve donnée :
    chaque 1er/2e/3e de catégorie (place calculée à partir des scores) rapporte
    50/30/10 points à son club (Article 9.1), cumulables sur les 16 catégories
    Âge/Arme/Sexe.
    """
    points_par_club = defaultdict(int)
    for categorie in toutes_les_categories():
        for ligne in classement_epreuve_categorie(epreuve, *categorie):
            if ligne["place"] in POINTS_PERFORMANCE_CLUB:
                points_par_club[ligne["archer"].club_id] += POINTS_PERFORMANCE_CLUB[ligne["place"]]
    return dict(points_par_club)


def points_bonus_participation_pour_epreuve(epreuve: Epreuve) -> dict[int, int]:
    """
    Bonus de participation par club pour une épreuve (Article 9.2) : dépend du
    pourcentage d'archers du club parmi le total des inscrits à l'épreuve.
    """
    resultats = Resultat.objects.filter(epreuve=epreuve).select_related("archer__club")
    total_participants = resultats.count()
    if total_participants == 0:
        return {}

    participants_par_club = defaultdict(int)
    for res in resultats:
        participants_par_club[res.archer.club_id] += 1

    bonus_par_club = {}
    for club_id, nb_participants in participants_par_club.items():
        pourcentage = (nb_participants / total_participants) * 100
        bonus_par_club[club_id] = _palier_bonus_participation(pourcentage)
    return bonus_par_club


@dataclass
class LigneClassementClub:
    club: Club
    points_performance: int = 0
    points_bonus: int = 0
    nb_victoires_individuelles: int = 0

    @property
    def total_points(self) -> int:
        return self.points_performance + self.points_bonus

    @property
    def cle_tri(self):
        """
        Tri du classement des clubs (Article 9.3) :
        1) le plus de points cumulés (performance + participation),
        2) en cas d'égalité, le plus de 1ères places individuelles.
        """
        return (-self.total_points, -self.nb_victoires_individuelles)


def classement_clubs() -> list[LigneClassementClub]:
    """Classement général des clubs sur l'ensemble des épreuves disputées."""
    lignes: dict[int, LigneClassementClub] = {
        club.id: LigneClassementClub(club=club) for club in Club.objects.all()
    }

    for epreuve in Epreuve.objects.all():
        for club_id, pts in points_performance_club_pour_epreuve(epreuve).items():
            lignes[club_id].points_performance += pts
        for club_id, pts in points_bonus_participation_pour_epreuve(epreuve).items():
            lignes[club_id].points_bonus += pts

    victoires = defaultdict(int)
    for epreuve in Epreuve.objects.all():
        for categorie in toutes_les_categories():
            for ligne_ep in classement_epreuve_categorie(epreuve, *categorie):
                if ligne_ep["place"] == 1:
                    victoires[ligne_ep["archer"].club_id] += 1
    for club_id, nb in victoires.items():
        if club_id in lignes:
            lignes[club_id].nb_victoires_individuelles = nb

    return sorted(lignes.values(), key=lambda l: l.cle_tri)
