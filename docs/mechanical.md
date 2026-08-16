# Conception mécanique

Toutes les cotes sont en millimètres. Le repère d'assemblage a son origine
$z = 0$ sur la **face supérieure du plateau de base**, l'axe $Z$ confondu avec
l'axe de rotation (lacet).

![Vue d'assemblage](../mechanical/renders/assembly.png)

## 1. Chaîne cinématique

```
                    STL-19P (couché, plan de balayage vertical)
                       │  centre optique : z = 205, sur l'axe
                  ┌────┴────┐
                  │ berceau │  C3 — serre sur la tige
                  └────┬────┘
                       │  tige acier Ø8, z 65 → 180
                  ┌────┴────┐
                  │ 608ZZ   │  z 122 (palier de butée : reprend le poids)
                  │ colonne │  C2
                  │ 608ZZ   │  z 82  (palier de guidage)
                  └────┬────┘
                       │  accouplement flexible 5→8, z 52 → 77
                  ┌────┴────┐
                  │ NEMA 17 │  z 0 → 40
                  └────┬────┘
                  ┌────┴────┐
                  │ plateau │  C1
                  └────┬────┘
                       │  insert 1/4"-20
                    trépied
```

Hauteur totale au-dessus de la semelle du trépied : **229 mm**.
Masse de la tête tournante : environ 110 g (STL-19P ~47 g + berceau 45 g + tige).

## 2. Décisions de conception

### Entraînement direct plutôt que courroie

Le TMC2209 en 1/16 de pas donne $360 / (200 \times 16) = 0{,}1125°$ par
micro-pas, soit 3,5 fois plus fin que le pas de balayage visé (0,4°). Une
réduction par courroie n'apporterait donc aucune résolution utile, tout en
introduisant du jeu et une pièce d'usure supplémentaire. L'entraînement direct
supprime totalement le jeu de renversement.

### Moteur au-dessus du plateau, coaxial

L'axe de rotation et la vis de trépied doivent tous deux passer par le centre.
Le conflit se résout en plaçant le moteur **sur** le plateau (arbre vers le
haut) et l'insert 1/4"-20 **sous** le plateau, dans un bossage. La colonne
coiffe alors le moteur.

### Accouplement flexible, pas rigide

Deux roulements sur une tige rigide plus un accouplement rigide vers le moteur
forment un système hyperstatique : le moindre défaut d'alignement précontraint
les roulements et crée un point dur. Un accouplement à mâchoires absorbe ce
défaut.

### Palier de butée en haut

Le roulement supérieur (z 122) reprend la charge axiale : le moyeu du berceau
prend appui sur sa bague intérieure. Le chemin d'effort est donc
LiDAR → berceau → bague intérieure → billes → bague extérieure → épaulement de
la colonne → plateau → trépied. Le roulement inférieur (z 82) ne travaille
qu'en radial.

## 3. Occultation au nadir

Tout ce qui se trouve sous le LiDAR et sur l'axe se trouve **dans** le plan de
balayage et masque une portion de la sphère autour du nadir.

| Élément | Ø | Distance sous le centre optique | Demi-angle masqué |
|---|---|---|---|
| Sommet du moyeu | 12 | 25 | 13,5° |
| Voile du berceau | 14 (en Y) | 25 | 15,6° |
| Sommet de la colonne | 34 | 72 | 13,3° |
| Contrefort de butée | 48 (local) | 53 | 24° sur un seul azimut |

Le cône aveugle fait donc environ **20° de demi-angle**, plus un secteur
étroit à l'azimut du contrefort. Sur un trépied à 1,50 m, cela correspond à un
disque de sol d'environ 0,55 m de rayon autour des pieds — que l'on comble
depuis une seconde position de scan. Un scanner terrestre professionnel perd
exactement la même zone.

La platine du berceau, elle, est parallèle au plan de balayage et décalée de
22 mm : deux plans parallèles ne se coupent jamais, elle n'occulte donc rien.

## 4. Cotes principales

### C1 — Plateau de base

![Plateau de base](../mechanical/renders/base_plate.png)

| Cote | Valeur |
|---|---|
| Diamètre | 126 |
| Épaisseur | 8 |
| Bossage trépied | Ø30 × 16 vers le bas |
| Logement d'insert | Ø8,4 × 13, par le dessous — insert **1/4"-20 × 10 × 8 mm** |
| Fixation moteur | 4 × M3 traversants, carré 31 — **écrou M3** côté bride NEMA |
| Fixation colonne | 4 × M3 sur Ø106, écrous noyés par le dessous |
| Passage de câbles | Lumière 18 × 8 à 180° |

Les vis du moteur passent par le plateau ; l'**écrou M3** se pose côté bride
NEMA (trous traversants sur les 17HS4401 courants).

### C2 — Colonne à roulements

![Colonne](../mechanical/renders/bearing_tower.png)

| Cote | Valeur |
|---|---|
| Bride | Ø118 × 6 |
| Base du cône | Ø96 |
| Col | Ø34 |
| Hauteur totale | 133 |
| Cavité moteur | Ø62 jusqu'à z 42 |
| Gorge d'accouplement | Ø26 |
| Logement roulement bas | Ø22,15 × 7 à z 82 |
| Dégagement intermédiaire | Ø23,5 |
| Logement roulement haut | Ø22,15 × 7 à z 122 |

Les trois fenêtres hexagonales à z 64 donnent accès **aux vis de
l'accouplement**, inaccessibles une fois la colonne posée. Elles ne sont pas
décoratives.

Le contrefort dorsal sert de **butée mécanique** pour la prise de référence
d'azimut par StallGuard, sans capteur.

### C3 — Berceau LiDAR

![Berceau](../mechanical/renders/lidar_cradle.png)

| Cote | Valeur |
|---|---|
| Moyeu | Ø18, serrage sur 40 mm de tige, alésage Ø8,45, rétreint à Ø12 en tête |
| Fente de serrage | 1,8 mm + vis M3×25 |
| Platine | 5 mm d'épaisseur, à x = −22 (= décalage optique) |
| Fixation STL-19P | 3 × M2,5 — oreilles lat. **31,92 mm**, haute **42,69 mm** (depuis le bas) |
| Passage câble | **Ø14 mm** à **38,59 mm** (connecteur ZH1.5T, datasheet § 5.1) |
| Rebord de centrage | **54 × 46,3**, hauteur 2,5 |
| Secteur de butée | 26° sur Ø48 |

Les trous M2,5 sont positionnés d'après le **datasheet STL-19P § 5.1** (entraxe
latéral 46,8 mm ; oreilles lat. à 31,92 mm, oreille haute à 42,69 mm, connecteur
à 38,59 mm depuis le bord bas de la face de fixation). Mesurer quand même le
décalage optique sur l'exemplaire réel.

