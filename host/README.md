# Station hôte

Réception UDP, conversion cartésienne, visualisation temps réel et
post-traitement du nuage de points.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
# sous WSL2 + WSLg, si lidar-visualize échoue :
export DISPLAY=:0
```

Python ≥ 3.10. Dépendances : NumPy et Open3D. Les commandes `lidar-*` sont
installées par `pip install -e .` (pas besoin de `PYTHONPATH`).

## Utilisation

### Visualisation pendant le scan

```bash
lidar-visualize --port 9000
```

Sous WSL sans affichage : `--headless --output scans/out.pcd`, ou
`lidar-receive` (voir [docs/open3d.md](../docs/open3d.md)).

### Flux de test sans matériel

Dans un terminal :

```bash
lidar-visualize --port 9000
```

Dans un autre :

```bash
lidar-simulate --host 127.0.0.1 --port 9000 --fast
```

Le simulateur envoie une pièce rectangulaire synthétique (protocole UDP v2)
**et enregistre** le nuage dans `scans/simulate.pcd` par défaut. Un exemplaire
est versionné dans le dépôt : on peut l’ouvrir sans relancer la simulation.

```bash
python -c "import open3d as o3d; o3d.visualization.draw_geometries([o3d.io.read_point_cloud('scans/simulate.pcd')])"
```

```bash
# Fichier seul, sans UDP
lidar-simulate --fast --no-udp --output scans/sim.pcd

# UDP sans fichier
lidar-simulate --fast --no-save
```

Options : `--width`, `--depth`, `--height`, `--speed`, `--psi-end`, `--loops 0`
(infini), `--calibration`. Détails dans
[docs/open3d.md](../docs/open3d.md#flux-de-test-sans-matériel).

### Enregistrement

```bash
lidar-receive --port 9000 --output scans/salon_pos1.pcd --auto-stop
```

`--auto-stop` arrête la capture à réception du drapeau de fin de balayage.

### Recalage et maillage

```bash
lidar-register scans/salon_*.pcd --output salon.pcd
lidar-mesh salon.pcd --output salon.ply --depth 8
```

## Calibration

[`calibration.json`](calibration.json) regroupe le bras de levier, les
décalages angulaires et le vecteur gravité de référence. Ces valeurs sont
appliquées **au post-traitement** : les corriger et rejouer un scan ne demande
ni reflashage ni nouvelle acquisition.

Procédures détaillées dans [docs/calibration.md](../docs/calibration.md).

Guide Open3D (fenêtre live, fichiers, ICP, Poisson, dépannage) :
[docs/open3d.md](../docs/open3d.md).

## Tests

```bash
pytest -q
```

39 tests, sans matériel. Ils couvrent le décodage du protocole, la
transformation géométrique (garde-fou contre la formule sphérique naïve) et
le simulateur UDP (dont l'enregistrement du nuage).

## Organisation

```
host/
├── src/lidar_host/
│   ├── protocol.py     décodage UDP v2, vectorisé NumPy
│   ├── transform.py    polaire -> cartésien, calibration, nivellement
│   ├── receiver.py     socket, accumulation, export
│   ├── visualize.py    affichage temps réel Open3D
│   ├── simulate.py     flux UDP de test (pièce synthétique)
│   └── postprocess.py  filtrage, ICP, Poisson
├── tests/
└── calibration.json
```

## Protocole

Spécifié dans
[docs/architecture.md](../docs/architecture.md#protocole-udp-version-2). Les
points arrivent en **polaire brut** : distance et angle d'élévation par point,
azimut en en-tête de datagramme.
