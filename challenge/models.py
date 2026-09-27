from django.db import models
from django.core.exceptions import ValidationError
from datetime import date


class Club(models.Model):
    DEPARTEMENTS = [
        ("04", "Alpes-de-Haute-Provence (04)"),
        ("05", "Hautes-Alpes (05)"),
    ]

    nom = models.CharField(max_length=150, unique=True)
    departement = models.CharField(max_length=2, choices=DEPARTEMENTS)
    logo = models.ImageField(
        upload_to="clubs/",
        blank=True,
        null=True,
        help_text="Logo du club (facultatif), affiché sur le classement des clubs.",
    )

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.departement})"


class Archer(models.Model):
    SEXE_CHOICES = [
        ("F", "Fille / Femme"),
        ("H", "Garçon / Homme"),
    ]
    CATEGORIE_AGE_CHOICES = [
        ("U11", "U11"),
        ("U13", "U13"),
        ("U15", "U15"),
        ("U18", "U18"),
    ]
    TYPE_ARC_CHOICES = [
        ("NU", "Arc Nu (Barebow)"),
        ("VISEUR", "Arc avec Viseur (Classique / Poulies)"),
    ]

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="archers")
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    categorie_age = models.CharField(max_length=3, choices=CATEGORIE_AGE_CHOICES)
    type_arc = models.CharField(max_length=6, choices=TYPE_ARC_CHOICES)
    licence_a_jour = models.BooleanField(
        default=True,
        help_text="Doit être coché pour que l'archer soit éligible (Article 2).",
    )
    numero_licence = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.club.nom})"

    def age_a_date(self, reference: date) -> int:
        """Âge civil de l'archer à une date de référence (Article 7, critère 3)."""
        return (
            reference.year
            - self.date_naissance.year
            - ((reference.month, reference.day) < (self.date_naissance.month, self.date_naissance.day))
        )

    @property
    def categorie_key(self):
        """Clé identifiant la catégorie de classement : Âge / Arme / Sexe (Article 3)."""
        return (self.categorie_age, self.type_arc, self.sexe)


class Epreuve(models.Model):
    DISCIPLINE_CHOICES = [
        ("SALLE", "Tir en Salle"),
        ("FEDERAL", "Tir Fédéral (Tir à l'Extérieur)"),
        ("CAMPAGNE", "Tir de Campagne"),
        ("NATURE", "Tir Nature"),
        ("3D", "Tir 3D"),
        ("BEURSAULT", "Tir Beursault"),
        ("RUN", "Run Archery"),
    ]

    discipline = models.CharField(max_length=10, choices=DISCIPLINE_CHOICES, unique=True)
    edition = models.PositiveIntegerField(default=2026)
    date = models.DateField()
    lieu = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.get_discipline_display()} ({self.date})"


class Resultat(models.Model):
    """
    Un résultat = le score obtenu par un archer sur une épreuve donnée.

    La place au sein de sa catégorie (Âge / Arme / Sexe), et donc les points
    (Article 5), sont calculés automatiquement à partir des scores de tous
    les archers de la même catégorie sur cette épreuve (voir
    `challenge.services.classement_epreuve_categorie`) — inutile de saisir la
    place à la main.

    Gestion des égalités : si deux archers obtiennent le même score, ils sont
    considérés ex-æquo et reçoivent tous les deux les points de la place
    concernée ; l'archer suivant "saute" la place correspondante (classement
    sauté), exactement comme dans une compétition classique.
    """

    BAREME = {1: 40, 2: 30, 3: 20}
    POINTS_AUTRES_PARTICIPANTS = 10

    archer = models.ForeignKey(Archer, on_delete=models.CASCADE, related_name="resultats")
    epreuve = models.ForeignKey(Epreuve, on_delete=models.CASCADE, related_name="resultats")
    score = models.PositiveIntegerField(
        help_text="Score obtenu par l'archer sur cette épreuve. Le classement et les points "
                   "sont calculés automatiquement, il n'y a pas besoin de saisir une place."
    )

    class Meta:
        unique_together = ("archer", "epreuve")
        ordering = ["epreuve", "-score"]

    def __str__(self):
        return f"{self.archer} - {self.epreuve} - {self.score} pts"

    def clean(self):
        if not self.archer.licence_a_jour:
            raise ValidationError(
                "Cet archer n'a pas de licence à jour (Article 2) et ne peut pas être classé."
            )

    @classmethod
    def points_pour_place(cls, place: int) -> int:
        return cls.BAREME.get(place, cls.POINTS_AUTRES_PARTICIPANTS)