### C4/C5 — Boîtier électronique

![Boîtier](../mechanical/renders/electronics_box.png)

Volume intérieur 106 × 76 × 34. Il se **sangle sur la colonne centrale du
trépied** par deux berceaux en Ø32 sous le fond. L'électronique reste ainsi au
sol : la tête tournante ne porte que le LiDAR et son câble, et le trépied
n'est pas déséquilibré par une masse en porte-à-faux.

## 5. Contraintes de non-collision vérifiées

Ces contraintes sont vérifiées géométriquement dans les sources OpenSCAD et
ont été validées par rendu.

| Contrainte | Marge |
|---|---|
| Sommet de la tige (z 180) sous le corps du STL-19P (z 181,9) | **1,9 mm** |
| Voile du berceau (z ≤ 179) sous le corps (z ≥ 182) | **~3 mm** |
| Cavité de la colonne Ø62 / diagonale NEMA 17 Ø59,8 | 1,1 mm au rayon |
| Paroi de la colonne au droit de la cavité | 4,2 mm mini |
| Vis de colonne (R 53) hors du cône (R 48) | 5 mm, têtes accessibles |
| Nervures dorsales du berceau côté −X | hors volume LiDAR |

**La tige ne doit pas dépasser 115 mm** : au-delà elle pénètre dans le corps
du STL-19P (encombrement plus haut que l'ancien LD19 plat 38,6 mm).

## 6. Impression 3D

Guide détaillé (coupon, insert trépied, contrôles) :
[printing.md](printing.md).

### Réglages généraux

| Paramètre | Valeur | Remarque |
|---|---|---|
| Matériau | **PETG** | Recommandé — stable en chaleur, rigide |
| Buse | 0,4 mm | |
| Hauteur de couche | **0,2 mm** | Sauf `test_fits` : 0,28 mm |
| Températures | 240 °C / 80 °C | Ajuster au filament |
| Refroidissement | ~40 % | Trop froid fragilise le PETG |
| Rétraction | Profil PETG du slicer | Le PETG file facilement |
| Adhérence plateau | PEI + colle barbie / laque | Bride de colonne : surface plane critique |

Le PLA convient pour un essai, mais se déforme dès 50 °C — à éviter en
extérieur ou en voiture.

### Réglages par pièce

| Pièce | Périmètres | Remplissage | Orientation | Supports | Durée indic. |
|---|---|---|---|---|---|
| `test_fits` | 2 | 10 % | Telle quelle | Non | 20–30 min |
| `base_plate` | 4 | 30 % | **Retournée**, bossage trépied vers le haut | Non | ~1 h 30 |
| `bearing_tower` | **5** | **40 %** | Bride sur le plateau | Non | ~4 h |
| `lidar_cradle` | 4 | 35 % | **Couchée**, platine à plat (`rotate -90° Y`) | Sous le moyeu | ~1 h |
| `electronics_box` | 3 | 20 % | Ouverture vers le haut | Non | ~1 h |
| `electronics_lid` | 3 | 20 % | À plat | Non | ~15 min |

**Total** : environ 9 h et 220 g de filament.

Points d'attention :

- **`bearing_tower`** — pièce la plus critique : ne pas réduire les 5
  périmètres ni les 40 % de remplissage. Toute souplesse ici se traduit en
  erreur angulaire dans le nuage.
- **`base_plate` retournée** — face supérieure sur le plateau : pas de
  surplomb, face moteur plane.
- **`lidar_cradle` couchée** — couches perpendiculaires au porte-à-faux du
  LiDAR ; imprimée debout, la pièce casse au voile.

### Ajustements dimensionnels (calibrés)

Imprimer le coupon **`test_fits` en premier**. Reporter les valeurs retenues
dans [`params.scad`](../mechanical/openscad/params.scad) :

| Paramètre | Valeur calibrée | Effet |
|---|---|---|
| `fit_press` | **0,15** | Logement 608ZZ → **Ø22,15** (encoche 5) |
| `fit_slide` | **0,45** | Alésage tige → **Ø8,45** (encoche 4) |

Puis regénérer les STL : `cd mechanical/openscad && make`.

## 7. Matériau et rigidité

Le **PETG** est recommandé : il est plus rigide et bien plus stable
dimensionnellement que le PLA dans une voiture ou un local chaud, et moins
capricieux que l'ABS.

Points de rigidité structurants :

- La **colonne** détermine la précision angulaire : respecter **5 périmètres**
  et **40 %** de remplissage (voir § 6).
- L'entraxe des deux roulements (40 mm) fixe la rigidité en basculement. Le
  réduire dégraderait directement la précision.
- Le **moyeu du berceau** serre sur 40 mm de tige, ce qui suffit largement pour
  110 g en porte-à-faux de 40 mm.

## 8. Génération des pièces

```bash
cd mechanical/openscad
make                # STL dans ../stl/
make renders        # aperçus PNG (nécessite un contexte OpenGL)
```

Sans serveur graphique, utiliser le rasteriseur en Python pur du dépôt :

```bash
cd mechanical
OPENSCAD=/chemin/vers/openscad ./tools/render_all.sh
```

Tous les paramètres sont centralisés dans
[`params.scad`](../mechanical/openscad/params.scad). Modifier une cote et
relancer `make` propage le changement à toutes les pièces.
