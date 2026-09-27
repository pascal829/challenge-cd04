from datetime import date

from django.core.management.base import BaseCommand

from challenge.models import Archer, Club, Epreuve, Resultat


class Command(BaseCommand):
    help = "Charge un jeu de données de démonstration pour tester le challenge."

    def handle(self, *args, **options):
        Resultat.objects.all().delete()
        Archer.objects.all().delete()
        Epreuve.objects.all().delete()
        Club.objects.all().delete()

        club_a = Club.objects.create(nom="Archers de Digne", departement="04")
        club_b = Club.objects.create(nom="Cie d'Arc de Gap", departement="05")
        club_c = Club.objects.create(nom="Archers de Sisteron", departement="04")

        epreuve1 = Epreuve.objects.create(discipline="SALLE", date=date(2026, 1, 18))
        epreuve2 = Epreuve.objects.create(discipline="NATURE", date=date(2026, 4, 12))

        # Catégorie U15 / VISEUR / H : 3 archers -> catégorie compétitive
        a1 = Archer.objects.create(nom="Martin", prenom="Léo", date_naissance=date(2012, 3, 1),
                                    club=club_a, sexe="H", categorie_age="U15", type_arc="VISEUR")
        a2 = Archer.objects.create(nom="Durand", prenom="Noa", date_naissance=date(2012, 6, 15),
                                    club=club_b, sexe="H", categorie_age="U15", type_arc="VISEUR")
        a3 = Archer.objects.create(nom="Petit", prenom="Enzo", date_naissance=date(2011, 9, 20),
                                    club=club_a, sexe="H", categorie_age="U15", type_arc="VISEUR")

        # Épreuve 1 : Léo et Noa font le même score -> ex-aequo 1ers, Enzo 3e
        # (le classement sauté est calculé automatiquement à partir des scores)
        Resultat.objects.create(archer=a1, epreuve=epreuve1, score=520)
        Resultat.objects.create(archer=a2, epreuve=epreuve1, score=520)
        Resultat.objects.create(archer=a3, epreuve=epreuve1, score=480)

        # Épreuve 2 : Léo 1er, Enzo 2e, Noa 3e
        Resultat.objects.create(archer=a1, epreuve=epreuve2, score=610)
        Resultat.objects.create(archer=a3, epreuve=epreuve2, score=590)
        Resultat.objects.create(archer=a2, epreuve=epreuve2, score=555)

        # Catégorie U11 / NU / F : un seul archer -> catégorie NON compétitive (Article 6)
        Archer.objects.create(nom="Roux", prenom="Alice", date_naissance=date(2016, 5, 1),
                               club=club_c, sexe="F", categorie_age="U11", type_arc="NU")

        self.stdout.write(self.style.SUCCESS("Données de démonstration chargées."))
