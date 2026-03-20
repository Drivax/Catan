# Catan Simulator - Documentation Technique

## Vue d'ensemble

Ce projet est une implémentation complète du jeu de plateau Catan, construite de zéro en Python. Il comprend un moteur de jeu fonctionnel, deux types d'agents autonomes (aléatoire et intelligent), un système de fine-tuning par optimisation bayésienne avec recuit simulé, ainsi qu'une visualisation interactive du plateau via pygame.

L'objectif principal est de disposer d'un environnement de simulation rapide pour comparer des stratégies, optimiser des paramètres comportementaux, et étudier l'émergence de tactiques dans un contexte de jeu de plateau multi-joueurs.

---

## Structure du projet

```
Catan/
├── game/
│   ├── map.py           - Coordonnées de la grille hexagonale, positions des cases, ports
│   ├── board.py         - Plateau de jeu : tuiles, bâtiments, routes, voleur, production
│   ├── core.py          - Moteur de jeu : tours, dés, échanges, victoire
│   ├── player.py        - Ressources, construction, échanges d'un joueur
│   └── rules.py         - Constantes : coûts, points, ressources
├── agents/
│   ├── base.py          - Interface abstraite Agent + dataclass Action
│   ├── random_agent.py  - Agent aléatoire avec paramètres comportementaux configurables
│   └── smart_agent.py   - Agent heuristique avec scoring de vertex, routes, voleur, trades
├── main.py              - Point d'entrée : configure les agents et lance une comparaison
├── train.py             - Alias de lancement pour la comparaison d'agents
├── fine_tuning.py       - Optimisation des paramètres par recuit simulé
├── run_finetuning.py    - Script de lancement du fine-tuning
├── charts.py            - Visualisation des résultats de comparaison (matplotlib)
├── vizualize.py         - Rendu graphique du plateau en temps réel (pygame)
├── test_baseline.py     - Test de performance de référence de SmartAgent
└── requirements.txt     - Dépendances Python
```

---

## Fondements mathématiques : la grille hexagonale

### Système de coordonnées axiales

Le plateau de Catan est une grille d'hexagones. La représentation la plus naturelle pour ce type de grille utilise un système de coordonnées axiales `(q, r)`, où chaque hexagone est identifié par deux entiers. Cette représentation évite la redondance du système cubique `(x, y, z)` sous contrainte `x + y + z = 0` tout en conservant ses propriétés de distance.

La disposition standard du plateau Catan comprend 19 hexagones organisés en losange tronqué :

```
Ligne 0 :  3 cases  (q ∈ {0, 1, 2},     r = -2)
Ligne 1 :  4 cases  (q ∈ {-1, 0, 1, 2}, r = -1)
Ligne 2 :  5 cases  (q ∈ {-2, ..., 2},  r =  0)
Ligne 3 :  4 cases  (q ∈ {-2, -1, 0, 1}, r = 1)
Ligne 4 :  3 cases  (q ∈ {-2, -1, 0},   r =  2)
```

### Conversion axiale vers pixel (flat-top)

Pour les hexagones en orientation "flat-top" (côté plat en haut), la conversion des coordonnées axiales `(q, r)` vers des coordonnées cartésiennes `(x, y)` suit les formules :

```
x = R * (3/2 * q)
y = R * (sqrt(3)/2 * q + sqrt(3) * r)
```

où `R` est le rayon de l'hexagone (distance centre-sommet), ici `R = 70` pixels.

La largeur d'un hexagone est `2R` et sa hauteur est `R * sqrt(3)`. Le rayon intérieur (centre vers milieu d'un côté) vaut `R * sqrt(3) / 2`.

### Coordonnées des sommets (vertices)

