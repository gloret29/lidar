# Station hôte

Réception UDP, conversion cartésienne, visualisation temps réel et
post-traitement du nuage de points.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Python ≥ 3.10. Dépendances : NumPy et Open3D.

## Utilisation

### Visualisation pendant le scan

```bash
lidar-visualize --port 9000
```

Le nuage se construit à l'écran, colorié selon l'altitude. Surveiller que les
murs apparaissent **plans** et les angles **droits** : des murs courbes
signalent un bras de levier mal calibré.

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

## Tests

```bash
PYTHONPATH=src python -m pytest tests/ -q
```

35 tests, sans matériel ni Open3D — seul NumPy est requis. Ils couvrent le
décodage du protocole et la transformation géométrique, avec un garde-fou
explicite contre le retour à la formule sphérique naïve.

## Organisation

```
host/
├── src/lidar_host/
│   ├── protocol.py     décodage UDP v2, vectorisé NumPy
│   ├── transform.py    polaire -> cartésien, calibration, nivellement
│   ├── receiver.py     socket, accumulation, export
│   ├── visualize.py    affichage temps réel Open3D
│   └── postprocess.py  filtrage, ICP, Poisson
├── tests/
└── calibration.json
```

## Protocole

Spécifié dans
[docs/architecture.md](../docs/architecture.md#protocole-udp-version-2). Les
points arrivent en **polaire brut** : distance et angle d'élévation par point,
azimut en en-tête de datagramme.
