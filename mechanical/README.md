# Mécanique

Pièces du châssis, entièrement paramétriques (OpenSCAD).

![Assemblage](renders/assembly.png)

## Contenu

```
mechanical/
├── openscad/     sources paramétriques
│   ├── params.scad       TOUTES les cotes, point d'entrée unique
│   ├── lib.scad          primitives réutilisables
│   ├── test_fits.scad    coupon de calibration
│   ├── base_plate.scad   01 — plateau de base
│   ├── bearing_tower.scad 02 — colonne à roulements
│   ├── lidar_cradle.scad 03 — berceau LiDAR
│   ├── electronics_box.scad / _lid.scad  04/05 — boîtier
│   ├── assembly.scad     vue d'ensemble
│   └── Makefile
├── stl/          pièces prêtes à imprimer
├── renders/      aperçus
└── tools/
    ├── render_all.sh     génération STL + PNG
    └── stl_preview.py    rasteriseur STL en Python pur
```

## Génération

```bash
cd openscad
make                # STL dans ../stl/
make renders        # PNG (nécessite un contexte OpenGL)
```

Sans serveur graphique — machine distante, conteneur, CI — utiliser le
rasteriseur en Python pur, qui n'a aucune dépendance :

```bash
OPENSCAD=/chemin/vers/openscad ./tools/render_all.sh
```

```bash
# Aperçu d'une pièce isolée, sous l'angle de son choix
python3 tools/stl_preview.py stl/bearing_tower.stl /tmp/apercu.png \
    --azim 40 --elev 20 --color 5aa469
```

## Paramétrage

Toutes les cotes sont dans
[`openscad/params.scad`](openscad/params.scad). Modifier une valeur et relancer
`make` la propage à l'ensemble des pièces.

Les deux paramètres à ajuster impérativement avant d'imprimer :

| Paramètre | Comment l'obtenir |
|---|---|
| `fit_press`, `fit_slide` | Imprimer `test_fits`, voir [docs/printing.md](../docs/printing.md) |
| `lidar_optical_offset` | Mesurer au pied à coulisse, voir [docs/calibration.md](../docs/calibration.md) § 1 |

## Pièces

| Pièce | Rôle | Impression |
|---|---|---|
| `test_fits` | **À imprimer en premier** : calibration des ajustements | 15 min |
| `base_plate` | Interface trépied, support moteur, embase colonne | Retournée |
| `bearing_tower` | Porte les deux 608ZZ, **définit l'axe** | 5 périmètres, 40 % |
| `lidar_cradle` | Présente le STL-19P (3 oreilles M2,5) sur la tranche | Couchée |
| `electronics_box` + `_lid` | Boîtier sanglé sur le trépied | Standard |

Voir [docs/mechanical.md](../docs/mechanical.md) pour les cotes et la
justification des choix, [docs/printing.md](../docs/printing.md) pour les
réglages, [docs/assembly.md](../docs/assembly.md) pour le montage.

## Vérification

Les six pièces sont rendues sans erreur par OpenSCAD et produisent des solides
manifold. Les contraintes de non-collision (tige contre corps du STL-19P, voile
contre LiDAR, cavité contre moteur, têtes de vis contre cône) sont listées avec
leurs marges dans [docs/mechanical.md](../docs/mechanical.md) § 5.