Chaque hexagone possède 6 sommets. Pour éviter la redondance (un sommet est partagé par jusqu'à 3 hexagones), les sommets sont encodés en coordonnées entières par multiplication par 2 :

```python
def get_corners(q, r):
    qq = q * 2
    rr = r * 2
    return [
        (qq + 2, rr + 0),   # Nord-Est
        (qq + 1, rr - 1),   # Est
        (qq    , rr - 2),   # Sud-Est
        (qq - 2, rr    ),   # Sud-Ouest
        (qq - 1, rr + 1),   # Ouest
        (qq    , rr + 2),   # Nord-Ouest
    ]
```

Ce schéma garantit que deux hexagones adjacents partagent exactement les mêmes identifiants de sommets. Le graphe de voisinage des sommets `vertex_neighbors` est construit par itération sur toutes les arêtes de tous les hexagones.

La conversion inverse d'un vertex `(vq, vr)` vers pixel est :

```
q = vq / 2,  r = vr / 2
x = R * (3/2 * q)
y = R * sqrt(3) * (r + q / 2)
```

---

## Probabilités des dés

Le mécanisme central de production de ressources repose sur le lancer de deux dés à 6 faces. La distribution de la somme de deux dés uniformes est une distribution triangulaire discrète sur `{2, ..., 12}`.

Le nombre de façons d'obtenir chaque valeur, et la probabilité associée :

| Valeur | Combinaisons | Probabilité |
|--------|-------------|-------------|
| 2      | 1           | 1/36 ≈ 2.78% |
| 3      | 2           | 2/36 ≈ 5.56% |
| 4      | 3           | 3/36 ≈ 8.33% |
| 5      | 4           | 4/36 ≈ 11.11% |
| 6      | 5           | 5/36 ≈ 13.89% |
| 7      | 6           | 6/36 ≈ 16.67% |
| 8      | 5           | 5/36 ≈ 13.89% |
| 9      | 4           | 4/36 ≈ 11.11% |
| 10     | 3           | 3/36 ≈ 8.33% |
| 11     | 2           | 2/36 ≈ 5.56% |
| 12     | 1           | 1/36 ≈ 2.78% |

Les numéros 6 et 8 ont la probabilité maximale hors 7 (5/36 chacun). Le 7 déclenche le voleur et ne produit pas de ressources. Les agents tiennent compte de ces probabilités lors du placement initial des colonies : une case numérotée 6 ou 8 vaut nettement plus qu'une case numérotée 2 ou 12.

L'espérance de production par tour pour une colonie sur un sommet adjacent aux cases `c1, c2, c3` de numéros `n1, n2, n3` est :

```
E[production] = sum_i  P(lancer = ni) * 1  (colonie)
              = sum_i  (6 - |ni - 7|) / 36

E[production] = sum_i  P(lancer = ni) * 2  (ville)
```

---

## Distribution des ressources sur le plateau

Le plateau est initialisé avec les fréquences officielles du jeu :

| Ressource | Nombre de cases |
|-----------|----------------|
| Bois      | 4              |
| Brique    | 3              |
| Mouton    | 4              |
| Blé       | 4              |
| Minerai   | 3              |
| Désert    | 1              |
| **Total** | **19**         |

Les numéros de cases sont distribués parmi les 18 cases non-désert : `{2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12}`. Le 7 n'est jamais assigné à une case (il est réservé au voleur). Les ressources et les numéros sont mélangés aléatoirement à chaque partie.

---

## Règles de construction

### Coûts

| Construction | Coût                        | Points de victoire |
|-------------|-----------------------------|--------------------|
| Route       | 1 Bois + 1 Brique           | 0                  |
| Colonie     | 1 Bois + 1 Brique + 1 Mouton + 1 Blé | 1           |
| Ville       | 2 Blé + 3 Minerai           | 2 (net +1 sur la colonie remplacée) |

### Contrainte de distance

La règle de distance impose qu'aucune colonie ne peut être placée sur un sommet adjacent à un sommet déjà occupé. En termes de graphe : si `B` est l'ensemble des sommets occupés, un sommet `v` est valide pour une nouvelle colonie si et seulement si :

```
v ∉ B  ET  N(v) ∩ B = ∅
```

où `N(v)` est le voisinage immédiat de `v` dans le graphe des sommets.

### Limite de pièces

Chaque joueur dispose d'un stock limité : 15 routes, 5 colonies, 4 villes. Une ville remplace une colonie : la colonie est rendue au stock (`settlements_left += 1`), la ville est déposée (`cities_left -= 1`), le gain net en points est `+1` (la colonie valait déjà 1 point, la ville en vaut 2).

### Condition de victoire

La partie se termine lorsqu'un joueur atteint **10 points de victoire** (constante `VICTORY_POINTS_TO_WIN`).

---

## La plus longue route (Longest Road)

La plus longue route rapporte **2 points de victoire** au joueur ayant le chemin continu le plus long, à condition que ce chemin fasse au moins **5 segments**. Le calcul utilise un parcours en profondeur (DFS) sur le graphe des routes du joueur :

```
fonction dfs(sommet_courant, arête_précédente, ensemble_arêtes_visitées):
    longueur_max = 0
    pour chaque voisin de sommet_courant:
        arête = {sommet_courant, voisin}
        si arête ∉ arêtes_visitées:
            ajouter arête à arêtes_visitées
            longueur = 1 + dfs(voisin, arête, arêtes_visitées)
            longueur_max = max(longueur_max, longueur)
            retirer arête de arêtes_visitées
    retourner longueur_max
```

La complexité de cet algorithme est exponentielle dans le pire cas (backtracking complet), mais reste acceptable vu la taille limitée du graphe (au plus 15 routes par joueur).

Si le leader de la plus longue route perd sa position (un autre joueur prend la tête), les 2 points sont transférés immédiatement.

---

## Échanges

### Échange avec la banque

Le ratio standard est **4:1** (donner 4 unités d'une ressource pour recevoir 1 d'une autre). Les ports améliorent ce ratio :

- Port générique (3:1) : n'importe quelle ressource en triple
- Port spécifique (2:1) : une ressource particulière en double

Un joueur accède à un port si au moins une de ses colonies ou villes est placée sur l'un des deux sommets de l'arête portuaire.

### Échange entre joueurs

Lors de sa phase de tour, un joueur peut proposer un échange à un autre joueur. La logique d'acceptation du destinataire dépend de la rareté respective des ressources impliquées :

- Si le destinataire n'a pas assez de la ressource demandée : refus automatique
- Si le destinataire a un excès de la ressource à donner et manque de la ressource reçue : acceptation
- Sinon : décision probabiliste (entre 30% et 85% selon le contexte)

---

## Mécanisme du voleur

Lorsqu'un joueur lance un 7 :

1. Tout joueur ayant **plus de 7 ressources** en main doit en défausser la moitié (arrondie à l'inférieur).
2. Le joueur actif déplace le voleur sur une case de son choix. La case choisie ne produit plus tant que le voleur y reste.
3. Le joueur actif vole **1 ressource aléatoire** à un joueur adjacent à la case du voleur (s'il en existe un avec au moins 1 ressource).

---

## Phase de setup (Snake Draft)

L'initialisation des colonies de départ suit un ordre en "serpent" :

1. L'ordre des joueurs est mélangé aléatoirement.
2. Chaque joueur place une première colonie (et une route associée) dans l'ordre tiré.
3. Chaque joueur place une deuxième colonie en sens inverse.

Lors du setup, les colonies sont gratuites. Chaque colonie de départ produit immédiatement les ressources des cases adjacentes qui ont un numéro.

---

## Architecture des agents

### Interface abstraite (base.py)

Tous les agents héritent de la classe abstraite `Agent` et implémentent :

```python
def choose_action(self, game, player_id) -> Action
def choose_trade(self, game, player_id) -> dict | None
def choose_player_trade(self, game, player_id) -> Action | None
def choose_starting_settlement(self, game, player_id, valid_vertices) -> vertex | None
```

La dataclass `Action` encapsule une décision :

```python
@dataclass
class Action:
    action: str   # 'build_settlement', 'build_city', 'build_road', 'move_robber', 'pass', ...
    target: Any   # Vertex, arête (frozenset), case hexagonale, ou dict de trade
```

---

## RandomAgent

`RandomAgent` choisit ses actions uniformément parmi les options légales. Il dispose de trois paramètres comportementaux :

| Paramètre     | Type  | Description |
|---------------|-------|-------------|
| `trade_chaos` | float [0, 1] | Probabilité d'effectuer un échange désavantageux (ratio dégradé) |
| `sheep_hoarder` | bool | Si vrai, refuse systématiquement de donner du mouton |
| `dumb_thief` | bool | Si vrai, déplace toujours le voleur sur la case du joueur en tête |

Ces paramètres servent à modéliser des comportements humains non optimaux et à tester la robustesse de SmartAgent contre des adversaires variés.

---

## SmartAgent

`SmartAgent` utilise des fonctions de scoring heuristiques pour évaluer chaque décision. Il hérite de tous les paramètres de `RandomAgent` et en ajoute plusieurs :

| Paramètre          | Type  | Valeur par défaut | Description |
|--------------------|-------|-------------------|-------------|
| `prob_trade`       | float [0, 1] | 0.7 | Probabilité de tenter un échange par tour |
| `road_maker`       | int {0, 1} | 0 | Mode "constructeur de routes" : priorité aux routes et au brique |
| `greed`            | int {0, 1} | 0 | Mode "greedy" : n'accepte que les trades avantageux |
| `prob_weight`      | float | 1.0 | Poids accordé à la probabilité des dés dans le scoring de placement |
| `diversity_weight` | float | 1.0 | Poids accordé à la diversité des ressources dans le scoring |
| `city_first`       | float [0, 10] | 0.0 | Biais vers la mise à niveau en ville dès que possible |
| `port_lover`       | bool | False | Préférence forte pour les emplacements portuaires |

### Scoring du placement initial

Pour chaque sommet valide `v`, SmartAgent calcule un score composite :

```
score(v) = prob_weight * score_probabilité(v)
         + diversity_weight * diversité(v)
         + bonus_brique(v) * road_maker
         + bonus_port(v) * port_lover
```

où :

```
score_probabilité(v) = sum sur les cases c adjacentes à v :
    3.0  si numéro(c) ∈ {6, 8}
    2.0  si numéro(c) ∈ {5, 9}
    1.0  si numéro(c) ∈ {4, 10}
    0.1  sinon

diversité(v) = nombre de types de ressources distincts
               parmi les cases adjacentes à v (hors désert)
```

Le sommet de départ optimal maximise donc à la fois la production attendue et la couverture en types de ressources.

### Scoring des vertices pour construction

La fonction `_vertex_value` score les sommets disponibles en cours de partie :

```
score(v) = 0           si diversité = 1 et ressource = bois ou brique
         = 0.1         si diversité = 1 et ressource = minerai
         = score_prob + 1.0   si diversité = 2
         = score_prob + 5.0   si diversité = 3
         + 10.0        si port_lover et port accessible depuis v
```

Cette heuristique favorise fortement les sommets touchant 3 types de ressources différents, ce qui maximise l'autonomie productive.

### Scoring des routes

La fonction `_road_value` évalue l'utilité d'une arête :

```
score(arête) = 0.5 (base)
             + 3.0 pour chaque extrémité occupée par un bâtiment du joueur
             + 0.3 pour chaque extrémité libre ouvrant vers de nouveaux territoires
             + max_vertex_value(voisins libres) * 0.3
```

Les routes sont construites pour maximiser l'accès à de bons emplacements futurs.

### Stratégie du voleur (SmartAgent)

En mode normal, SmartAgent score chaque case pour le placement du voleur :

```
score(case) = sum sur les adversaires adj à la case :
    points_victoire(adversaire) * 20  si adversaire = leader
    points_victoire(adversaire) * 3   sinon
    + ressources totales(adversaire)
    + bâtiments adjacents(adversaire) * 5
```

Ce scoring priorise massivement le blocage du joueur en tête.

### Priorité des actions

L'ordre de priorité pour `choose_action` est :

1. Voleur (si dé = 7)
2. Routes (si `road_maker = 1`)
3. Mise à niveau en ville (si seuil `city_first` atteint)
4. Nouvelle colonie (si emplacement valide disponible)
5. Route pour ouvrir de nouveaux emplacements
6. Route standard
7. Passer

Le seuil de mise à niveau est calculé comme :
```
upgrade_threshold = max(1, int(4 - city_first * 0.3))
```
Ainsi `city_first = 0` requiert 4 colonies avant d'upgrader, tandis que `city_first = 10` permet d'upgrader dès la première colonie.

---

## Fine-tuning par recuit simulé

### Objectif

Trouver la combinaison de paramètres de `SmartAgent` qui maximise le taux de victoire contre un mélange réaliste d'adversaires. L'espace de recherche est à 10 dimensions (paramètres du tableau ci-dessus).

### Protocole d'évaluation

Pour chaque combinaison de paramètres testée, `games_per_eval` parties sont jouées. Les adversaires sont tirés aléatoirement :
- 50% des parties : 3 `RandomAgent` par défaut
- 25% des parties : 3 `SmartAgent` par défaut
- 25% des parties : 3 `SmartAgent` avec paramètres aléatoires

L'ordre de placement est mélangé à chaque partie. Le taux de victoire est mesuré indépendamment de la position de départ.

### Algorithme de recuit simulé

Le recuit simulé (Simulated Annealing) est une méthode de méta-heuristique inspirée du refroidissement contrôlé des métaux. Elle permet d'explorer l'espace des paramètres en acceptant parfois des solutions moins bonnes pour éviter les minima locaux.

A chaque itération `t` parmi `N` total :

1. Générer un candidat `theta'` par mutation de la solution courante `theta`.
2. Evaluer le taux de victoire `w(theta')`.
3. Calculer `delta = w(theta') - w(theta)`.
4. Température courante : `T(t) = 1 - 0.9 * (t / N)`, qui vaut `T(0) = 1` en début d'optimisation et `T(N) = 0.1` à la fin (refroidissement linéaire).
5. Probabilité d'acceptation :
   - Si `delta > 0` : acceptation certaine (amélioration).
   - Si `delta <= 0` : acceptation avec probabilité `exp(delta / max(0.01, T(t)))`.

Plus la température est élevée (début de l'optimisation), plus les solutions dégradées sont acceptées. Au fur et à mesure du refroidissement, seules les améliorations sont acceptées.

### Mutation des paramètres

Les paramètres binaires (`road_maker`, `greed`, `sheep_hoarder`, `dumb_thief`, `port_lover`) sont inversés avec une probabilité `mutation_rate`.

Les paramètres continus reçoivent un bruit gaussien :

```
sigma = (max_val - min_val) * 0.15 * mutation_rate
nouveau_val = val_courante + Normal(0, sigma)
nouveau_val = clamp(nouveau_val, min_val, max_val)
```

Le taux de mutation de base est `0.3`, mais augmente de `0.1` par rejet consécutif, plafonné à `0.7`. Cela permet d'intensifier l'exploration lorsque l'algorithme est bloqué.

### Résultats obtenus (60 évaluations, 150 parties par évaluation)

Le meilleur agent trouvé atteint un taux de victoire de **77.3%**, contre un baseline attendu de 25% (chance pure à 4 joueurs). Les meilleurs paramètres trouvés sont :

```
prob_trade       = 0.738
road_maker       = False
greed            = False
prob_weight      = 0.5
diversity_weight = 0.639
trade_chaos      = 0.024
sheep_hoarder    = False
dumb_thief       = True
city_first       = 1.126
port_lover       = False
```

---

## Visualisation

### Rendu pygame (vizualize.py)

Le module `vizualize.py` utilise pygame pour afficher le plateau en temps réel. La position de chaque hexagone est calculée via la conversion axiale-pixel. Les bâtiments sont représentés par des cercles de couleur (4 couleurs joueurs), les routes par des segments.

Contrôles :
- `Espace` : avancer d'un tour
- `A` : activer/désactiver le mode automatique
- `Q` : quitter

### Comparaison de performance (charts.py)

Le module `charts.py` génère des graphiques matplotlib à l'issue d'une série de parties :
- Graphique en barres : nombre de victoires par agent avec pourcentages
- Graphique en camembert : distribution des taux de victoire

Les résultats sont sauvegardés dans `agent_comparison.png`.

---

## Installation et utilisation

### Dépendances

```
numpy
matplotlib
pygame
```

```bash
pip install -r requirements.txt
```

### Lancer une comparaison d'agents

```python
# main.py
from agents.smart_agent import SmartAgent
from agents.random_agent import RandomAgent
from charts import compare_agents

agents_config = [SmartAgent(), SmartAgent(), RandomAgent(), RandomAgent()]
compare_agents(agents_config, num_games=500, max_turns=500)
```

### Lancer le fine-tuning

```bash
python run_finetuning.py
```

### Lancer une partie avec visualisation

```python
from agents.smart_agent import SmartAgent
from game.core import CatanGame
import vizualize

agents = [SmartAgent() for _ in range(4)]
game = CatanGame(agents=agents, num_players=4, verbose=True)
vizualize.draw_board(game, max_turns=150)
```

### Tester les performances de référence

```bash
python test_baseline.py
```

---

## Résumé de l'architecture logicielle

```
CatanGame
  ├── Board
  │     ├── HexTile[] (resource, number, robber)
  │     ├── buildings: vertex -> (player_id, type)
  │     ├── roads: frozenset{v1,v2} -> player_id
  │     ├── production_map: dice_value -> [hex_pos]
  │     └── ports: [{edge, type, vertices, center}]
  ├── Player[]
  │     ├── resources: Counter
  │     └── victory_points, roads_left, settlements_left, cities_left
  └── Agent[]
        ├── RandomAgent (base aléatoire + paramètres comportementaux)
        └── SmartAgent  (heuristique + scoring + tous les paramètres)
```

Le moteur de jeu `CatanGame.play_one_turn()` exécute séquentiellement : lancer de dés, phase voleur ou production, échange entre joueurs, échange avec la banque, construction, vérification de victoire, puis passe au joueur suivant.