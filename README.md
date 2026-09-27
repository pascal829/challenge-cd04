# Challenge Jeunes Inter-Départemental (04 / 05) — Application Django

Application Django permettant de gérer les résultats et de calculer
automatiquement les classements du Challenge Jeunes Inter-Départemental
(comités 04 et 05), conformément au règlement fourni.

## Ce que l'application calcule

- **Article 3** — 16 catégories de classement : 4 tranches d'âge (U11/U13/U15/U18)
  × 2 types d'arc (Nu / Viseur) × 2 sexes.
- **Article 4** — les 7 épreuves du challenge (Salle, Fédéral, Campagne, Nature,
  3D, Beursault, Run Archery).
- **Article 5** — barème de points par épreuve (1er = 40, 2e = 30, 3e = 20,
  tout autre participant classé = 10), avec gestion des ex-æquo par
  "classement sauté" (voir plus bas).
- **Article 6** — classement général par catégorie, et **condition de
  compétitivité** : un archer seul dans sa catégorie ne peut pas être déclaré
  vainqueur (il faut au moins 2 archers ayant participé à au moins une épreuve).
- **Article 7** — critères de départage en cas d'égalité au classement
  général : nombre de victoires, puis nombre de participations, puis l'archer
  le plus jeune.
- **Article 9** — classement des clubs : points de performance (50/30/10 par
  podium individuel) + points bonus de participation (10/25/50/80 selon le
  pourcentage d'archers du club parmi les participants de l'épreuve), et
  départage par nombre de victoires individuelles en cas d'égalité.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate        # sous Windows : venv\Scripts\activate
pip install django

python3 manage.py migrate
python3 manage.py createsuperuser   # pour accéder à /admin/
python3 manage.py runserver
```

Puis ouvrir http://127.0.0.1:8000/ dans un navigateur.

- **/** : liste des épreuves du challenge
- **/classement/** : classement individuel par catégorie, avec vainqueurs
- **/classement-clubs/** : classement général des clubs
- **/admin/** : interface d'administration pour saisir clubs, archers,
  épreuves et résultats

## Charger des données de démonstration (optionnel)

Une commande est fournie pour vérifier rapidement le fonctionnement des
calculs (3 clubs, 4 archers, 2 épreuves, dont un cas d'égalité) :

```bash
python3 manage.py donnees_demo
```

## Saisie des résultats — il suffit d'entrer le score

Un `Resultat` = le **score** obtenu par un archer sur une épreuve (dans
l'administration : Club → Archer → Épreuve → Score). **La place et les
points sont calculés automatiquement**, pas besoin de les saisir :

- les archers d'une même catégorie (Âge / Arme / Sexe) sont classés par
  score décroissant sur chaque épreuve ;
- en cas d'égalité de score, les archers concernés sont ex-æquo et reçoivent
  la même place et les mêmes points ("classement sauté" : si deux archers
  sont ex-æquo à la 1ère place, l'archer suivant est classé 3e) ;
- le barème de l'Article 5 (40/30/20/10 points) est ensuite appliqué à la
  place calculée.

Après avoir saisi les scores d'une épreuve, on peut vérifier immédiatement
le classement obtenu sur la page **"/epreuve/&lt;id&gt;/"** (accessible depuis
la page d'accueil en cliquant sur l'épreuve), avant même que le classement
général ne soit consulté.

## Logo des clubs

Chaque club peut avoir un logo (champ facultatif dans l'administration,
onglet Club). Une fois ajouté, il s'affiche automatiquement sur le
classement des clubs et à côté du nom du club dans le classement individuel.

Formats courants acceptés (PNG, JPG...). Le package `Pillow` est nécessaire
pour l'upload d'images — il est à installer avec Django :

```bash
pip install django Pillow
```

En développement (`DEBUG = True`), les logos uploadés sont automatiquement
servis par `runserver` ; aucune configuration supplémentaire n'est requise.

## Structure du projet

```
challenge_project/
├── manage.py
├── challenge_project/       # configuration Django (settings, urls)
└── challenge/                # application métier
    ├── models.py             # Club, Archer, Epreuve, Resultat
    ├── services.py           # logique de calcul des classements (Articles 5-9)
    ├── admin.py               # interface d'administration pour la saisie
    ├── views.py / urls.py / templates/   # pages web de consultation
    └── management/commands/donnees_demo.py
```

Toute la logique de calcul (barème, condition de compétitivité, départages,
points des clubs) est centralisée dans `challenge/services.py`, avec des
docstrings faisant référence à l'article du règlement concerné — n'hésitez
pas à me solliciter si le règlement évolue d'une édition à l'autre.
