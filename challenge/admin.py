from django.contrib import admin
from django.utils.html import format_html

from .models import Archer, Club, Epreuve, Resultat
from .services import classement_epreuve_categorie


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("nom", "departement", "apercu_logo")
    list_filter = ("departement",)
    search_fields = ("nom",)

    @admin.display(description="Logo")
    def apercu_logo(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="height:40px; width:auto; border-radius:4px;">', obj.logo.url
            )
        return "—"


@admin.register(Archer)
class ArcherAdmin(admin.ModelAdmin):
    list_display = (
        "nom", "prenom", "club", "sexe", "categorie_age", "type_arc", "licence_a_jour",
    )
    list_filter = ("club", "sexe", "categorie_age", "type_arc", "licence_a_jour")
    search_fields = ("nom", "prenom", "numero_licence")


@admin.register(Epreuve)
class EpreuveAdmin(admin.ModelAdmin):
    list_display = ("discipline", "edition", "date", "lieu")
    list_filter = ("edition",)


@admin.register(Resultat)
class ResultatAdmin(admin.ModelAdmin):
    list_display = ("archer", "epreuve", "score", "place_calculee", "points_calcules")
    list_filter = ("epreuve", "archer__categorie_age", "archer__type_arc", "archer__sexe")
    autocomplete_fields = ("archer",)
    search_fields = ("archer__nom", "archer__prenom")

    @admin.display(description="Place (calculée)")
    def place_calculee(self, obj):
        for ligne in classement_epreuve_categorie(
            obj.epreuve, obj.archer.categorie_age, obj.archer.type_arc, obj.archer.sexe
        ):
            if ligne["archer"].id == obj.archer_id:
                return f"{ligne['place']}e"
        return "—"

    @admin.display(description="Points (calculés)")
    def points_calcules(self, obj):
        for ligne in classement_epreuve_categorie(
            obj.epreuve, obj.archer.categorie_age, obj.archer.type_arc, obj.archer.sexe
        ):
            if ligne["archer"].id == obj.archer_id:
                return ligne["points"]
        return "—"
