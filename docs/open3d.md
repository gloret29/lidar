# Guide Open3D pour le scanner LiDAR

[Open3D](https://www.open3d.org/) est la bibliothèque 3D utilisée par la
station hôte : visualisation pendant le scan, fichiers `.pcd` / `.ply`,
recalage multi-positions et reconstruction de surface.

Ce guide couvre le parcours **typique de ce projet**, pas toute l’API Open3D.

## 1. Installation

```bash
cd host
python -m venv .venv
source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -e .
```

Open3D est tiré automatiquement (`open3d>=0.17`). Vérifier :

```bash
python -c "import open3d as o3d; print(o3d.__version__)"
```

### Affichage sous WSL / sans GPU

La fenêtre Open3D a besoin d’un serveur graphique :

| Environnement | Astuce |
|---|---|
| Windows natif | Fonctionne en général sans réglage |
| WSL2 + WSLg | `export DISPLAY=:0` puis `lidar-visualize` |
| WSL2 sans GUI | `lidar-receive … --output scans/test.pcd` puis ouvrir le fichier sous Windows |
| SSH distant | idem : recevoir en `.pcd`, visualiser ailleurs |

Si la fenêtre échoue, `lidar-visualize` bascule tout seul en **réception
sans fenêtre** et écrit un `.pcd` (défaut `scans/headless.pcd`, ou
`--output`). Forcer ce mode : `--headless`.

```bash
# Terminal A (WSL)
lidar-receive --port 9000 --output scans/sim.pcd --auto-stop
# ou
lidar-visualize --port 9000 --headless --output scans/sim.pcd

# Terminal B
lidar-simulate --host 127.0.0.1 --port 9000 --fast
```

Sous Windows (PowerShell), pour ouvrir le fichier généré dans WSL :

```powershell
python -c "import open3d as o3d; o3d.visualization.draw_geometries([o3d.io.read_point_cloud(r'\\wsl$\Ubuntu\home\loret\dev\lidar\host\scans\sim.pcd')])"
```

(Adapter le chemin distro / utilisateur.)

Sans affichage, on peut quand même tout faire sauf la fenêtre live.

## 2. Chaîne complète (vue d’ensemble)

```
ESP32  --UDP polaire-->  host (NumPy)
  ou lidar-simulate
                              │
                              ├─ polar_to_cartesian + calibration.json
                              │
                              ▼
                         points XYZ
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       lidar-visualize   lidar-receive    (rejeu .pcd)
         fenêtre live      fichier.pcd
                              │
                              ▼
                       lidar-register   (plusieurs positions)
                              │
                              ▼
                         lidar-mesh  →  salon.ply
```

### Flux de test sans matériel

Deux terminaux, depuis `host/` avec le venv activé :

```bash
# Terminal A — réception / affichage
lidar-visualize --port 9000

# Terminal B — émetteur synthétique
lidar-simulate --host 127.0.0.1 --port 9000 --fast
```

Sans fenêtre Open3D :

```bash
# Terminal A
lidar-receive --port 9000 --output scans/sim_pos1.pcd --auto-stop

# Terminal B
lidar-simulate --host 127.0.0.1 --port 9000 --fast
```

Le simulateur raytrace une pièce axis-aligned (défaut 4×5×2,5 m, capteur à
1,5 m), encode des datagrammes **identiques au firmware** (magic `LDAR`,
120 points, drapeaux start/end) et les envoie en UDP.

| Option | Défaut | Rôle |
|---|---|---|
| `--host` / `--port` | `127.0.0.1` / 9000 | Destination |
| `--fast` | off | Ignore le rythme temps réel ~4,5 kpts/s |
| `--psi-end` | 180 | Amplitude azimut |
| `--speed` | 2 °/s | Vitesse azimut (temps réel) |
| `--width` `--depth` `--height` | 4 / 5 / 2,5 | Dimensions de la pièce (m) |
| `--loops` | 1 | `0` = balayages en boucle |

On doit voir des **murs plans** et des **angles droits**. Si ce n’est pas le
cas avec le simulateur, le bug est côté hôte (calibration / transform), pas
côté matériel.

Open3D intervient dès qu’il y a **affichage**, **fichier nuage** ou
**géométrie** (ICP, Poisson). Le décodage UDP et la trigonométrie restent en
NumPy (`protocol.py`, `transform.py`).

## 3. Visualisation pendant le scan

Sur la station hôte, **avant** de lancer le balayage depuis le panneau web :

```bash
cd host && source .venv/bin/activate
lidar-visualize --port 9000
```

Options utiles :

| Option | Défaut | Rôle |
|---|---|---|
| `--port` | 9000 | Doit coller à l’UDP configuré sur l’ESP32 |
| `--calibration` | `calibration.json` | Bras de levier, offsets, `g_zero` |
| `--refresh` | 0,25 s | Fréquence de rafraîchissement de la fenêtre |
| `--output` | — | Si présent, enregistre un `.pcd` à la fermeture |

### Ce que montre la fenêtre

- Nuage coloré **selon l’altitude Z** (sol / murs / plafond lisibles d’un coup)
- Repère XYZ de 50 cm à l’origine (centre optique)
- Fond sombre, points de taille 1,5

### Navigation (souris)

| Action | Effet |
|---|---|
| Clic gauche + glisser | Orbit autour du nuage |
| Molette | Zoom |
| Clic molette / droit + glisser | Pan (selon version / OS) |
| `R` (souvent) | Reset de la vue — sinon fermer et relancer |

La première arrivée de points recentre la caméra automatiquement.

### Que surveiller en live

| Observation | Cause probable | Action |
|---|---|---|
| Murs **courbes** / cintrage | Bras de levier `tx,ty,tz` faux | [calibration.md](calibration.md) |
| Pièce **penchée** | Trépied / `g_zero` | Nivellement IMU ou bulle |
| Angles muraux non droits | Offset ψ / θ | Calibration angulaire |
| Bande manquante au nadir | Normal (ombre de la base) | Deuxième position |
| Nuage vide | Mauvais port, mauvais Wi‑Fi, hôte mal adressé | Panneau web + `docs/wifi.md` |

Fermer la fenêtre (ou Ctrl+C) pour quitter. Avec `--output`, le nuage est
écrit à ce moment-là.

## 4. Enregistrer un scan en `.pcd`

Sans fenêtre, ou en parallèle d’une autre machine :

```bash
mkdir -p scans
lidar-receive --port 9000 --output scans/salon_pos1.pcd --auto-stop
```

`--auto-stop` s’arrête quand l’ESP32 envoie le drapeau de **fin de balayage**.
Sans cette option : Ctrl+C pour couper.

Le fichier `.pcd` est un nuage Open3D standard (coordonnées en **mètres**,
repère projet après calibration).

### Relire un fichier dans Open3D (sans le scanner)

```bash
python - <<'PY'
import open3d as o3d
p = o3d.io.read_point_cloud("scans/salon_pos1.pcd")
print(p)
o3d.visualization.draw_geometries([p], window_name="Rejeu scan")
PY
```

Ou avec le même coloriage altitude que l’outil live :

```bash
python - <<'PY'
import numpy as np, open3d as o3d
from lidar_host.visualize import colorize_by_height

p = o3d.io.read_point_cloud("scans/salon_pos1.pcd")
pts = np.asarray(p.points)
p.colors = o3d.utility.Vector3dVector(colorize_by_height(pts))
o3d.visualization.draw_geometries(
    [p, o3d.geometry.TriangleMesh.create_coordinate_frame(0.5)],
    window_name="Rejeu coloré",
)
PY
```

## 5. Plusieurs positions : recalage (`lidar-register`)

Pour une pièce complète, on scanne depuis 2–4 emplacements (recouvrement
≈ 30 %), puis :

```bash
lidar-register scans/salon_pos1.pcd scans/salon_pos2.pcd scans/salon_pos3.pcd \
  --output scans/salon_complet.pcd \
  --voxel 0.05
```

Sous le capot Open3D :

1. Sous-échantillonnage voxel (défaut **5 cm**)
2. Estimation de normales
3. **ICP point-to-plane** entre chaque nouvelle position et le nuage fusionné
4. Fusion (`+`) puis écriture `.pcd`

La console affiche `fitness` et `rmse` par position :

| `fitness` | Lecture |
|---|---|
| \> 0,5 | Recouvrement correct |
| 0,3 – 0,5 | Limite — vérifier le chevauchement |
| \< 0,3 | Échec probable — rescaner avec plus de mur commun |

`--voxel` plus petit (ex. `0.02`) affine le recalage mais coûte plus cher en
CPU. Plus grand (`0.08`) : plus robuste / plus grossier.

## 6. Maillage (`lidar-mesh`)

```bash
lidar-mesh scans/salon_complet.pcd --output scans/salon.ply --depth 8 --voxel 0.01
```

Étapes Open3D :

1. Nettoyage : voxel + rejet des outliers statistiques  
2. Normales + orientation cohérente  
3. **Poisson surface reconstruction** (`depth` = niveau octree)  
4. Élagage des zones de faible densité  
5. Export `.ply` (maillage triangulaire)

| `--depth` | Effet typique |
|---|---|
| 7 | Rapide, lisse, détails perdus |
| **8** | Réglage standard intérieur |
| 9–10 | Plus de détail, plus de triangles, plus de bruit amplifié |

Le `.ply` s’ouvre dans Open3D, Blender, MeshLab, CloudCompare, etc. :

```bash
python - <<'PY'
import open3d as o3d
m = o3d.io.read_triangle_mesh("scans/salon.ply")
m.compute_vertex_normals()
o3d.visualization.draw_geometries([m], mesh_show_back_face=True)
PY
```

## 7. Formats et unités

| Format | Contenu | Usage dans ce projet |
|---|---|---|
| `.pcd` | Nuage de points | Sortie `receive` / `register` / `visualize --output` |
| `.ply` | Maillage (ou nuage) | Sortie `mesh` |
| UDP brut | Polaire | Jamais un fichier Open3D — reste sur le fil |

- Distances Open3D : **mètres**  
- Origine : centre optique du LD19 (après bras de levier)  
- **Z** : vertical après redressement `g_zero` (vers le haut une fois nivelé ; le vecteur gravité de calage est `(0,0,-1)` dans le fichier de config)

Modifier `calibration.json` puis **rejouer** un enregistrement n’est pas automatisé
par une commande dédiée : il faut soit rescanner, soit écrire un petit script
qui relit des paquets bruts. En pratique on corrige la calage, puis on
rescane une position de contrôle — ou on garde les `.pcd` déjà transformés et
on n’y touche plus.

Pour itérer sur la géométrie **sans** matériel, le plus simple est de garder
des captures UDP brutes (extension future) ; aujourd’hui le flux standard est
UDP → XYZ → `.pcd`.

## 8. Recettes Open3D utiles (hors CLI)

À lancer depuis `host/` avec le venv activé.

### Stats d’un nuage

```python
import open3d as o3d
import numpy as np

p = o3d.io.read_point_cloud("scans/salon_pos1.pcd")
pts = np.asarray(p.points)
print(len(pts), "points")
print("bbox min", pts.min(0))
print("bbox max", pts.max(0))
print("étendue m", pts.ptp(0))
```

### Filtrer à la main

```python
import open3d as o3d

p = o3d.io.read_point_cloud("scans/salon_pos1.pcd")
p = p.voxel_down_sample(0.02)
p, _ = p.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
o3d.io.write_point_cloud("scans/salon_pos1_clean.pcd", p)
```

(`lidar-mesh` fait déjà ce nettoyage avant Poisson.)

### Comparer deux positions avant recalage

```python
import open3d as o3d

a = o3d.io.read_point_cloud("scans/salon_pos1.pcd")
b = o3d.io.read_point_cloud("scans/salon_pos2.pcd")
a.paint_uniform_color([1, 0.3, 0.1])
b.paint_uniform_color([0.2, 0.5, 1])
o3d.visualization.draw_geometries([a, b])
```

Si les deux pièces se superposent mal **avant** ICP, augmenter le
recouvrement au prochain scan plutôt que de forcer `--voxel`.

## 9. Débit et performance

| Situation | Conseil |
|---|---|
| Visualisation saccadée | Augmenter `--refresh` (ex. 0,5) |
| PC lent pendant ICP | `--voxel 0.06` ou plus |
| Poisson très long | baisser `--depth`, ou voxel plus gros en entrée |
| Trop de points (> 2 M fusionnés) | voxel avant register / mesh |

Le firmware envoie ~4 500 pts/s ; un scan 90 s ≈ **400 k points**. Open3D
gère ça sans peine sur une machine récente.

## 10. Dépannage Open3D

| Symptôme | Piste |
|---|---|
| `ImportError: libGL` / pas de fenêtre | GPU / WSLg / pilotes ; utiliser `lidar-receive` |
| Fenêtre noire, 0 points | Pas de trafic UDP — IP hôte dans le portail Wi‑Fi, même LAN, port 9000 |
| `.pcd` vide | Scan arrêté trop tôt, ou tout filtré (`rho_min` / intensité) |
| Maillage « boule de savon » | Trous trop grands, depth trop bas, ou normales inversées — rescaner les angles morts |
| ICP qui décale tout | Recouvrement insuffisant entre positions |
| Couleurs absentes dans un viewer tiers | Normal : beaucoup de `.pcd` du projet sont XYZ seuls ; le coloriage altitude est surtout live |

## 11. Liens

| Document | Contenu |
|---|---|
| [host/README.md](../host/README.md) | Installation et commandes CLI |
| [operation.md](operation.md) | Conduite d’un scan sur site |
| [calibration.md](calibration.md) | Bras de levier, offsets, gravité |
| [architecture.md](architecture.md) | Protocole UDP v2 |
| [Open3D docs](https://www.open3d.org/docs/latest/) | Référence amont |

En une phrase : **Open3D est l’atelier 3D du PC** — l’ESP32 livre les
mesures, NumPy les place dans l’espace, Open3D les montre, les fusionne et les
transforme en surface.
